"""Deterministic providers for owned-process and external-host conformance."""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path

from agentteam.domain.interactive import (
    CapabilityLevel,
    CleanupFact,
    CloseFactsV1,
    DoctorCheckV1,
    ProviderCapabilitiesV1,
    ProviderDoctorV1,
)
from agentteam.execution.protocol import (
    ActiveTurn,
    CancelDisposition,
    OpenMemberSpec,
    PermissionOutcome,
    ProviderDescriptor,
    ProviderEvent,
    ProviderSession,
    ProviderTurnResult,
    ProviderTurnStatus,
    TurnSpec,
)


class FakeProviderError(RuntimeError):
    pass


_FAKE_OWNED_PROCESSES: dict[int, subprocess.Popen[bytes]] = {}
_FAKE_PARENT = """
import pathlib
import signal
import subprocess
import sys
import time

child = subprocess.Popen(
    [sys.executable, "-c", "import time; time.sleep(3600)"],
    stdin=subprocess.DEVNULL,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
child_pid_path = pathlib.Path(sys.argv[1])
temporary_pid_path = child_pid_path.with_suffix(".tmp")
temporary_pid_path.write_text(f"{child.pid}\\n", encoding="ascii")
temporary_pid_path.replace(child_pid_path)

def stop(*_args):
    if child.poll() is None:
        child.terminate()
        try:
            child.wait(timeout=2)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()
    raise SystemExit(0)

if sys.platform != "win32":
    signal.signal(signal.SIGTERM, stop)
while True:
    time.sleep(3600)
"""


def _process_is_running(pid: int, *, platform: str = sys.platform) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    if platform != "win32":
        try:
            observed = subprocess.run(
                ["ps", "-o", "stat=", "-p", str(pid)],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                check=False,
                timeout=2,
            )
        except (OSError, subprocess.TimeoutExpired):
            return True
        state = observed.stdout.decode("ascii", errors="ignore").strip()
        return observed.returncode == 0 and bool(state) and not state.startswith("Z")
    return True


class _OwnedProcessHandle:
    """A process handle that can be reconstructed from the persisted pid."""

    def __init__(self, pid: int, process: subprocess.Popen[bytes] | None = None) -> None:
        self.pid = pid
        self.process = process

    def poll(self) -> int | None:
        if self.process is not None:
            return self.process.poll()
        if sys.platform != "win32":
            try:
                waited, status = os.waitpid(self.pid, os.WNOHANG)
            except ChildProcessError:
                pass
            else:
                if waited == self.pid:
                    return os.waitstatus_to_exitcode(status)
        try:
            os.kill(self.pid, 0)
        except ProcessLookupError:
            return 0
        except PermissionError:
            return None
        return None

    def terminate(self) -> None:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill.exe", "/T", "/F", "/PID", str(self.pid)],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=5,
            )
        else:
            os.killpg(self.pid, signal.SIGTERM)

    def kill(self) -> None:
        if sys.platform == "win32":
            self.terminate()
        else:
            os.killpg(self.pid, signal.SIGKILL)

    def wait(self) -> int:
        if self.process is not None:
            result = self.process.wait()
            _FAKE_OWNED_PROCESSES.pop(self.pid, None)
            return result
        observed = self.poll()
        while observed is None:
            observed = self.poll()
        _FAKE_OWNED_PROCESSES.pop(self.pid, None)
        return observed


