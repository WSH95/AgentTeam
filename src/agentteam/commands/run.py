"""`atm run` (plan sections 8 and 12).

`--render-only` resolves the request exactly as a live run would (profiles,
selection with `decided_by`, model/effort precedence, bundle hashing) and
writes every rendered invocation for inspection without launching anything.
Without it, the direct ensemble state machine runs: pending archive first,
isolated per-leg workspace copies, concurrent legs, one transient retry,
synthesis over labelled reports, acceptance tiers, stable exit codes
(0 success, 1 runtime/harness, 2 invalid input, 3 semantic, 130 cancelled).
"""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from agentteam.commands.common import EXIT_CANCELLED, emit, fail
from agentteam.domain.bundle import AssistantRefV1
from agentteam.domain.common import HarnessId
from agentteam.domain.request import HarnessOverrideV1
from agentteam.harness import get_adapter
from agentteam.harness.environment import EnvironmentConflictError
from agentteam.harness.rendering import RenderError
from agentteam.harness.types import RenderContext
from agentteam.resolution.archive import build_bundle_manifest
from agentteam.resolution.profiles import default_profile_path
from agentteam.run.preflight import PreflightError, ResolvedRun, build_request, preflight
from agentteam.run.runner import execute_run
from agentteam.run.team import TeamInfrastructureError, execute_team_run, render_team_only
from agentteam.run.team_preflight import (
    load_team_request,
    preflight_team,
    request_kind,
)

_ALIASES = {"claude": "claude-code"}


def _normalise_harness(value: str) -> HarnessId:
    name = _ALIASES.get(value, value)
    try:
        return HarnessId(name)
    except ValueError:
        raise fail(f"unknown harness: {value!r}") from None


def _parse_overrides(values: list[str], flag: str) -> list[HarnessOverrideV1]:
    overrides = []
    for value in values:
        if "=" not in value:
            raise fail(f"{flag} takes harness=value, got {value!r}")
        harness_raw, _, override = value.partition("=")
        harness = _ALIASES.get(harness_raw, harness_raw)
        try:
            overrides.append(HarnessOverrideV1(harness=HarnessId(harness), value=override))
        except (ValueError, ValidationError) as error:
            raise fail(f"{flag} {value!r}: {error}") from None
    return overrides


def register_run(app: typer.Typer) -> None:
    @app.command("run")
    def run(
        request_file: Annotated[
            Path | None, typer.Argument(help="Optional request.yaml|request.json.")
        ] = None,
        assistant: Annotated[Path | None, typer.Option("--assistant")] = None,
        workspace: Annotated[Path | None, typer.Option("--workspace")] = None,
        task_file: Annotated[Path | None, typer.Option("--task-file")] = None,
        harness: Annotated[
            list[str] | None, typer.Option("--harness", help="Repeatable; `claude` is an alias.")
        ] = None,
        model: Annotated[
            list[str] | None, typer.Option("--model", help="harness=model, repeatable.")
        ] = None,
        effort: Annotated[
            list[str] | None, typer.Option("--effort", help="harness=effort, repeatable.")
        ] = None,
        no_synthesis: Annotated[bool, typer.Option("--no-synthesis")] = False,
        render_only: Annotated[
            bool, typer.Option("--render-only", help="Write rendered invocations; launch nothing.")
        ] = False,
        output_dir: Annotated[Path | None, typer.Option("--output-dir")] = None,
        config: Annotated[Path | None, typer.Option("--config")] = None,
        json_out: Annotated[bool, typer.Option("--json")] = False,
    ) -> None:
        """Run one Assistant or a committed TeamRun request."""
        if request_file is not None and request_kind(request_file) == "team-run-request":
            forbidden_flags: list[str] = []
            for present, name in (
                (assistant is not None, "--assistant"),
                (workspace is not None, "--workspace"),
                (task_file is not None, "--task-file"),
                (bool(harness), "--harness"),
                (bool(model), "--model"),
                (bool(effort), "--effort"),
                (no_synthesis, "--no-synthesis"),
            ):
                if present:
                    forbidden_flags.append(name)
            if forbidden_flags:
                raise fail(
                    "team mode takes run-shaping values from the request file's "
                    "members map; unsupported flags: " + ", ".join(forbidden_flags)
                )
            try:
                team_request = load_team_request(request_file, output_dir=output_dir)
                profile_path = config if config is not None else default_profile_path(os.environ)
                team_resolved = preflight_team(
                    team_request,
                    request_path=request_file,
                    profile_path=profile_path,
                    live=not render_only,
                    environ=os.environ,
                    platform=sys.platform,
                )
                if render_only:
                    summary = render_team_only(
                        team_resolved,
                        environ=dict(os.environ),
                        platform=sys.platform,
                    )
                    emit(
                        json_out,
                        summary,
                        f"rendered {len(team_resolved.members)} team members into "
                        f"{summary['output_dir']}; nothing launched",
                    )
                    return
                outcome = asyncio.run(execute_team_run(team_resolved, environ=dict(os.environ)))
            except (PreflightError, RenderError, EnvironmentConflictError) as error:
                raise fail(str(error), exit_code=2) from None
            except TeamInfrastructureError as error:
                raise fail(str(error), exit_code=1) from None
            except KeyboardInterrupt:
                raise typer.Exit(EXIT_CANCELLED) from None
            emit(json_out, outcome.summary, outcome.human)
            if outcome.exit_code != 0:
                raise typer.Exit(outcome.exit_code)
            return

        try:
            request = build_request(
                request_file=request_file,
                assistant=assistant,
                workspace=workspace,
                task_file=task_file,
                harnesses=[_normalise_harness(h).value for h in (harness or [])],
                model_overrides=_parse_overrides(model or [], "--model"),
                effort_overrides=_parse_overrides(effort or [], "--effort"),
                no_synthesis=no_synthesis,
                output_dir=output_dir,
            )
        except PreflightError as error:
            raise fail(str(error), exit_code=error.exit_code) from None

        profile_path = config if config is not None else default_profile_path(os.environ)
        try:
            resolved = preflight(
                request,
                profile_path=profile_path,
                live=not render_only,
                environ=os.environ,
                platform=sys.platform,
            )
        except PreflightError as error:
            raise fail(str(error), exit_code=error.exit_code) from None

        if render_only:
            _render_only(resolved, json_out)
            return

        try:
            outcome = asyncio.run(execute_run(resolved, environ=dict(os.environ)))
        except PreflightError as error:
            raise fail(str(error), exit_code=error.exit_code) from None
        except KeyboardInterrupt:
            raise typer.Exit(EXIT_CANCELLED) from None
        emit(json_out, outcome.summary, outcome.human)
        if outcome.exit_code != 0:
            raise typer.Exit(outcome.exit_code)


