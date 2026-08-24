"""Sanitized, no-model-call profile diagnostics and probe preflight."""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agentteam.domain.common import HarnessId
from agentteam.domain.profile import HarnessProfileV1, Verification
from agentteam.harness.capabilities import readiness_problems
from agentteam.harness.diagnostics import capture_cli
from agentteam.resolution.profiles import (
    ProfileError,
    resolve_config_home,
    resolve_profile_executable,
)

_HELP_CHECKS: dict[HarnessId, tuple[tuple[str, ...], tuple[str, ...]]] = {
    HarnessId.CLAUDE_CODE: (
        ("--help",),
        (
            "--output-format",
            "--json-schema",
            "--append-system-prompt",
            "--plugin-dir",
            "--setting-sources",
            "--mcp-config",
            "--strict-mcp-config",
            "--permission-mode",
            "--no-session-persistence",
        ),
    ),
    HarnessId.CODEX: (
        ("exec", "--help"),
        (
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--skip-git-repo-check",
            "--output-schema",
            "--output-last-message",
            "--json",
            "--sandbox",
            "--cd",
            "--config",
        ),
    ),
    HarnessId.GROK: (
        ("--help",),
        (
            "--prompt-file",
            "--output-format",
            "--no-subagents",
            "--sandbox",
            "--rules",
            "--system-prompt-override",
            "--json-schema",
        ),
    ),
}


@dataclass(frozen=True)
class DiagnosticReport:
    rows: list[dict[str, Any]]
    exit_code: int
    probe_preflight_ok: bool


def diagnose_profiles(
    profiles: list[HarnessProfileV1],
    *,
    profile_path: Path,
    environ: Mapping[str, str] | None = None,
    platform: str = sys.platform,
) -> DiagnosticReport:
    """Assess install/auth/readiness without changing the profile or making a model call."""
    parent = dict(os.environ if environ is None else environ)
    rows: list[dict[str, Any]] = []
    invalid = False
    unhealthy = False
    probe_ok = True
    for profile in profiles:
        row, row_invalid, row_unhealthy, row_probe_ok = _diagnose_one(
            profile, profile_path=profile_path, parent=parent, platform=platform
        )
        rows.append(row)
        invalid = invalid or row_invalid
        unhealthy = unhealthy or row_unhealthy
        probe_ok = probe_ok and row_probe_ok
    exit_code = 2 if invalid else (1 if unhealthy else 0)
    return DiagnosticReport(rows=rows, exit_code=exit_code, probe_preflight_ok=probe_ok)


