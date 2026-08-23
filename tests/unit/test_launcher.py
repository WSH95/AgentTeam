"""Launcher policy (plan section 9): direct exec, shim resolution, fail-closed allowlist."""

from __future__ import annotations

import sys
from pathlib import Path

from agentteam.domain.run import LauncherPolicy
from agentteam.harness.launcher import check_allowlist, parse_cmd_shim, resolve_launcher

NPM_SHIM = (
    "@ECHO off\r\nGOTO start\r\n:find_dp0\r\nSET dp0=%~dp0\r\nEXIT /b\r\n"
    ":start\r\nSETLOCAL\r\nCALL :find_dp0\r\n\r\n"
    'IF EXIST "%dp0%\\node.exe" (\r\n'
    '  SET "_prog=%dp0%\\node.exe"\r\n'
    ") ELSE (\r\n"
    '  SET "_prog=node"\r\n'
    "  SET PATHEXT=%PATHEXT:;.JS;=;%\r\n"
    ")\r\n\r\n"
    "endLocal & goto #_undefined_# 2>NUL || title %COMSPEC% & "
    '"%_prog%"  "%dp0%\\node_modules\\claude\\cli.js" %*\r\n'
)


def test_posix_binary_is_launched_directly(tmp_path: Path) -> None:
    exe = tmp_path / "claude"
    exe.write_text("#!/bin/sh\n", encoding="utf-8")
    resolved = resolve_launcher(exe, ["-p", "--version"], platform="linux")
    assert resolved.policy is LauncherPolicy.POSIX_DIRECT
    assert resolved.argv == [str(exe), "-p", "--version"]
    assert resolved.reason is None


def test_python_script_uses_sys_executable_on_every_platform(tmp_path: Path) -> None:
    fake = tmp_path / "fake_codex.py"
    fake.write_text("print('hi')\n", encoding="utf-8")
    for platform in ("linux", "darwin", "win32"):
        resolved = resolve_launcher(fake, ["exec"], platform=platform)
        assert resolved.policy is LauncherPolicy.PYTHON_SCRIPT
        assert resolved.argv == [sys.executable, str(fake), "exec"]


def test_windows_exe_is_launched_directly(tmp_path: Path) -> None:
    exe = tmp_path / "grok.exe"
    exe.write_bytes(b"MZ")
    resolved = resolve_launcher(exe, ["--version"], platform="win32")
    assert resolved.policy is LauncherPolicy.NATIVE_EXE
    assert resolved.argv == [str(exe), "--version"]


def test_parse_cmd_shim_extracts_node_and_script() -> None:
    target = parse_cmd_shim(NPM_SHIM)
    assert target is not None
    # the shim's IF EXIST branch: the %dp0% candidate is carried; resolution
    # falls back to plain "node" when the bundled node.exe is absent
    assert target.interpreter == "%dp0%\\node.exe"
    assert target.script == "%dp0%\\node_modules\\claude\\cli.js"


def test_parse_cmd_shim_returns_none_for_opaque_batch() -> None:
    assert parse_cmd_shim("@echo off\r\nsomething %*\r\n") is None


def test_windows_cmd_shim_is_resolved_to_its_script(tmp_path: Path) -> None:
    shim = tmp_path / "claude.cmd"
    shim.write_bytes(NPM_SHIM.encode("utf-8"))
    resolved = resolve_launcher(shim, ["-p", "hi & there"], platform="win32")
    assert resolved.policy is LauncherPolicy.RESOLVED_CMD_SHIM
    node, script, *rest = resolved.argv
    assert node == "node"  # %dp0%\node.exe does not exist next to the shim
    assert script == str(tmp_path / "node_modules" / "claude" / "cli.js")
    assert rest == ["-p", "hi & there"]  # metacharacters are safe: no cmd.exe involved


def test_windows_cmd_shim_prefers_the_bundled_node(tmp_path: Path) -> None:
    shim = tmp_path / "claude.cmd"
    shim.write_bytes(NPM_SHIM.encode("utf-8"))
    (tmp_path / "node.exe").write_bytes(b"MZ")
    resolved = resolve_launcher(shim, [], platform="win32")
    assert resolved.argv[0] == str(tmp_path / "node.exe")


def test_unresolvable_cmd_with_clean_args_is_allowlisted(tmp_path: Path) -> None:
    shim = tmp_path / "tool.bat"
    shim.write_text("@echo off\nsomething %*\n", encoding="utf-8")
    resolved = resolve_launcher(shim, ["--version", "a b"], platform="win32")
    assert resolved.policy is LauncherPolicy.ALLOWLISTED_CMD
    assert resolved.argv == [str(shim), "--version", "a b"]


def test_unresolvable_cmd_with_metacharacters_is_refused(tmp_path: Path) -> None:
    shim = tmp_path / "tool.cmd"
    shim.write_text("@echo off\nsomething %*\n", encoding="utf-8")
    for bad in ["a&b", "a|b", "a<b", "a>b", "a^b", "a%b", "a!b", "a(b", 'a"b', "a)b", "a\nb"]:
        resolved = resolve_launcher(shim, [bad], platform="win32")
        assert resolved.policy is LauncherPolicy.REFUSED, bad
        assert resolved.reason is not None and "allowlist" in resolved.reason


def test_check_allowlist_accepts_spaces_and_plain_args() -> None:
    assert check_allowlist(["--flag", "value with spaces", "path\\to\\file.js"]) is None
    verdict = check_allowlist(["ok", "no&no"])
    assert verdict is not None and "no&no" in verdict
