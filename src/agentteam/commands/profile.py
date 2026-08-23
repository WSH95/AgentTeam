"""`atm profile init/validate/doctor` (plan sections 8 and 11; no --probe until G5).

`init` creates non-secret directories and configuration and prints login
instructions; it never automates a browser or copies a credential store.
`doctor` exposes allowlisted, sanitized status only: names, never values.
"""

from __future__ import annotations

import asyncio
import os
import shutil
import sys
from pathlib import Path
from typing import Annotated, Any

import typer

from agentteam.commands.common import EXIT_RUNTIME, emit, fail
from agentteam.harness.launcher import resolve_launcher
from agentteam.harness.process import ProcessSpec, run_process
from agentteam.resolution.profiles import (
    ProfileError,
    default_profile_path,
    load_profile_set,
    resolve_profile_path,
    seed_default_profiles,
    write_profile_set,
)

profile_app = typer.Typer(name="profile", help="Local harness profiles (never committed).")

_LOGIN_INSTRUCTIONS = """\
Native subscription logins (run each yourself; AgentTeam never automates a
browser and never reads or copies a credential store):
  claude-code:  CLAUDE_CONFIG_DIR=<config home> claude /login
  codex:        CODEX_HOME=<config home> codex login
  grok:         GROK_HOME=<config home> grok login
Authentication stays unverified until the G5 probes / first live leg."""


def _config_option(value: Path | None) -> Path:
    return value if value is not None else default_profile_path(os.environ)


@profile_app.command("init")
def init(
    config: Annotated[Path | None, typer.Option("--config")] = None,
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Write the seeded default profiles and create the vendor config homes."""
    path = _config_option(config)
    if path.exists():
        raise fail(f"profile file already exists: {path} (edit it, or move it away first)")
    profile_set = seed_default_profiles()
    write_profile_set(path, profile_set)
    homes = []
    for profile in profile_set.profiles:
        home = resolve_profile_path(path, profile.config_home)
        home.mkdir(parents=True, exist_ok=True)
        homes.append(str(home))
    emit(
        json_out,
        {"profile_file": str(path), "config_homes": homes},
        f"wrote {path}\ncreated config homes:\n  "
        + "\n  ".join(homes)
        + "\n"
        + _LOGIN_INSTRUCTIONS,
    )


@profile_app.command("validate")
def validate(
    config: Annotated[Path | None, typer.Option("--config")] = None,
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Load and schema-validate the profile set."""
    path = _config_option(config)
    try:
        profile_set = load_profile_set(path)
    except ProfileError as error:
        raise fail(str(error)) from None
    emit(
        json_out,
        {"valid": True, "profiles": [p.harness.value for p in profile_set.profiles]},
        f"valid: {len(profile_set.profiles)} profile(s) in {path}",
    )


async def _capture_version(executable: Path) -> str | None:
    resolved = resolve_launcher(executable, ["--version"], platform=sys.platform)
    if resolved.reason is not None:
        return None
    raw = await run_process(
        ProcessSpec(
            argv=resolved.argv,
            env={k: v for k, v in os.environ.items() if k in {"PATH", "SystemRoot"}},
            cwd=Path.cwd(),
            stdin_text=None,
            timeout_seconds=20,
        )
    )
    if raw.exit_code != 0:
        return None
    return raw.stdout.decode("utf-8", errors="replace").strip() or None


@profile_app.command("doctor")
def doctor(
    config: Annotated[Path | None, typer.Option("--config")] = None,
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Sanitized status: executables, config homes, conflict names, capabilities."""
    path = _config_option(config)
    try:
        profile_set = load_profile_set(path)
    except ProfileError as error:
        raise fail(str(error)) from None

    rows: list[dict[str, Any]] = []
    lines: list[str] = []
    all_ok = True
    for profile in profile_set.profiles:
        executable = resolve_profile_path(path, profile.executable)
        resolved = executable.is_file() or shutil.which(str(profile.executable)) is not None
        if not executable.is_file():
            which = shutil.which(str(profile.executable))
            if which is not None:
                executable = Path(which)
        version = asyncio.run(_capture_version(executable)) if resolved else None
        home = resolve_profile_path(path, profile.config_home)
        conflicts_set = sorted(name for name in profile.environment.conflicts if name in os.environ)
        capabilities = {
            "verified": sum(1 for c in profile.capabilities if c.verification.value == "verified"),
            "observed": sum(1 for c in profile.capabilities if c.verification.value == "observed"),
            "unverified": sum(
                1 for c in profile.capabilities if c.verification.value == "unverified"
            ),
        }
        all_ok = all_ok and resolved
        rows.append(
            {
                "harness": profile.harness.value,
                "executable_resolved": resolved,
                "version": version,
                "config_home_exists": home.is_dir(),
                "conflicts_set": conflicts_set,
                "capabilities": capabilities,
                "auth": "unverified (probes arrive at G5)",
            }
        )
        status = version if version else ("ok" if resolved else "NOT FOUND")
        conflict_note = f"; conflicts set: {', '.join(conflicts_set)}" if conflicts_set else ""
        lines.append(
            f"{profile.harness.value}: "
            + (status if resolved else "executable not found")
            + conflict_note
        )
    emit(json_out, {"profiles": rows}, "\n".join(lines))
    if not all_ok:
        raise typer.Exit(code=EXIT_RUNTIME)
