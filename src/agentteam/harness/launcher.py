"""Launcher policy (plan section 9).

Python's `subprocess` documents that Windows batch files may be launched
through the system shell regardless of `shell=False`, with no escaping added.
AgentTeam therefore never hands user-controlled content to a batch file: a
native `.exe` is launched directly; an npm `.cmd` shim is resolved to the node
entry script it wraps so `cmd.exe` never parses anything; if resolution fails,
the `.cmd` runs only when every argv element passes a strict safe-character
allowlist, otherwise the invocation is refused (exit 2) with the reason.
Deterministic fakes are Python scripts launched as `[sys.executable, script]`
so their records are honest (`python-script`). The resolved launcher and the
branch taken are recorded on the invocation.
"""

from __future__ import annotations

import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from agentteam.domain.run import LauncherPolicy

# Characters cmd.exe treats specially; spaces are allowed (quoted by subprocess).
_FORBIDDEN = set('&|<>^%!()"') | {"\n", "\r", "\0"}


@dataclass(frozen=True)
class ShimTarget:
    """The interpreter/script pair an npm-style `.cmd` shim wraps."""

    interpreter: str  # "node", "node.exe", or a %dp0%-relative path
    script: str  # raw script argument, may contain %dp0%


@dataclass(frozen=True)
class ResolvedLauncher:
    argv: list[str]
    policy: LauncherPolicy
    reason: str | None = None


# The npm cmd-shim launch line looks like:
#   ... & "%_prog%"  "%dp0%\node_modules\pkg\cli.js" %*
# with _prog set to "%dp0%\node.exe" or "node" earlier in the file.
_LAUNCH_LINE = re.compile(r'"%_prog%"\s+"(?P<script>[^"]+\.(?:js|cjs|mjs))"\s+%\*')
_PROG_NODE = re.compile(r'SET\s+"_prog=(?P<prog>[^"]*node(?:\.exe)?)"', re.IGNORECASE)


def parse_cmd_shim(text: str) -> ShimTarget | None:
    """Parse npm-style `.cmd` shim text; None when the shape is not recognised."""
    launch = _LAUNCH_LINE.search(text)
    if launch is None:
        return None
    progs = _PROG_NODE.findall(text)
    if not progs:
        return None
    # Prefer the %dp0%-relative node if the shim defines one, else plain node.
    interpreter = next((p for p in progs if "%dp0%" in p.lower()), progs[-1])
    return ShimTarget(interpreter=interpreter, script=launch.group("script"))


def check_allowlist(argv: list[str]) -> str | None:
    """None when every element is safe; else a message naming the offender."""
    for element in argv:
        bad = sorted({ch for ch in element if ch in _FORBIDDEN})
        if bad:
            printable = ", ".join(repr(ch) for ch in bad)
            return f"argv element {element!r} fails the cmd.exe allowlist ({printable})"
    return None


def _expand_dp0(value: str, shim_dir: Path) -> Path:
    expanded = re.sub(r"%~?dp0%?\\?", "", value, flags=re.IGNORECASE)
    expanded = expanded.replace("\\", "/")
    return (shim_dir / expanded).resolve() if not Path(expanded).is_absolute() else Path(expanded)


def resolve_launcher(executable: Path, argv_rest: list[str], *, platform: str) -> ResolvedLauncher:
    executable = Path(executable)
    suffix = executable.suffix.lower()

    if suffix == ".py":
        return ResolvedLauncher(
            argv=[sys.executable, str(executable), *argv_rest],
            policy=LauncherPolicy.PYTHON_SCRIPT,
        )

    if platform != "win32":
        return ResolvedLauncher(
            argv=[str(executable), *argv_rest], policy=LauncherPolicy.POSIX_DIRECT
        )

    # A bare command name must PATH-resolve here: CreateProcess appends only
    # `.exe`, so an npm-installed CLI whose on-disk artifact is a `.cmd` shim
    # is unreachable until the name resolves to that file (G7 vendor smoke,
    # run 32764172806 — every Windows diagnostic capture failed).
    if not suffix and executable.parent == Path("."):
        found = shutil.which(str(executable))
        if found is not None:
            executable = Path(found)
            suffix = executable.suffix.lower()

    if suffix in {".cmd", ".bat"}:
        try:
            text = executable.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        target = parse_cmd_shim(text)
        if target is not None:
            shim_dir = executable.parent
            script = _expand_dp0(target.script, shim_dir)
            if "%dp0%" in target.interpreter.lower():
                bundled = _expand_dp0(target.interpreter, shim_dir)
                interpreter = str(bundled) if bundled.exists() else "node"
            else:
                interpreter = target.interpreter
            return ResolvedLauncher(
                argv=[interpreter, str(script), *argv_rest],
                policy=LauncherPolicy.RESOLVED_CMD_SHIM,
            )
        verdict = check_allowlist([str(executable), *argv_rest])
        if verdict is None:
            return ResolvedLauncher(
                argv=[str(executable), *argv_rest], policy=LauncherPolicy.ALLOWLISTED_CMD
            )
        return ResolvedLauncher(
            argv=[str(executable), *argv_rest],
            policy=LauncherPolicy.REFUSED,
            reason=f"unresolvable batch launcher: {verdict}",
        )

    return ResolvedLauncher(argv=[str(executable), *argv_rest], policy=LauncherPolicy.NATIVE_EXE)
