"""Secure, credential-blind native profile initialization."""

from __future__ import annotations

import shlex
import sys
from dataclasses import dataclass
from pathlib import Path

from agentteam.domain.common import HarnessId
from agentteam.harness.skills import MARKER
from agentteam.resolution.profiles import (
    ProfileError,
    atomic_write_text,
    ensure_owner_directory,
    resolve_config_home,
    seed_default_profiles,
    write_profile_set,
)

CODEX_CONFIG = """\
cli_auth_credentials_store = "file"
forced_login_method = "chatgpt"
"""

GROK_CONFIG = """\
# AgentTeam's dedicated Grok home must not discover another harness's state.
[compat.cursor]
skills = false
rules = false
agents = false
mcps = false
hooks = false
sessions = false

[compat.claude]
skills = false
rules = false
agents = false
mcps = false
hooks = false
sessions = false
"""

_LOGIN_ARGS: dict[HarnessId, tuple[str, ...]] = {
    HarnessId.CLAUDE_CODE: ("auth", "login"),
    HarnessId.CODEX: ("login",),
    HarnessId.GROK: ("login", "--oauth"),
}


@dataclass(frozen=True)
class InitResult:
    profile_file: Path
    config_homes: list[Path]
    login_commands: list[str]


def initialize_profiles(path: Path, *, platform: str = sys.platform) -> InitResult:
    """Create a new profile set without opening or copying any credential file."""
    path = Path(path).expanduser().absolute()
    if path.exists() or path.is_symlink():
        raise ProfileError(f"profile file already exists: {path} (edit it, or move it away first)")
    _reject_symlink_components(path.parent)

    profile_set = seed_default_profiles()
    homes: list[Path] = []
    for profile in profile_set.profiles:
        home = resolve_config_home(path, profile.config_home)
        if home.exists() and not home.is_dir():
            raise ProfileError(f"config home is not a directory: {home}")
        homes.append(home)

    claude_home = homes[0]
    claude_skills = claude_home / "skills"
    if claude_skills.is_symlink():
        raise ProfileError(f"unsafe symlinked Claude Skill directory: {claude_skills}")
    if (
        claude_skills.exists()
        and not (claude_skills / MARKER).is_file()
        and any(claude_skills.iterdir())
    ):
        raise ProfileError(f"refusing unmarked nonempty Claude Skill directory: {claude_skills}")

    seeded_files = {
        homes[1] / "config.toml": CODEX_CONFIG,
        homes[2] / "config.toml": GROK_CONFIG,
    }
    for seed_path in seeded_files:
        if seed_path.exists() or seed_path.is_symlink():
            raise ProfileError(f"refusing to overwrite vendor configuration: {seed_path}")

    ensure_owner_directory(path.parent, platform=platform)
    for home in homes:
        ensure_owner_directory(home, platform=platform)
    ensure_owner_directory(claude_skills, platform=platform)
    atomic_write_text(
        claude_skills / MARKER,
        "written by agentteam; safe to delete\n",
        platform=platform,
    )
    for seed_path, body in seeded_files.items():
        atomic_write_text(seed_path, body, platform=platform)
    write_profile_set(path, profile_set, platform=platform)

    commands = [
        _login_command(
            profile.executable,
            profile.environment.config_home_variable,
            home,
            _LOGIN_ARGS[profile.harness],
            platform,
        )
        for profile, home in zip(profile_set.profiles, homes, strict=True)
    ]
    return InitResult(profile_file=path, config_homes=homes, login_commands=commands)


def _reject_symlink_components(path: Path) -> None:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        if current.is_symlink():
            raise ProfileError(f"unsafe symlink in profile path: {current}")


def _login_command(
    executable: str,
    variable: str,
    home: Path,
    args: tuple[str, ...],
    platform: str,
) -> str:
    if platform == "win32":
        argv = " ".join(_powershell_quote(value) for value in (executable, *args))
        return f"$env:{variable} = {_powershell_quote(str(home))}; & {argv}"
    return f"{variable}={shlex.quote(str(home))} {shlex.join([executable, *args])}"


def _powershell_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"