class _FakeTurn(ActiveTurn):
    def __init__(
        self,
        request_id: str,
        worker: Callable[[_FakeTurn], Awaitable[ProviderTurnResult]],
    ) -> None:
        self.request_id = request_id
        self._queue: asyncio.Queue[ProviderEvent | None] = asyncio.Queue()
        self._cancelled = asyncio.Event()
        self._started = False
        self._terminal = False
        self._permission_sequence = 0
        self._permissions: dict[str, asyncio.Future[PermissionOutcome]] = {}
        self._task = asyncio.create_task(self._run(worker))

    async def _run(
        self, worker: Callable[[_FakeTurn], Awaitable[ProviderTurnResult]]
    ) -> ProviderTurnResult:
        self._started = True
        await self._queue.put(ProviderEvent(event="turn-started"))
        try:
            result = await worker(self)
            if result.text is not None:
                await self._queue.put(ProviderEvent(event="text", text=result.text))
            return result
        except BaseException as error:
            return ProviderTurnResult(status=ProviderTurnStatus.FAILED, error=str(error))
        finally:
            self._terminal = True
            await self._queue.put(None)

    def cancelled(self) -> bool:
        return self._cancelled.is_set()

    async def __aiter__(self) -> AsyncIterator[ProviderEvent]:
        while True:
            event = await self._queue.get()
            if event is None:
                return
            yield event

    async def result(self) -> ProviderTurnResult:
        return await self._task

    async def cancel(self, _reason: str) -> CancelDisposition:
        if self._terminal:
            return CancelDisposition.TERMINAL
        self._cancelled.set()
        for response in self._permissions.values():
            if not response.done():
                response.set_result(PermissionOutcome.CANCEL)
        return CancelDisposition.RUNNING if self._started else CancelDisposition.QUEUED

    async def request_permission(self, tool_kind: str) -> PermissionOutcome:
        self._permission_sequence += 1
        permission_id = f"permission-{self._permission_sequence}"
        response: asyncio.Future[PermissionOutcome] = asyncio.get_running_loop().create_future()
        self._permissions[permission_id] = response
        data = {
            "permission_id": permission_id,
            "tool_kind": tool_kind,
            "tool_title": f"fake {tool_kind}",
        }
        if tool_kind in {
            "workspace-read",
            "workspace-write",
            "network",
            "outside-workspace",
            "native-spawn",
            "full-access",
            "unknown",
        }:
            data["classification"] = tool_kind
        if tool_kind == "workspace-read":
            data["tool_input"] = json.dumps({"path": "."})
        elif tool_kind == "workspace-write":
            data["tool_input"] = json.dumps({"path": "fake-output.txt"})
        await self._queue.put(
            ProviderEvent(
                event="permission-request",
                data=data,
            )
        )
        try:
            return await response
        finally:
            self._permissions.pop(permission_id, None)

    async def respond_permission(self, permission_id: str, outcome: PermissionOutcome) -> None:
        response = self._permissions.get(permission_id)
        if response is None or response.done():
            raise FakeProviderError(f"unknown permission request: {permission_id}")
        response.set_result(outcome)


