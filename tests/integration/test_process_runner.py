"""Shared process runner (plan section 9): exec-only, drained, capped, tree-killed."""

from __future__ import annotations

import asyncio
import os
import sys
import textwrap
import time
from pathlib import Path

import pytest

from agentteam.domain.run import RetryClassification
from agentteam.harness.process import ProcessSpec, classify_failure, run_process


def _script(tmp_path: Path, name: str, body: str) -> list[str]:
    path = tmp_path / name
    path.write_text(textwrap.dedent(body), encoding="utf-8")
    return [sys.executable, str(path)]


def _env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k in {"PATH", "SYSTEMROOT", "SystemRoot"}}
    return env


async def test_captures_stdout_stderr_exit_and_stdin(tmp_path: Path) -> None:
    argv = _script(
        tmp_path,
        "echo.py",
        """
        import sys
        data = sys.stdin.read()
        sys.stdout.write("out:" + data)
        sys.stderr.write("err")
        sys.exit(3)
        """,
    )
    raw = await run_process(
        ProcessSpec(argv=argv, env=_env(), cwd=tmp_path, stdin_text="hello", timeout_seconds=30)
    )
    assert raw.exit_code == 3
    assert raw.signal is None
    assert raw.stdout == b"out:hello"
    assert raw.stderr == b"err"
    assert raw.timed_out is False
    assert raw.duration_ms >= 0


async def test_drains_large_concurrent_streams_without_deadlock(tmp_path: Path) -> None:
    argv = _script(
        tmp_path,
        "big.py",
        """
        import sys
        chunk = "x" * 65536
        for _ in range(32):
            sys.stdout.write(chunk)
            sys.stderr.write(chunk)
        """,
    )
    raw = await run_process(
        ProcessSpec(argv=argv, env=_env(), cwd=tmp_path, stdin_text=None, timeout_seconds=60)
    )
    assert raw.exit_code == 0
    assert len(raw.stdout) == 32 * 65536
    assert len(raw.stderr) == 32 * 65536


async def test_timeout_kills_the_whole_process_tree(tmp_path: Path) -> None:
    marker = tmp_path / "grandchild-alive"
    argv = _script(
        tmp_path,
        "spawner.py",
        f"""
        import subprocess, sys, time
        child = subprocess.Popen(
            [sys.executable, "-c",
             "import time,pathlib\\n"
             "p = pathlib.Path({str(marker)!r})\\n"
             "start = time.time()\\n"
             "while time.time() - start < 20:\\n"
             "    p.write_text(str(time.time()))\\n"
             "    time.sleep(0.2)\\n"]
        )
        time.sleep(30)
        """,
    )
    raw = await run_process(
        ProcessSpec(argv=argv, env=_env(), cwd=tmp_path, stdin_text=None, timeout_seconds=2)
    )
    assert raw.timed_out is True
    assert raw.exit_code is None or raw.exit_code != 0
    # the grandchild must stop refreshing its marker shortly after the kill
    await asyncio.sleep(1.0)
    if marker.exists():
        first = marker.read_text()
        await asyncio.sleep(1.0)
        assert marker.read_text() == first, "grandchild survived the tree kill"


async def test_cancellation_terminates_and_finalizes(tmp_path: Path) -> None:
    argv = _script(tmp_path, "sleep.py", "import time; time.sleep(30)")
    task = asyncio.create_task(
        run_process(
            ProcessSpec(argv=argv, env=_env(), cwd=tmp_path, stdin_text=None, timeout_seconds=60)
        )
    )
    await asyncio.sleep(0.5)
    task.cancel()
    start = time.monotonic()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert time.monotonic() - start < 10  # the child did not hold cancellation hostage


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX signal semantics")
async def test_sigint_death_maps_to_signal_and_130(tmp_path: Path) -> None:
    argv = _script(
        tmp_path,
        "selfint.py",
        """
        import os, signal
        os.kill(os.getpid(), signal.SIGINT)
        """,
    )
    raw = await run_process(
        ProcessSpec(argv=argv, env=_env(), cwd=tmp_path, stdin_text=None, timeout_seconds=30)
    )
    assert raw.signal == "SIGINT"
    assert raw.exit_code in (None, 130)


async def test_output_file_is_read_after_exit(tmp_path: Path) -> None:
    out = tmp_path / "final.txt"
    argv = _script(
        tmp_path,
        "writer.py",
        f"""
        import pathlib
        pathlib.Path({str(out)!r}).write_text("final message", encoding="utf-8")
        """,
    )
    raw = await run_process(
        ProcessSpec(
            argv=argv,
            env=_env(),
            cwd=tmp_path,
            stdin_text=None,
            timeout_seconds=30,
            output_file=out,
        )
    )
    assert raw.output_file_text == "final message"


def test_classify_failure_transient_vs_permanent() -> None:
    def raw(exit_code: int | None = 1, stderr: bytes = b"", timed_out: bool = False):  # type: ignore[no-untyped-def]
        from agentteam.harness.types import RawInvocationV1

        return RawInvocationV1(
            exit_code=exit_code,
            signal=None,
            stdout=b"",
            stderr=stderr,
            output_file_text=None,
            timed_out=timed_out,
            duration_ms=1,
        )

    assert classify_failure(raw(timed_out=True)) is RetryClassification.TRANSIENT
    assert classify_failure(raw(stderr=b"429 Too Many Requests")) is RetryClassification.TRANSIENT
    assert classify_failure(raw(stderr=b"rate limit exceeded")) is RetryClassification.TRANSIENT
    transient = [b"503 Service Unavailable", b"connection reset by peer"]
    for marker in transient:
        assert classify_failure(raw(stderr=marker)) is RetryClassification.TRANSIENT
    permanent = [b"invalid api key", b"schema validation failed"]
    for marker in permanent:
        assert classify_failure(raw(stderr=marker)) is RetryClassification.PERMANENT
    assert classify_failure(raw(exit_code=0)) is RetryClassification.NONE
