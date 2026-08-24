"""Harness profile sets: default location, seeding, load/write, path resolution.

Profiles are local and gitignored (plan section 6.1: `~/.agentteam/profiles.yaml`,
override with `AGENTTEAM_HOME`). Relative `executable`/`config_home` values
resolve against the profile file's own directory so a checked-in fake profile
(`examples/profiles/ci-fake.yaml`) is position-independent.

The seeded conflict lists implement plan section 11's fail-closed rule; the
plan names only the categories, so the concrete names live here as data
(fact sheet 2026-08-23) and stay owner-editable in the profile file.
"""

from __future__ import annotations

import contextlib
import os
import shutil
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path

import yaml
from pydantic import ValidationError

from agentteam.domain.common import HarnessId
from agentteam.domain.profile import (
    CapabilityRecordV1,
    EnvironmentNamesV1,
    HarnessProfileSetV1,
    HarnessProfileV1,
    ProxyPolicy,
    Verification,
)


class ProfileError(ValueError):
    """The profile set cannot be loaded/parsed."""


_PROXY_CONFLICTS = [
    name
    for base in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY")
    for name in (base, base.lower())
]

# Per-harness conflict variables (categories from plan section 11; names are
# data — fact sheet 2026-08-23). Owners may extend them in profiles.yaml.
_CONFLICTS: dict[HarnessId, list[str]] = {
    HarnessId.CLAUDE_CODE: [
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_AUTH_TOKEN",
        "ANTHROPIC_BASE_URL",
        "CLAUDE_CODE_USE_BEDROCK",
        "CLAUDE_CODE_USE_VERTEX",
    ],
    HarnessId.CODEX: ["CODEX_API_KEY", "OPENAI_API_KEY", "OPENAI_BASE_URL"],
    HarnessId.GROK: ["XAI_API_KEY", "GROK_AUTH_PROVIDER_COMMAND"],
}

_CONFIG_HOME_VARS: dict[HarnessId, str] = {
    HarnessId.CLAUDE_CODE: "CLAUDE_CONFIG_DIR",
    HarnessId.CODEX: "CODEX_HOME",
    HarnessId.GROK: "GROK_HOME",
}

_EXECUTABLES: dict[HarnessId, str] = {
    HarnessId.CLAUDE_CODE: "claude",
    HarnessId.CODEX: "codex",
    HarnessId.GROK: "grok",
}

# Capability rows seeded from the 2026-08-23 fact sheet; probes upgrade them.
_SEED_CAPABILITIES: dict[HarnessId, list[tuple[str, Verification]]] = {
    HarnessId.CLAUDE_CODE: [
        ("headless-json", Verification.OBSERVED),
        ("structured-output", Verification.OBSERVED),
        ("native-auth", Verification.UNVERIFIED),
        ("append-system-prompt", Verification.OBSERVED),
        ("append-system-prompt-file", Verification.UNVERIFIED),
        ("skills-config-home", Verification.UNVERIFIED),
        ("skills-plugin-dir", Verification.OBSERVED),
        ("skills-workspace", Verification.OBSERVED),
    ],
    HarnessId.CODEX: [
        ("headless-jsonl", Verification.OBSERVED),
        ("structured-output", Verification.OBSERVED),
        ("output-last-message", Verification.OBSERVED),
        ("native-auth", Verification.UNVERIFIED),
        ("jsonl-final-agent-message", Verification.UNVERIFIED),
        ("instructions-workspace-agents-md", Verification.OBSERVED),
        ("instructions-model-instructions-file", Verification.OBSERVED),
        ("instructions-developer-instructions", Verification.OBSERVED),
        ("skills-workspace", Verification.OBSERVED),
    ],
    HarnessId.GROK: [
        ("headless-json", Verification.OBSERVED),
        ("structured-output", Verification.OBSERVED),
        ("prompt-file", Verification.OBSERVED),
        ("instructions-rules", Verification.OBSERVED),
        ("instructions-system-prompt-override", Verification.OBSERVED),
        ("skills-workspace-grok", Verification.OBSERVED),
        ("skills-workspace-agents", Verification.OBSERVED),
        ("structured-output-field", Verification.UNVERIFIED),
        ("structured-output-text", Verification.UNVERIFIED),
        ("native-auth", Verification.UNVERIFIED),
    ],
}


