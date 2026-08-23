"""Windows-only `.cmd` launcher integration (plan sections 9 and 15).

Synthesises both shim shapes in tmp (CRLF) and actually launches them through
the process runner: the npm-shim branch must deliver adversarial arguments
verbatim to the wrapped script (cmd.exe never parses them); the opaque-batch
branch runs only allowlist-clean arguments and refuses metacharacters.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

from agentteam.domain.run import LauncherPolicy
from agentteam.harness.launcher import resolve_launcher
from agentteam.harness.process import ProcessSpec, run_process

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows-only launcher branch")

NODE = shutil.which("node")


def _npm_shim(tmp_path: Path) -> Path:
    script = tmp_path / "node_modules" / "tool" / "cli.js"
    script.parent.mkdir(parents=True)
    script.write_text(
        "const fs = require('fs');\n"
        "fs.writeFileSync(process.argv[2], JSON.stringify(process.argv.slice(3)));\n",
        encoding="utf-8",
    )
    shim = tmp_path / "tool.cmd"
    shim.write_bytes(
        b'@ECHO off\r\nSETLOCAL\r\nSET "_prog=node"\r\n'
        b"endLocal & goto #_undefined_# 2>NUL || title %COMSPEC% & "
        b'"%_prog%"  "%dp0%\\node_modules\\tool\\cli.js" %*\r\n'
    )
    return shim


@pytest.mark.skipif(NODE is None, reason="node not on PATH")
async def test_resolved_shim_delivers_metacharacters_verbatim(tmp_path: Path) -> None:
    shim = _npm_shim(tmp_path)
    out = tmp_path / "argv.json"
    adversarial = ["with space", "a&b", "50%", "^caret", 'quote"quote', "(paren)"]
    assert NODE is not None
    resolved = resolve_launcher(shim, [str(out), *adversarial], platform="win32")
    assert resolved.policy is LauncherPolicy.RESOLVED_CMD_SHIM
    raw = await run_process(
        ProcessSpec(
            argv=resolved.argv,
            env={"PATH": str(Path(NODE).parent), "SystemRoot": "C:\\Windows"},
            cwd=tmp_path,
            stdin_text=None,
            timeout_seconds=60,
        )
    )
    assert raw.exit_code == 0, raw.stderr
    assert json.loads(out.read_text(encoding="utf-8")) == adversarial


async def test_allowlisted_opaque_batch_runs_clean_args(tmp_path: Path) -> None:
    batch = tmp_path / "opaque.cmd"
    batch.write_bytes(b"@echo off\r\necho ran %1 > out.txt\r\n")
    resolved = resolve_launcher(batch, ["cleanarg"], platform="win32")
    assert resolved.policy is LauncherPolicy.ALLOWLISTED_CMD
    import os

    raw = await run_process(
        ProcessSpec(
            argv=resolved.argv,
            env={
                "PATH": os.environ.get("PATH", ""),
                "SystemRoot": os.environ.get("SYSTEMROOT", "C:\\Windows"),
                "COMSPEC": os.environ.get("COMSPEC", "C:\\Windows\\System32\\cmd.exe"),
            },
            cwd=tmp_path,
            stdin_text=None,
            timeout_seconds=60,
        )
    )
    assert raw.exit_code == 0, raw.stderr
    assert (
        (tmp_path / "out.txt")
        .read_text(encoding="utf-8", errors="replace")
        .strip()
        .startswith("ran cleanarg")
    )


def test_metacharacter_args_are_refused_before_launch(tmp_path: Path) -> None:
    batch = tmp_path / "opaque.cmd"
    batch.write_bytes(b"@echo off\r\necho pwned\r\n")
    resolved = resolve_launcher(batch, ["a&b"], platform="win32")
    assert resolved.policy is LauncherPolicy.REFUSED
    assert resolved.reason is not None
