"""Explicit installation and no-model-call diagnostics for execution runtimes."""

from __future__ import annotations

import asyncio
import os
import shutil
import sys
from pathlib import Path
from typing import Annotated

import typer

from agentteam.commands.common import EXIT_RUNTIME, emit, fail
from agentteam.domain.common import HarnessId
from agentteam.execution.direct_acp import (
    RUNTIME_ID,
    DirectAcpError,
    DirectAcpQualificationTarget,
    build_direct_acp_qualification_target,
    doctor_direct_acp,
    install_direct_acp,
    installed_runtime_path,
    installed_runtime_tree_hash,
)
from agentteam.resolution.profiles import (
    ProfileError,
    default_profile_path,
    load_profile_set,
)

runtime_app = typer.Typer(name="runtime", help="Optional execution-provider runtimes.")


def _require_direct_acp(runtime: str) -> None:
    if runtime != RUNTIME_ID:
        raise fail(f"unknown runtime: {runtime!r}")


def _parse_harnesses(values: list[str]) -> tuple[HarnessId, ...]:
    aliases = {"claude": HarnessId.CLAUDE_CODE.value}
    parsed: list[HarnessId] = []
    for value in values:
        try:
            harness = HarnessId(aliases.get(value, value))
        except ValueError:
            raise fail(f"unknown harness: {value!r}") from None
        if harness not in parsed:
            parsed.append(harness)
    return tuple(parsed)


def _qualification_targets(
    *,
    config: Path | None,
    selected: tuple[HarnessId, ...],
) -> tuple[tuple[DirectAcpQualificationTarget, ...], dict[str, str]]:
    profile_path = config or default_profile_path(os.environ)
    try:
        profile_set = load_profile_set(profile_path)
    except ProfileError as error:
        return (), {"profile-set": str(error)}
    profiles = {profile.harness: profile for profile in profile_set.profiles}
    requested = selected or tuple(profiles)
    runtime_path = installed_runtime_path(os.environ)
    try:
        runtime_tree_hash = installed_runtime_tree_hash(runtime_path)
    except DirectAcpError:
        runtime_tree_hash = None
    node = shutil.which("node", path=os.environ.get("PATH")) or "node"
    targets: list[DirectAcpQualificationTarget] = []
    problems: dict[str, str] = {}
    for harness in requested:
        profile = profiles.get(harness)
        if profile is None:
            problems[f"{harness.value}-profile"] = "harness profile is missing"
            continue
        try:
            targets.append(
                build_direct_acp_qualification_target(
                    profile,
                    profile_path=profile_path,
                    runtime_path=runtime_path,
                    node=node,
                    environ=os.environ,
                    platform=sys.platform,
                    runtime_tree_hash=runtime_tree_hash,
                )
            )
        except DirectAcpError as error:
            problems[f"{harness.value}-profile"] = str(error)
    return tuple(targets), problems


@runtime_app.command("install")
def install(
    runtime: Annotated[str, typer.Argument(help="Runtime id (direct-acp).")],
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Download only the exact packaged npm lock into AgentTeam's runtime store."""
    _require_direct_acp(runtime)
    try:
        path = install_direct_acp()
    except DirectAcpError as error:
        raise fail(str(error), exit_code=EXIT_RUNTIME) from None
    emit(
        json_out,
        {"runtime": RUNTIME_ID, "installed": True, "path": str(path)},
        f"installed {RUNTIME_ID}: {path}",
    )


@runtime_app.command("doctor")
def doctor(
    runtime: Annotated[str, typer.Argument(help="Runtime id (direct-acp).")],
    json_out: Annotated[bool, typer.Option("--json")] = False,
    config: Annotated[Path | None, typer.Option("--config")] = None,
    harness: Annotated[
        list[str] | None,
        typer.Option(
            "--harness",
            help="Limit no-call qualification; repeatable (claude-code, codex, grok).",
        ),
    ] = None,
) -> None:
    """Probe exact profiles through ACP initialize/resume/close; zero model calls."""
    _require_direct_acp(runtime)
    selected = _parse_harnesses(harness or [])
    targets, setup_problems = _qualification_targets(config=config, selected=selected)
    report = asyncio.run(
        doctor_direct_acp(
            environ=os.environ,
            platform=sys.platform,
            targets=targets,
            setup_problems=setup_problems,
        )
    )
    payload = report.model_dump(mode="json")
    emit(
        json_out,
        payload,
        f"{runtime}: {report.status}; model calls: 0\n"
        + "\n".join(
            f"{check.name}: {check.status}{': ' + check.detail if check.detail else ''}"
            for check in report.checks
        ),
    )
    if report.status != "pass":
        raise typer.Exit(code=EXIT_RUNTIME)
