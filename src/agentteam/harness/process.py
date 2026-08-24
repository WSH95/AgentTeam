"""The shared shell-free process runner (plan section 9).

Shell-free `subprocess.Popen` plus nonblocking pipe polling avoids dependence on
an asyncio child watcher (some sandboxed hosts lose very short-lived child exit
notifications). A hard per-attempt timeout, POSIX process-session and Windows
process-group tree termination finalize every attempt. Failure
classification is pure and data-driven: retry once only for network
interruption, rate limit, service unavailability, or timeout (plan section 12
steps 8-9).
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import signal as signal_module
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import IO, Any, cast

from agentteam.domain.run import RetryClassification
from agentteam.harness.types import RawInvocationV1


@dataclass(frozen=True)
class ProcessSpec:
    argv: list[str]
    env: dict[str, str]
    cwd: Path
    stdin_text: str | None
    timeout_seconds: int
    output_file: Path | None = field(default=None)


def _signal_name(returncode: int | None) -> str | None:
    if returncode is None or returncode >= 0:
        return None
    number = -returncode
    try:
        return signal_module.Signals(number).name
    except ValueError:
        return f"signal-{number}"


async def run_process(spec: ProcessSpec) -> RawInvocationV1:
    """Run one attempt concurrently; cancellation kills its process tree first."""
    started = time.monotonic()
    started_at = datetime.now(tz=UTC)
    process = _start_process(spec)
    stdout_task = asyncio.create_task(_read_pipe(process.stdout))
    stderr_task = asyncio.create_task(_read_pipe(process.stderr))
    stdin_task = asyncio.create_task(_write_stdin(process.stdin, spec.stdin_text))
    wait_task = asyncio.create_task(_wait_process(process))
    combined = asyncio.gather(wait_task, stdin_task, stdout_task, stderr_task)
    timed_out = False
    try:
        done, _pending = await asyncio.wait({combined}, timeout=spec.timeout_seconds)
        if combined not in done:
            timed_out = True
            await _kill_tree(process)
            done, _pending = await asyncio.wait({combined}, timeout=10)
            if combined not in done:
                process.kill()
                done, _pending = await asyncio.wait({combined}, timeout=5)
        if combined in done:
            _returncode, _stdin_done, stdout, stderr = combined.result()
        else:
            stdout = b""
            stderr = b"process pipes did not close after termination"
    except asyncio.CancelledError:
        await _kill_tree(process)
        await asyncio.wait({combined}, timeout=10)
        for task in (stdin_task, stdout_task, stderr_task, wait_task):
            task.cancel()
        await asyncio.gather(
            stdin_task, stdout_task, stderr_task, wait_task, return_exceptions=True
        )
        await asyncio.gather(combined, return_exceptions=True)
        raise
    finally:
        if process.poll() is None:
            await _kill_tree(process)

    output_file_text: str | None = None
    if spec.output_file is not None and spec.output_file.is_file():
        output_file_text = spec.output_file.read_text(encoding="utf-8", errors="replace")
    returncode = process.returncode
    return RawInvocationV1(
        exit_code=returncode if returncode is not None and returncode >= 0 else None,
        signal=_signal_name(returncode),
        stdout=stdout,
        stderr=stderr,
        output_file_text=output_file_text,
        timed_out=timed_out,
        duration_ms=int((time.monotonic() - started) * 1000),
        started_at=started_at,
        finished_at=datetime.now(tz=UTC),
    )


def _start_process(spec: ProcessSpec) -> subprocess.Popen[bytes]:
    creationflags = 0
    start_new_session = False
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
    else:
        start_new_session = True
    return subprocess.Popen(
        spec.argv,
        cwd=str(spec.cwd),
        env=spec.env,
        stdin=subprocess.PIPE if spec.stdin_text is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=start_new_session,
        creationflags=creationflags,
    )


async def _read_pipe(pipe: IO[Any] | None) -> bytes:
    if pipe is None:
        return b""
    try:
        descriptor = pipe.fileno()
        if sys.platform == "win32":
            return cast(bytes, await asyncio.to_thread(pipe.read))
        os.set_blocking(descriptor, False)
        chunks: list[bytes] = []
        while True:
            try:
                chunk = os.read(descriptor, 65536)
            except BlockingIOError:
                await asyncio.sleep(0.005)
                continue
            if not chunk:
                return b"".join(chunks)
            chunks.append(chunk)
    finally:
        with contextlib.suppress(OSError):
            pipe.close()


async def _write_stdin(pipe: IO[Any] | None, text: str | None) -> None:
    if pipe is None or text is None:
        return
    data = memoryview(text.encode("utf-8"))
    descriptor = pipe.fileno()
    try:
        if sys.platform == "win32":
            await asyncio.to_thread(pipe.write, data)
            await asyncio.to_thread(pipe.flush)
        else:
            os.set_blocking(descriptor, False)
            while data:
                try:
                    written = os.write(descriptor, data)
                except BlockingIOError:
                    await asyncio.sleep(0.005)
                    continue
                data = data[written:]
    except (BrokenPipeError, OSError):
        pass
    finally:
        with contextlib.suppress(OSError):
            pipe.close()


async def _wait_process(process: subprocess.Popen[bytes]) -> int:
    while (returncode := process.poll()) is None:
        await asyncio.sleep(0.01)
    return returncode


async def _kill_tree(process: subprocess.Popen[bytes]) -> None:
    """Terminate the whole process group; never raise."""
    if process.poll() is not None:
        return
    try:
        if sys.platform == "win32":
            killer = subprocess.Popen(
                ["taskkill.exe", "/T", "/F", "/PID", str(process.pid)],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            await _wait_process(killer)
            return
        try:
            os.killpg(process.pid, signal_module.SIGTERM)
        except ProcessLookupError:
            return
        await asyncio.sleep(0.5)
        if process.poll() is None:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal_module.SIGKILL)
    except OSError:
        with contextlib.suppress(OSError):
            process.kill()


_TRANSIENT_MARKERS = (
    b"429",
    b"rate limit",
    b"rate-limit",
    b"too many requests",
    b"503",
    b"502",
    b"service unavailable",
    b"overloaded",
    b"connection reset",
    b"connection refused",
    b"temporarily unavailable",
    b"network is unreachable",
    b"timed out",
    b"timeout",
)


def classify_failure(raw: RawInvocationV1) -> RetryClassification:
    """Retry once only for network/rate-limit/unavailability/timeout (plan section 12)."""
    if raw.exit_code == 0 and not raw.timed_out:
        return RetryClassification.NONE
    if raw.timed_out:
        return RetryClassification.TRANSIENT
    haystack = (raw.stderr + b"\n" + raw.stdout).lower()
    if any(marker in haystack for marker in _TRANSIENT_MARKERS):
        return RetryClassification.TRANSIENT
    return RetryClassification.PERMANENT