class _BaseFakeProvider:
    provider_id: str

    def __init__(self, *, clock: Callable[[], datetime] | None = None) -> None:
        self.clock = clock or (lambda: datetime.now(tz=UTC))
        self.sessions: dict[str, ProviderSession] = {}
        self.context: dict[str, list[str]] = {}
        self.turns: dict[str, _FakeTurn] = {}
        self.run_state_dirs: dict[str, set[Path]] = {}
        self.background_tasks: set[asyncio.Task[None]] = set()

    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            provider_id=self.provider_id,
            version="fake-1",
            capabilities=self._capabilities(),
        )

    async def doctor(self) -> ProviderDoctorV1:
        return ProviderDoctorV1(
            schema_version=1,
            kind="provider-doctor",
            provider=self.provider_id,
            checked_at=self.clock(),
            status="pass",
            capabilities=self._capabilities(),
            checks=[DoctorCheckV1(name="deterministic-fake", status="pass")],
            model_calls=0,
        )

    async def open_member(self, spec: OpenMemberSpec) -> ProviderSession:
        if spec.session_id in self.sessions:
            raise FakeProviderError(f"session already exists: {spec.session_id}")
        resuming = spec.resume_session_ref is not None
        provider_ref = self._provider_ref(spec)
        if resuming and spec.resume_session_ref != provider_ref:
            raise FakeProviderError("strict continuity mismatch")
        if spec.state_dir.exists():
            if not resuming or not spec.state_dir.is_dir() or spec.state_dir.is_symlink():
                raise FakeProviderError(f"fresh or unsafe session state exists: {spec.state_dir}")
        else:
            if resuming:
                raise FakeProviderError("resume state is missing")
            spec.state_dir.mkdir(parents=True, exist_ok=False)
        continuity = spec.resume_session_ref is None or spec.resume_session_ref == provider_ref
        marker = spec.state_dir / "session.txt"
        if resuming:
            try:
                observed_ref = marker.read_text(encoding="utf-8").strip()
                continuity = continuity and observed_ref == provider_ref
            except OSError:
                continuity = False
        if not continuity:
            if not resuming:
                shutil.rmtree(spec.state_dir)
            raise FakeProviderError("strict continuity mismatch")
        session = ProviderSession(
            provider_id=self.provider_id,
            run_id=spec.run_id,
            member=spec.member,
            session_id=spec.session_id,
            generation=spec.generation,
            provider_session_ref=provider_ref,
            workspace=spec.workspace.resolve(),
            state_dir=spec.state_dir.resolve(),
            continuity_verified=True,
        )
        stored_context: list[str] = []
        if resuming:
            try:
                context_text = (session.state_dir / "context.json").read_text(encoding="utf-8")
                stored = json.loads(context_text)
            except (OSError, json.JSONDecodeError) as error:
                raise FakeProviderError(f"resume context is invalid: {error}") from None
            if not isinstance(stored, list) or not all(isinstance(item, str) for item in stored):
                raise FakeProviderError("resume context is invalid")
            stored_context = stored
        self._open_effect(spec, session)
        self.sessions[session.session_id] = session
        self.context[session.session_id] = stored_context
        self.run_state_dirs.setdefault(spec.run_id, set()).add(session.state_dir)
        marker.write_text(provider_ref + "\n", encoding="utf-8")
        self._write_context(session.session_id)
        return session

    async def start_turn(self, session: ProviderSession, spec: TurnSpec) -> ActiveTurn:
        self._require_session(session)
        existing = self.turns.get(session.session_id)
        if existing is not None and existing._terminal:
            self.turns.pop(session.session_id, None)
        elif existing is not None:
            raise FakeProviderError(f"turn already active for {session.session_id}")

        async def worker(turn: _FakeTurn) -> ProviderTurnResult:
            if spec.text == "WAIT":
                await turn._cancelled.wait()
                return ProviderTurnResult(
                    status=ProviderTurnStatus.CANCELLED, stop_reason="cancelled"
                )
            if spec.text.startswith("PERMISSION:"):
                outcome = await turn.request_permission(spec.text.partition(":")[2] or "unknown")
                if outcome in {
                    PermissionOutcome.REJECT_ONCE,
                    PermissionOutcome.REJECT_ALWAYS,
                    PermissionOutcome.CANCEL,
                }:
                    return ProviderTurnResult(
                        status=ProviderTurnStatus.CANCELLED,
                        stop_reason=f"permission-{outcome.value}",
                    )
            if spec.text.startswith("READFILE:"):
                relative = spec.text.partition(":")[2]
                candidate = (session.workspace / relative).resolve()
                if session.workspace not in candidate.parents and candidate != session.workspace:
                    return ProviderTurnResult(
                        status=ProviderTurnStatus.FAILED,
                        error="fake read escaped the workspace",
                    )
                content = candidate.read_text(encoding="utf-8")
                history = self.context[session.session_id]
                history.append(spec.text)
                self._write_context(session.session_id)
                return ProviderTurnResult(
                    status=ProviderTurnStatus.COMPLETED,
                    text=f"file:{content}",
                )
            if spec.text.startswith("EMIT:"):
                output = spec.text.partition(":")[2]
                history = self.context[session.session_id]
                history.append(spec.text)
                self._write_context(session.session_id)
                return ProviderTurnResult(
                    status=ProviderTurnStatus.COMPLETED,
                    text=output,
                )
            history = self.context[session.session_id]
            history.append(spec.text)
            self._write_context(session.session_id)
            response = f"turn-{len(history)}:" + "|".join(history)
            return ProviderTurnResult(status=ProviderTurnStatus.COMPLETED, text=response)

        active = _FakeTurn(spec.request_id, worker)
        self.turns[session.session_id] = active

        async def clear_when_done() -> None:
            await active.result()
            self.turns.pop(session.session_id, None)

        task = asyncio.create_task(clear_when_done())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
        return active

    async def cancel_turn(self, session: ProviderSession, reason: str) -> CancelDisposition:
        self._require_session(session)
        turn = self.turns.get(session.session_id)
        if turn is None:
            return CancelDisposition.TERMINAL
        return await turn.cancel(reason)

    async def verify_continuity(self, session: ProviderSession) -> bool:
        current = self.sessions.get(session.session_id)
        return current == session and self._continuity_effect(session)

    async def close_member(self, session: ProviderSession, _reason: str) -> CloseFactsV1:
        self._require_session(session)
        turn = self.turns.get(session.session_id)
        if turn is not None:
            await turn.cancel("session close")
            await turn.result()
        if self.background_tasks:
            await asyncio.gather(*tuple(self.background_tasks), return_exceptions=True)
        process = await self._close_effect(session)
        self.sessions.pop(session.session_id, None)
        self.context.pop(session.session_id, None)
        self.turns.pop(session.session_id, None)
        shutil.rmtree(session.state_dir, ignore_errors=False)
        return CloseFactsV1(
            logical_session=CleanupFact.CONFIRMED,
            process=process,
            local_state=CleanupFact.CONFIRMED,
            provider_history=self._provider_history_fact(),
        )

    async def dispose_run(self, run_id: str) -> CleanupFact:
        if self.background_tasks:
            await asyncio.gather(*tuple(self.background_tasks), return_exceptions=True)
        if any(session.run_id == run_id for session in self.sessions.values()):
            return CleanupFact.FAILED
        for path in self.run_state_dirs.pop(run_id, set()):
            if path.exists():
                shutil.rmtree(path)
        return CleanupFact.CONFIRMED

    def lose_session(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)

    def _require_session(self, session: ProviderSession) -> None:
        if self.sessions.get(session.session_id) != session:
            raise FakeProviderError(f"unknown or replaced session: {session.session_id}")

    def _write_context(self, session_id: str) -> None:
        session = self.sessions[session_id]
        temporary = session.state_dir / ".context.json.tmp"
        temporary.write_text(json.dumps(self.context[session_id]) + "\n", encoding="utf-8")
        os.replace(temporary, session.state_dir / "context.json")

    def _provider_ref(self, spec: OpenMemberSpec) -> str:
        return f"{self.provider_id}-{spec.run_id}-{spec.member}-g{spec.generation}"

    def _open_effect(self, spec: OpenMemberSpec, session: ProviderSession) -> None:
        del spec, session

    def _continuity_effect(self, session: ProviderSession) -> bool:
        del session
        return True

    async def _close_effect(self, session: ProviderSession) -> CleanupFact:
        del session
        return CleanupFact.NOT_APPLICABLE

    def _provider_history_fact(self) -> CleanupFact:
        return CleanupFact.NOT_APPLICABLE

    def _capabilities(self) -> ProviderCapabilitiesV1:
        raise NotImplementedError