def _diagnose_one(
    profile: HarnessProfileV1,
    *,
    profile_path: Path,
    parent: Mapping[str, str],
    platform: str,
) -> tuple[dict[str, Any], bool, bool, bool]:
    invalid = False
    problems: list[str] = []
    try:
        executable = resolve_profile_executable(profile_path, profile.executable)
        home = resolve_config_home(profile_path, profile.config_home)
    except ProfileError as error:
        invalid = True
        executable = Path(profile.executable)
        home = Path(profile.config_home)
        problems.append(str(error))

    executable_resolved = executable.is_file()
    if executable_resolved and platform != "win32" and not os.access(executable, os.X_OK):
        executable_resolved = False
        problems.append("executable is not owner-executable")
    if not executable_resolved:
        problems.append("executable not found")

    conflicts = sorted(name for name in profile.environment.conflicts if name in parent)
    if conflicts:
        invalid = True
        problems.append("conflicting environment variables are set")

    home_exists = home.is_dir() and not home.is_symlink()
    if not home_exists:
        problems.append("config home does not exist")

    concrete = profile.model_copy(update={"executable": str(executable), "config_home": str(home)})
    version: str | None = None
    missing_flags: list[str] = []
    if executable_resolved:
        code, stdout, _stderr = capture_cli(
            concrete, ["--version"], parent=parent, platform=platform
        )
        if code == 0:
            version = stdout.decode("utf-8", errors="replace").strip() or None
        if version is None:
            problems.append("--version failed")
        help_args, required_flags = _HELP_CHECKS[profile.harness]
        help_code, help_stdout, help_stderr = capture_cli(
            concrete, help_args, parent=parent, platform=platform
        )
        help_text = (help_stdout + b"\n" + help_stderr).decode("utf-8", errors="replace")
        if help_code != 0:
            missing_flags = list(required_flags)
        else:
            missing_flags = [flag for flag in required_flags if flag not in help_text]
        if missing_flags:
            problems.append("required flags missing: " + ", ".join(missing_flags))

    expected_mismatch = profile.expected_version is not None and version != profile.expected_version
    if expected_mismatch:
        problems.append(f"expected version {profile.expected_version!r}, found {version!r}")

    auth_state = _auth_state(
        concrete,
        version=version,
        parent=parent,
        platform=platform,
        safe_to_query=executable_resolved and home_exists and not conflicts,
    )
    if auth_state == "signed-out":
        problems.append("native subscription is signed out")
    elif auth_state == "unknown" and profile.harness is not HarnessId.GROK:
        problems.append("native authentication status could not be verified")

    readiness = readiness_problems(profile, cli_version=version, needs_skills=True)
    stale = any(
        capability.verification is Verification.VERIFIED
        and capability.cli_version is not None
        and capability.cli_version != version
        for capability in profile.capabilities
    )
    counts = {
        state.value: sum(1 for item in profile.capabilities if item.verification is state)
        for state in Verification
    }
    row: dict[str, Any] = {
        "harness": profile.harness.value,
        "executable_resolved": executable_resolved,
        "version": version,
        "config_home_exists": home_exists,
        "conflicts_set": conflicts,
        "capabilities": counts,
        "auth": auth_state,
        "auth_state": auth_state,
        "expected_version_mismatch": expected_mismatch,
        "required_flags_missing": missing_flags,
        "stale": stale,
        "readiness": {"ready": not readiness, "problems": readiness},
        "problems": problems,
        "probe": {
            "status": "not-requested",
            "calls_used": 0,
            "capture_id": None,
            "profile_updated": False,
        },
    }
    auth_healthy = auth_state in {"signed-in", "verified-by-probe"} or (
        profile.harness is HarnessId.GROK and auth_state == "unverified"
    )
    probe_preflight_ok = (
        not invalid
        and executable_resolved
        and version is not None
        and home_exists
        and not expected_mismatch
        and not missing_flags
        and auth_healthy
    )
    unhealthy = bool(problems or readiness)
    return row, invalid, unhealthy, probe_preflight_ok


def _auth_state(
    profile: HarnessProfileV1,
    *,
    version: str | None,
    parent: Mapping[str, str],
    platform: str,
    safe_to_query: bool,
) -> str:
    if not safe_to_query:
        return "unknown"
    if profile.harness is HarnessId.CLAUDE_CODE:
        code, stdout, _stderr = capture_cli(
            profile, ["auth", "status", "--json"], parent=parent, platform=platform
        )
        if code not in (0, 1):
            return "unknown"
        try:
            payload = json.loads(stdout.decode("utf-8", errors="replace"))
        except json.JSONDecodeError:
            return "unknown"
        if isinstance(payload, dict) and payload.get("loggedIn") is True:
            return "signed-in"
        if isinstance(payload, dict) and payload.get("loggedIn") is False:
            return "signed-out"
        return "unknown"
    if profile.harness is HarnessId.CODEX:
        code, stdout, stderr = capture_cli(
            profile, ["login", "status"], parent=parent, platform=platform
        )
        text = (stdout + b"\n" + stderr).decode("utf-8", errors="replace").lower()
        if code == 0 and "logged in" in text and "not logged in" not in text:
            return "signed-in"
        if "not logged in" in text or "signed out" in text or code == 1:
            return "signed-out"
        return "unknown"
    native = next((row for row in profile.capabilities if row.name == "native-auth"), None)
    if (
        native is not None
        and native.verification is Verification.VERIFIED
        and native.cli_version == version
        and native.verified_at is not None
    ):
        return "verified-by-probe"
    return "unverified"
