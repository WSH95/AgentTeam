"""The shared shell-free process runner (plan section 9).

`asyncio.create_subprocess_exec`, never `create_subprocess_shell`; concurrent
stream drain; a hard per-attempt timeout; POSIX process-session and Windows
process-group tree termination; every started attempt is finalized. Failure
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


async def _kill_tree(process: asyncio.subprocess.Process) -> None:
    """Terminate the whole tree; never raises."""
    pid = process.pid
    try:
        if sys.platform == "win32":
            killer = await asyncio.create_subprocess_exec(
                "taskkill.exe",
                "/T",
                "/F",
                "/PID",
                str(pid),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            await killer.wait()
        else:
            try:
                os.killpg(pid, signal_module.SIGTERM)
            except ProcessLookupError:
                return
            await asyncio.sleep(0.5)
            with contextlib.suppress(ProcessLookupError):
                os.killpg(pid, signal_module.SIGKILL)
    except OSError:
        with contextlib.suppress(ProcessLookupError):
            process.kill()


async def run_process(spec: ProcessSpec) -> RawInvocationV1:
    """Run one attempt; always returns (or re-raises CancelledError) finalized."""
    creationflags = 0
    start_new_session = False
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        start_new_session = True

    started = time.monotonic()
    started_at = datetime.now(tz=UTC)
    process = await asyncio.create_subprocess_exec(
        *spec.argv,
        cwd=str(spec.cwd),
        env=spec.env,
        stdin=subprocess.PIPE if spec.stdin_text is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=start_new_session,
        creationflags=creationflags,
    )
    stdin_bytes = spec.stdin_text.encode("utf-8") if spec.stdin_text is not None else None
    timed_out = False
    stdout = b""
    stderr = b""
    communicate = asyncio.create_task(process.communicate(stdin_bytes))
    try:
        done, _pending = await asyncio.wait({communicate}, timeout=spec.timeout_seconds)
        if communicate in done:
            stdout, stderr = communicate.result()
        else:
            timed_out = True
            await _kill_tree(process)
            # the pipes close once the tree is dead; the same task finishes
            done, _pending = await asyncio.wait({communicate}, timeout=10)
            if communicate in done and not communicate.cancelled():
                stdout, stderr = communicate.result()
            else:
                communicate.cancel()
                await asyncio.wait({communicate}, timeout=5)
    except asyncio.CancelledError:
        await _kill_tree(process)
        communicate.cancel()
        await asyncio.wait({communicate}, timeout=5)
        raise
    finally:
        if process.returncode is None:
            await _kill_tree(process)
            try:
                async with asyncio.timeout(10):
                    await process.wait()
            except TimeoutError:
                pass

    duration_ms = int((time.monotonic() - started) * 1000)
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
        duration_ms=duration_ms,
        started_at=started_at,
        finished_at=datetime.now(tz=UTC),
    )


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