def seed_default_profiles() -> HarnessProfileSetV1:
    """Non-secret starting profiles for the three first-pass harnesses."""
    profiles = []
    for harness in (HarnessId.CLAUDE_CODE, HarnessId.CODEX, HarnessId.GROK):
        profiles.append(
            HarnessProfileV1(
                harness=harness,
                executable=_EXECUTABLES[harness],
                config_home=f"vendors/{harness.value}",
                # A normal AgentTeam profile follows the owner's terminal
                # network path.  The proxy names remain in `conflicts` so an
                # owner can switch this profile back to `deny` without also
                # reconstructing the fail-closed list.
                proxy_policy=ProxyPolicy.INHERIT,
                environment=EnvironmentNamesV1(
                    config_home_variable=_CONFIG_HOME_VARS[harness],
                    conflicts=_CONFLICTS[harness] + _PROXY_CONFLICTS,
                ),
                capabilities=[
                    CapabilityRecordV1(name=name, verification=level)
                    for name, level in _SEED_CAPABILITIES[harness]
                ],
            )
        )
    return HarnessProfileSetV1(
        schema_version=1,
        kind="harness-profile-set",
        profiles=profiles,
        default_harness=HarnessId.CLAUDE_CODE,
    )


def default_profile_path(env: Mapping[str, str]) -> Path:
    home = env.get("AGENTTEAM_HOME")
    root = Path(home) if home else Path.home() / ".agentteam"
    return root / "profiles.yaml"


def load_profile_set(path: Path) -> HarnessProfileSetV1:
    path = Path(path)
    if not path.is_file():
        raise ProfileError(f"no profile set at {path} (run `atm profile init`)")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise ProfileError(f"{path}: not valid YAML: {error}") from None
    try:
        return HarnessProfileSetV1.model_validate(data)
    except ValidationError as error:
        details = "; ".join(
            f"{'.'.join(str(loc) for loc in item['loc'])}: {item['msg']}"
            for item in error.errors(include_url=False)
        )
        raise ProfileError(f"{path}: {details}") from None


def write_profile_set(
    path: Path, profile_set: HarnessProfileSetV1, *, platform: str | None = None
) -> None:
    payload = profile_set.model_dump(mode="json")
    atomic_write_text(path, yaml.safe_dump(payload, sort_keys=False), platform=platform)


def ensure_owner_directory(path: Path, *, platform: str | None = None) -> None:
    """Create an owner-only directory without accepting a symlink at the target."""
    path = Path(path)
    missing: list[Path] = []
    current = path
    while not current.exists():
        if current.is_symlink():
            raise ProfileError(f"unsafe symlinked directory: {current}")
        missing.append(current)
        parent = current.parent
        if parent == current:
            break
        current = parent
    if current.is_symlink() or path.is_symlink():
        raise ProfileError(
            f"unsafe symlinked directory: {current if current.is_symlink() else path}"
        )
    path.mkdir(parents=True, exist_ok=True)
    if not path.is_dir():
        raise ProfileError(f"not a directory: {path}")
    if (platform or sys.platform) != "win32":
        for directory in reversed(missing):
            with contextlib.suppress(OSError):
                directory.chmod(0o700)
        with contextlib.suppress(OSError):
            path.chmod(0o700)


def atomic_write_text(path: Path, text: str, *, platform: str | None = None) -> None:
    """Atomically replace one owner-only UTF-8 file in its destination directory."""
    path = Path(path)
    ensure_owner_directory(path.parent, platform=platform)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        if (platform or sys.platform) != "win32":
            os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            descriptor = -1
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        if (platform or sys.platform) != "win32":
            with contextlib.suppress(OSError):
                path.chmod(0o600)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        with contextlib.suppress(OSError):
            temporary.unlink()


def resolve_profile_path(profile_file: Path, value: str) -> Path:
    """Resolve a profile `executable`/`config_home` value.

    Absolute stays absolute; `~` expands; anything else is relative to the
    profile file's directory (makes checked-in fake profiles position-independent).
    """
    candidate = Path(value).expanduser()
    if candidate.is_absolute():
        return candidate
    resolved = (Path(profile_file).parent / candidate).resolve()
    return resolved


def resolve_config_home(profile_file: Path, value: str) -> Path:
    """Resolve a config home while refusing every symlinked path component."""
    candidate = Path(value).expanduser()
    lexical = candidate if candidate.is_absolute() else Path(profile_file).parent / candidate
    lexical = lexical.absolute()
    current = Path(lexical.anchor)
    for part in lexical.parts[1:]:
        current = current / part
        if current.is_symlink():
            raise ProfileError(f"unsafe symlink in config home: {current}")
    return lexical.resolve()


def resolve_profile_executable(profile_file: Path, value: str) -> Path:
    """Resolve path-like values against the profile and command names via PATH."""
    candidate = Path(value).expanduser()
    path_like = candidate.is_absolute() or candidate.parent != Path(".")
    if path_like:
        return resolve_profile_path(profile_file, value)
    profile_relative = Path(profile_file).parent / candidate
    if profile_relative.is_file():
        return profile_relative.resolve()
    found = shutil.which(value)
    return Path(found) if found is not None else resolve_profile_path(profile_file, value)
