"""`atm run` (plan section 8). G3 implements `--render-only`; launching is G4.

Render-only resolves the request exactly as a live run would (profiles,
selection with `decided_by`, model/effort precedence, bundle hashing) and
writes every rendered invocation for inspection — without launching anything,
creating a run archive, or touching the real workspace or any vendor config
home: every write lands under the output directory.
"""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import typer
import yaml
from pydantic import ValidationError

from agentteam.commands.common import emit, fail
from agentteam.domain.bundle import AssistantRefV1
from agentteam.domain.common import HarnessId
from agentteam.domain.profile import ProfileKind
from agentteam.domain.request import HarnessOverrideV1, RunRequestV1
from agentteam.harness import get_adapter
from agentteam.harness.environment import EnvironmentConflictError
from agentteam.harness.rendering import RenderError
from agentteam.harness.types import RenderContext
from agentteam.resolution.archive import ArchiveContractError, build_bundle_manifest, hash_package
from agentteam.resolution.models import resolve_model_effort
from agentteam.resolution.package import PackageError, load_package
from agentteam.resolution.profiles import (
    ProfileError,
    default_profile_path,
    load_profile_set,
    resolve_profile_path,
)
from agentteam.resolution.selection import SelectionError, select_harnesses

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
        """Run one Assistant over a workspace (G3: --render-only; launching at G4)."""
        request = _build_request(
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
        if request.overlay_refs:
            raise fail("overlay_refs are reserved for M3 and must be empty in M1a")
        if not render_only:
            raise fail("launching arrives at G4; use --render-only to inspect the rendering")
        if request.output_dir is None:
            raise fail(
                "--render-only needs an output directory (--output-dir or request output_dir)"
            )

        profile_path = config if config is not None else default_profile_path(os.environ)
        try:
            profile_set = load_profile_set(profile_path)
        except ProfileError as error:
            raise fail(str(error)) from None
        by_id = {p.harness: p for p in profile_set.profiles}
        for harness_id in request.harnesses:
            profile = by_id.get(harness_id)
            if profile is not None and profile.kind is ProfileKind.API_TEST:
                raise fail(f"profile {harness_id.value} is api-test; the M1a runner is native-only")

        try:
            loaded = load_package(Path(request.assistant))
            digest = hash_package(Path(request.assistant))
        except (PackageError, ArchiveContractError) as error:
            raise fail(str(error)) from None

        def installed(profile) -> bool:  # type: ignore[no-untyped-def]
            resolved = resolve_profile_path(profile_path, profile.executable)
            import shutil as _shutil

            return resolved.is_file() or _shutil.which(str(profile.executable)) is not None

        try:
            outcome = select_harnesses(
                requested=list(request.harnesses),
                policy=loaded.definition.harness_policy,
                profiles=profile_set,
                installed=installed,
            )
        except SelectionError as error:
            raise fail(str(error), exit_code=error.exit_code) from None

        out = Path(request.output_dir)
        out.mkdir(parents=True, exist_ok=True)
        bundle = build_bundle_manifest(
            assistant=AssistantRefV1(
                id=loaded.definition.id,
                version=loaded.definition.version,
                package_hash=digest.package_hash,
            ),
            digest=digest,
            created_at=datetime.now(tz=UTC),
        )
        (out / "bundle-manifest.json").write_text(
            bundle.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )

        model_by_harness = {o.harness: o.value for o in request.model_overrides}
        effort_by_harness = {o.harness: o.value for o in request.effort_overrides}
        rendered_harnesses: list[str] = []
        for harness_id in outcome.chosen:
            profile = by_id[harness_id]
            executable = resolve_profile_path(profile_path, profile.executable)
            profile = profile.model_copy(update={"executable": str(executable)})
            requested = resolve_model_effort(
                harness=harness_id,
                cli_model=model_by_harness.get(harness_id),
                cli_effort=effort_by_harness.get(harness_id),
                request_model=None,
                request_effort=None,
                profile=profile,
                hints=loaded.definition.harness_policy.model_hints,
            )
            harness_out = out / harness_id.value
            ctx = RenderContext(
                profile=profile,
                definition=loaded.definition,
                package_root=loaded.root,
                bundle=bundle,
                selection=outcome.selection,
                requested=requested,
                task_file=Path(request.task_file),
                workspace=Path(request.workspace),
                workspace_root=harness_out / "workspace",
                config_root=harness_out / "config-home",
                scratch_dir=harness_out / "scratch",
                parent_env=dict(os.environ),
                platform=sys.platform,
                run_id="run-render-only",
                invocation_id=f"inv-{harness_id.value}",
                timeout_seconds=request.limits.attempt_seconds or 900,
                profile_file=profile_path,
            )
            adapter = get_adapter(harness_id)
            try:
                rendered = adapter.render(ctx)
            except (RenderError, EnvironmentConflictError) as error:
                raise fail(f"{harness_id.value}: {error}") from None
            (harness_out / "invocation.render.json").write_text(
                rendered.model_dump_json(indent=2) + "\n", encoding="utf-8"
            )
            rendered_harnesses.append(harness_id.value)

        emit(
            json_out,
            {
                "render_only": True,
                "harnesses": rendered_harnesses,
                "decided_by": outcome.selection.decided_by.value,
                "package_hash": digest.package_hash,
                "effective_definition_hash": bundle.effective_definition_hash,
                "output_dir": str(out),
            },
            f"rendered {', '.join(rendered_harnesses)} into {out} "
            f"(decided_by: {outcome.selection.decided_by.value}); nothing launched",
        )


def _build_request(
    *,
    request_file: Path | None,
    assistant: Path | None,
    workspace: Path | None,
    task_file: Path | None,
    harnesses: list[str],
    model_overrides: list[HarnessOverrideV1],
    effort_overrides: list[HarnessOverrideV1],
    no_synthesis: bool,
    output_dir: Path | None,
) -> RunRequestV1:
    data: dict[str, object] = {}
    if request_file is not None:
        if not request_file.is_file():
            raise fail(f"request file does not exist: {request_file}")
        try:
            data = yaml.safe_load(request_file.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as error:
            raise fail(f"{request_file}: not valid YAML/JSON: {error}") from None
        if not isinstance(data, dict):
            raise fail(f"{request_file}: the request must be a mapping")
    data.setdefault("schema_version", 1)
    data.setdefault("kind", "run-request")
    data.setdefault("mode", "direct")
    if assistant is not None:
        data["assistant"] = str(assistant)
    if workspace is not None:
        data["workspace"] = str(workspace)
    if task_file is not None:
        data["task_file"] = str(task_file)
    if harnesses:
        data["harnesses"] = harnesses
    if model_overrides:
        data["model_overrides"] = [o.model_dump(mode="json") for o in model_overrides]
    if effort_overrides:
        data["effort_overrides"] = [o.model_dump(mode="json") for o in effort_overrides]
    if no_synthesis:
        data["synthesis"] = {"enabled": False}
    if output_dir is not None:
        data["output_dir"] = str(output_dir)
    for required in ("assistant", "workspace", "task_file"):
        if required not in data:
            raise fail(f"missing {required.replace('_', '-')} (flag or request file)")
    try:
        return RunRequestV1.model_validate(data)
    except ValidationError as error:
        details = "; ".join(
            f"{'.'.join(str(loc) for loc in item['loc'])}: {item['msg']}"
            for item in error.errors(include_url=False)
        )
        raise fail(f"invalid run request: {details}") from None