class OwnedProcessFakeProvider(_BaseFakeProvider):
    provider_id = "owned-process-fake"

    def __init__(self, *, clock: Callable[[], datetime] | None = None) -> None:
        super().__init__(clock=clock)
        self.processes: dict[str, _OwnedProcessHandle] = {}
        self.descendant_pids: dict[str, int] = {}

    def _open_effect(self, spec: OpenMemberSpec, session: ProviderSession) -> None:
        pid_path = session.state_dir / "process.pid"
        if spec.resume_session_ref is not None:
            try:
                pid = int(pid_path.read_text(encoding="ascii").strip())
            except (OSError, ValueError) as error:
                raise FakeProviderError(f"owned process identity is invalid: {error}") from None
            handle = _OwnedProcessHandle(pid, _FAKE_OWNED_PROCESSES.get(pid))
            if handle.poll() is not None:
                raise FakeProviderError("owned process continuity is lost")
            try:
                descendant = int((session.state_dir / "child.pid").read_text().strip())
            except (OSError, ValueError) as error:
                raise FakeProviderError(f"owned descendant identity is invalid: {error}") from None
            if not _process_is_running(descendant):
                raise FakeProviderError("owned descendant continuity is lost")
            self.processes[session.session_id] = handle
            self.descendant_pids[session.session_id] = descendant
            return
        creationflags = 0
        start_new_session = False
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
        else:
            start_new_session = True
        process = subprocess.Popen(
            [sys.executable, "-c", _FAKE_PARENT, str(session.state_dir / "child.pid")],
            cwd=spec.workspace,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=start_new_session,
            creationflags=creationflags,
        )
        _FAKE_OWNED_PROCESSES[process.pid] = process
        handle = _OwnedProcessHandle(process.pid, process)
        self.processes[session.session_id] = handle
        pid_path.write_text(f"{process.pid}\n", encoding="ascii")
        deadline = time.monotonic() + 2
        child_pid_path = session.state_dir / "child.pid"
        while (
            not child_pid_path.is_file() and handle.poll() is None and time.monotonic() < deadline
        ):
            time.sleep(0.01)
        try:
            descendant = int(child_pid_path.read_text(encoding="ascii").strip())
        except (OSError, ValueError) as error:
            with contextlib.suppress(OSError, subprocess.TimeoutExpired):
                handle.kill()
                handle.wait()
            self.processes.pop(session.session_id, None)
            _FAKE_OWNED_PROCESSES.pop(process.pid, None)
            raise FakeProviderError(f"owned descendant did not start: {error}") from None
        self.descendant_pids[session.session_id] = descendant

    def _continuity_effect(self, session: ProviderSession) -> bool:
        process = self.processes.get(session.session_id)
        descendant = self.descendant_pids.get(session.session_id)
        return (
            process is not None
            and process.poll() is None
            and descendant is not None
            and _process_is_running(descendant)
        )

    async def _close_effect(self, session: ProviderSession) -> CleanupFact:
        process = self.processes.pop(session.session_id, None)
        descendant = self.descendant_pids.pop(session.session_id, None)
        if process is None:
            return CleanupFact.FAILED
        if process.poll() is None or (descendant is not None and _process_is_running(descendant)):
            if sys.platform == "win32":
                with contextlib.suppress(OSError, subprocess.TimeoutExpired):
                    process.terminate()
            else:
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(process.pid, signal.SIGTERM)
            deadline = asyncio.get_running_loop().time() + 2
            while (
                process.poll() is None
                or (descendant is not None and _process_is_running(descendant))
            ) and asyncio.get_running_loop().time() < deadline:
                await asyncio.sleep(0.01)
            if process.poll() is None or (
                descendant is not None and _process_is_running(descendant)
            ):
                if sys.platform == "win32":
                    with contextlib.suppress(OSError, subprocess.TimeoutExpired):
                        process.kill()
                else:
                    with contextlib.suppress(ProcessLookupError):
                        os.killpg(process.pid, signal.SIGKILL)
                deadline = asyncio.get_running_loop().time() + 2
                while (
                    process.poll() is None
                    or (descendant is not None and _process_is_running(descendant))
                ) and asyncio.get_running_loop().time() < deadline:
                    await asyncio.sleep(0.01)
        terminal = process.poll() is not None and (
            descendant is None or not _process_is_running(descendant)
        )
        if terminal:
            _FAKE_OWNED_PROCESSES.pop(process.pid, None)
        return CleanupFact.CONFIRMED if terminal else CleanupFact.FAILED

    def _provider_history_fact(self) -> CleanupFact:
        return CleanupFact.CONFIRMED

    def _capabilities(self) -> ProviderCapabilitiesV1:
        return ProviderCapabilitiesV1(
            schema_version=1,
            kind="provider-capabilities",
            provider=self.provider_id,
            version="fake-1",
            persistent_turns=CapabilityLevel.SUPPORTED,
            recovery=CapabilityLevel.SUPPORTED,
            permission_events=CapabilityLevel.SUPPORTED,
            workspace_enforcement=CapabilityLevel.SUPPORTED,
            tool_filtering=CapabilityLevel.SUPPORTED,
            native_spawn_control=CapabilityLevel.SUPPORTED,
            process_stop_observability=CapabilityLevel.SUPPORTED,
            local_state_deletion=CapabilityLevel.SUPPORTED,
            provider_history_deletion=CapabilityLevel.SUPPORTED,
        )


class ExternalHostFakeProvider(_BaseFakeProvider):
    provider_id = "external-host-fake"

    def _provider_history_fact(self) -> CleanupFact:
        return CleanupFact.UNSUPPORTED

    def _capabilities(self) -> ProviderCapabilitiesV1:
        return ProviderCapabilitiesV1(
            schema_version=1,
            kind="provider-capabilities",
            provider=self.provider_id,
            version="fake-1",
            persistent_turns=CapabilityLevel.SUPPORTED,
            recovery=CapabilityLevel.SUPPORTED,
            permission_events=CapabilityLevel.SUPPORTED,
            workspace_enforcement=CapabilityLevel.SUPPORTED,
            tool_filtering=CapabilityLevel.SUPPORTED,
            native_spawn_control=CapabilityLevel.UNKNOWN,
            process_stop_observability=CapabilityLevel.UNSUPPORTED,
            local_state_deletion=CapabilityLevel.SUPPORTED,
            provider_history_deletion=CapabilityLevel.UNSUPPORTED,
        )