def _render_only(resolved: ResolvedRun, json_out: bool) -> None:
    request = resolved.request
    if request.output_dir is None:
        raise fail("--render-only needs an output directory (--output-dir or request output_dir)")
    out = Path(request.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    bundle = build_bundle_manifest(
        assistant=_assistant_ref(resolved),
        digest=resolved.digest,
        created_at=datetime.now(tz=UTC),
    )
    (out / "bundle-manifest.json").write_text(
        bundle.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )

    rendered_harnesses: list[str] = []
    for plan in resolved.legs:
        harness_out = out / plan.harness.value
        ctx = RenderContext(
            profile=plan.profile,
            definition=resolved.package.definition,
            package_root=resolved.package.root,
            bundle=bundle,
            selection=resolved.selection.selection,
            requested=plan.requested,
            task_file=Path(request.task_file),
            workspace=Path(request.workspace),
            workspace_root=harness_out / "workspace",
            config_root=harness_out / "config-home",
            scratch_dir=harness_out / "scratch",
            parent_env=dict(os.environ),
            platform=sys.platform,
            run_id="run-render-only",
            invocation_id=f"inv-{plan.harness.value}",
            timeout_seconds=resolved.timeout_seconds,
            cli_version=plan.cli_version,
            profile_file=resolved.profile_path,
        )
        adapter = get_adapter(plan.harness)
        try:
            rendered = adapter.render(ctx)
        except (RenderError, EnvironmentConflictError) as error:
            raise fail(f"{plan.harness.value}: {error}") from None
        (harness_out / "invocation.render.json").write_text(
            rendered.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )
        rendered_harnesses.append(plan.harness.value)

    emit(
        json_out,
        {
            "render_only": True,
            "harnesses": rendered_harnesses,
            "decided_by": resolved.selection.selection.decided_by.value,
            "package_hash": resolved.digest.package_hash,
            "effective_definition_hash": bundle.effective_definition_hash,
            "output_dir": str(out),
        },
        f"rendered {', '.join(rendered_harnesses)} into {out} "
        f"(decided_by: {resolved.selection.selection.decided_by.value}); nothing launched",
    )


def _assistant_ref(resolved: ResolvedRun) -> AssistantRefV1:
    return AssistantRefV1(
        id=resolved.package.definition.id,
        version=resolved.package.definition.version,
        package_hash=resolved.digest.package_hash,
    )
