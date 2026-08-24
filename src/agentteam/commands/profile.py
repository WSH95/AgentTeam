"""`atm profile init/validate/doctor --probe` native-profile lifecycle."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Annotated, Any

import typer
from click import Abort

from agentteam.commands.common import EXIT_CANCELLED, emit, fail
from agentteam.domain.common import HarnessId
from agentteam.domain.profile import ProfileKind
from agentteam.profile.doctor import DiagnosticReport, diagnose_profiles
from agentteam.profile.probe import (
    ProbeCancelled,
    ProbeHarnessResult,
    run_attended_probes,
)
from agentteam.profile.setup import initialize_profiles
from agentteam.resolution.profiles import (
    ProfileError,
    default_profile_path,
    load_profile_set,
)

profile_app = typer.Typer(name="profile", help="Local harness profiles (never committed).")


def _config_option(value: Path | None) -> Path:
    return value if value is not None else default_profile_path(os.environ)


@profile_app.command("init")
def init(
    config: Annotated[Path | None, typer.Option("--config")] = None,
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Create owner-only vendor homes, safe seed config, and profiles.yaml."""
    path = _config_option(config)
    try:
        result = initialize_profiles(path, platform=sys.platform)
    except (ProfileError, OSError) as error:
        raise fail(str(error)) from None
    payload = {
        "profile_file": str(result.profile_file),
        "config_homes": [str(home) for home in result.config_homes],
        "login_commands": result.login_commands,
    }
    human = (
        f"wrote {result.profile_file}\ncreated config homes:\n  "
        + "\n  ".join(str(home) for home in result.config_homes)
        + "\nNative subscription logins (run each yourself; AgentTeam never opens a browser "
        "and never reads or copies credential files):\n  " + "\n  ".join(result.login_commands)
    )
    emit(json_out, payload, human)


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


@profile_app.command("doctor")
def doctor(
    config: Annotated[Path | None, typer.Option("--config")] = None,
    json_out: Annotated[bool, typer.Option("--json")] = False,
    probe: Annotated[
        bool,
        typer.Option(
            "--probe",
            help="Run attended native-auth probes (up to two confirmed calls per harness).",
        ),
    ] = False,
) -> None:
    """Check installations/auth/readiness; optionally run bounded attended probes."""
    path = _config_option(config)
    try:
        profile_set = load_profile_set(path)
    except ProfileError as error:
        raise fail(str(error)) from None

    report = diagnose_profiles(
        profile_set.profiles,
        profile_path=path,
        environ=os.environ,
        platform=sys.platform,
    )
    if not probe:
        _emit_doctor(json_out, report.rows)
        if report.exit_code != 0:
            raise typer.Exit(report.exit_code)
        return

    if not _is_attended():
        raise fail("--probe requires an attended TTY", exit_code=2)
    required = {HarnessId.CLAUDE_CODE, HarnessId.CODEX, HarnessId.GROK}
    present = {profile.harness for profile in profile_set.profiles}
    if present != required or any(
        profile.kind is not ProfileKind.NATIVE for profile in profile_set.profiles
    ):
        raise fail("--probe requires one native Claude, Codex, and Grok profile", exit_code=2)
    if not report.probe_preflight_ok:
        rows = _merge_probe_rows(
            report.rows,
            {},
            default_status="preflight-failed",
        )
        _emit_doctor(json_out, rows)
        raise typer.Exit(report.exit_code or 1)

    versions = {
        HarnessId(row["harness"]): row["version"]
        for row in report.rows
        if isinstance(row.get("version"), str)
    }
    try:
        probe_result = run_attended_probes(
            profile_set.profiles,
            profile_path=path,
            versions=versions,
            environ=dict(os.environ),
            confirm=_confirm_call,
            platform=sys.platform,
        )
    except ProbeCancelled as cancelled:
        refreshed = _refresh(path)
        rows = _merge_probe_rows(
            refreshed.rows,
            cancelled.results,
            default_status="not-run",
        )
        _emit_doctor(json_out, rows)
        raise typer.Exit(EXIT_CANCELLED) from None
    except (ProfileError, OSError, ValueError) as error:
        raise fail(f"probe failed safely: {error}", exit_code=2) from None

    refreshed = _refresh(path)
    rows = _merge_probe_rows(refreshed.rows, probe_result.by_harness)
    _emit_doctor(json_out, rows)
    if not probe_result.all_ready or refreshed.exit_code != 0:
        raise typer.Exit(1)


def _refresh(path: Path) -> DiagnosticReport:
    profile_set = load_profile_set(path)
    return diagnose_profiles(
        profile_set.profiles,
        profile_path=path,
        environ=os.environ,
        platform=sys.platform,
    )


def _is_attended() -> bool:
    return sys.stdin.isatty() and sys.stderr.isatty()


def _confirm_call(harness: HarnessId, call_number: int, description: str) -> bool:
    try:
        return typer.confirm(
            f"Invoke {harness.value} probe call {call_number}/2 ({description})?",
            default=False,
            err=True,
        )
    except Abort as error:
        # Click normalizes Ctrl-C/EOF during a prompt to Abort. Convert it
        # back so the probe engine can retain completed evidence and emit 130.
        raise KeyboardInterrupt from error


def _merge_probe_rows(
    rows: list[dict[str, Any]],
    results: dict[HarnessId, ProbeHarnessResult],
    *,
    default_status: str = "not-run",
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for row in rows:
        harness = HarnessId(row["harness"])
        result = results.get(harness)
        probe = (
            {
                "status": result.status,
                "calls_used": result.calls_used,
                "capture_id": result.capture_id,
                "profile_updated": result.profile_updated,
            }
            if result is not None
            else {
                "status": default_status,
                "calls_used": 0,
                "capture_id": None,
                "profile_updated": False,
            }
        )
        merged.append({**row, "probe": probe})
    return merged


def _emit_doctor(json_out: bool, rows: list[dict[str, Any]]) -> None:
    lines = []
    for row in rows:
        version = row["version"] or "version unavailable"
        ready = "ready" if row["readiness"]["ready"] else "not ready"
        probe = row["probe"]
        lines.append(
            f"{row['harness']}: {version}; auth {row['auth_state']}; {ready}; "
            f"probe {probe['status']} ({probe['calls_used']} call(s))"
        )
        if row["conflicts_set"]:
            lines.append("  conflicts set: " + ", ".join(row["conflicts_set"]))
        for problem in row["problems"]:
            lines.append(f"  {problem}")
        for problem in row["readiness"]["problems"]:
            lines.append(f"  readiness: {problem}")
    emit(json_out, {"profiles": rows}, "\n".join(lines))
