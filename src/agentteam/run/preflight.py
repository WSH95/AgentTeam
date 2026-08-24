"""Request building and run preflight (plan sections 8, 11, 12 steps 1-3).

`build_request` merges a request file with CLI flags: flags win field-by-field,
per-harness model/effort overrides merge (a CLI override replaces only its own
harness's entry), and path fields resolve against the request file's directory
when they came from the file, against the invoking CWD when they came from a
flag. `preflight` performs every validation and resolution step that must
happen before the pending archive exists; all failures are `PreflightError`
(exit 2, invalid/unsafe input).
"""

from __future__ import annotations

import os
import shutil
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import ValidationError

from agentteam.domain.assistant import ArtifactKind
from agentteam.domain.common import HarnessId
from agentteam.domain.profile import HarnessProfileSetV1, HarnessProfileV1, ProfileKind
from agentteam.domain.request import MAX_TRANSIENT_RETRIES, HarnessOverrideV1, RunRequestV1
from agentteam.domain.run import RequestedV1
from agentteam.harness.capabilities import readiness_problems
from agentteam.harness.diagnostics import capture_version
from agentteam.harness.environment import EnvironmentConflictError, build_environment
from agentteam.resolution.archive import ArchiveContractError, PackageDigest, hash_package
from agentteam.resolution.models import resolve_model_effort
from agentteam.resolution.package import LoadedPackage, PackageError, load_package
from agentteam.resolution.profiles import (
    ProfileError,
    load_profile_set,
    resolve_config_home,
    resolve_profile_executable,
)
from agentteam.resolution.selection import SelectionError, SelectionOutcome, select_harnesses

DEFAULT_TIMEOUT_SECONDS = 900


class PreflightError(ValueError):
    """Invalid or unsafe input; the run fails before any side effect (exit 2)."""

    exit_code = 2


@dataclass(frozen=True)
class LegPlan:
    harness: HarnessId
    profile: HarnessProfileV1  # executable already resolved to a concrete path/name
    requested: RequestedV1
    cli_version: str | None  # observed by live preflight; None only for render-only


@dataclass(frozen=True)
class ResolvedRun:
    request: RunRequestV1
    profile_path: Path
    profile_set: HarnessProfileSetV1
    package: LoadedPackage
    digest: PackageDigest
    selection: SelectionOutcome
    legs: list[LegPlan]
    synthesis_planned: bool
    synthesis_leg: LegPlan | None
    oracle_path: Path | None
    timeout_seconds: int
    transient_retries: int
    live_ready: bool


def _resolve_against(base: Path, value: str) -> str:
    path = Path(value)
    if path.is_absolute():
        return str(path)
    return str((base / path).resolve())


def _resolve_file_paths(data: dict[str, object], base: Path) -> None:
    for key in ("assistant", "workspace", "task_file", "output_dir"):
        value = data.get(key)
        if isinstance(value, str):
            data[key] = _resolve_against(base, value)
    acceptance = data.get("acceptance")
    if isinstance(acceptance, dict):
        oracle = acceptance.get("oracle")
        if isinstance(oracle, str):
            acceptance["oracle"] = _resolve_against(base, oracle)


def _merge_overrides(
    file_entries: object, cli_entries: Sequence[HarnessOverrideV1]
) -> list[dict[str, str]]:
    merged: dict[str, str] = {}
    if isinstance(file_entries, list):
        for entry in file_entries:
            if isinstance(entry, dict) and "harness" in entry and "value" in entry:
                merged[str(entry["harness"])] = str(entry["value"])
    for override in cli_entries:
        merged[override.harness.value] = override.value
    return [{"harness": harness, "value": value} for harness, value in merged.items()]


def build_request(
    *,
    request_file: Path | None,
    assistant: Path | None,
    workspace: Path | None,
    task_file: Path | None,
    harnesses: Sequence[str],
    model_overrides: Sequence[HarnessOverrideV1],
    effort_overrides: Sequence[HarnessOverrideV1],
    no_synthesis: bool,
    output_dir: Path | None,
    cwd: Path | None = None,
) -> RunRequestV1:
    invoke_base = (cwd or Path.cwd()).resolve()
    data: dict[str, object] = {}
    if request_file is not None:
        if not request_file.is_file():
            raise PreflightError(f"request file does not exist: {request_file}")
        try:
            loaded = yaml.safe_load(request_file.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as error:
            raise PreflightError(f"{request_file}: not valid YAML/JSON: {error}") from None
        if not isinstance(loaded, dict):
            raise PreflightError(f"{request_file}: the request must be a mapping")
        data = loaded
        _resolve_file_paths(data, request_file.parent.resolve())
    data.setdefault("schema_version", 1)
    data.setdefault("kind", "run-request")
    data.setdefault("mode", "direct")
    if assistant is not None:
        data["assistant"] = _resolve_against(invoke_base, str(assistant))
    if workspace is not None:
        data["workspace"] = _resolve_against(invoke_base, str(workspace))
    if task_file is not None:
        data["task_file"] = _resolve_against(invoke_base, str(task_file))
    if harnesses:
        data["harnesses"] = list(harnesses)
    if model_overrides or "model_overrides" in data:
        data["model_overrides"] = _merge_overrides(data.get("model_overrides"), model_overrides)
    if effort_overrides or "effort_overrides" in data:
        data["effort_overrides"] = _merge_overrides(data.get("effort_overrides"), effort_overrides)
    if no_synthesis:
        synthesis = data.get("synthesis")
        base_synthesis = dict(synthesis) if isinstance(synthesis, dict) else {}
        base_synthesis["enabled"] = False
        data["synthesis"] = base_synthesis
    if output_dir is not None:
        data["output_dir"] = _resolve_against(invoke_base, str(output_dir))
    for required in ("assistant", "workspace", "task_file"):
        if required not in data:
            raise PreflightError(f"missing {required.replace('_', '-')} (flag or request file)")
    try:
        return RunRequestV1.model_validate(data)
    except ValidationError as error:
        details = "; ".join(
            f"{'.'.join(str(loc) for loc in item['loc'])}: {item['msg']}"
            for item in error.errors(include_url=False)
        )
        raise PreflightError(f"invalid run request: {details}") from None


def _default_installed(profile_path: Path) -> Callable[[HarnessProfileV1], bool]:
    def installed(profile: HarnessProfileV1) -> bool:
        resolved = resolve_profile_executable(profile_path, profile.executable)
        return resolved.is_file() or shutil.which(str(profile.executable)) is not None

    return installed


def _leg_plan(
    harness: HarnessId,
    *,
    profile: HarnessProfileV1,
    profile_path: Path,
    request: RunRequestV1,
    resolved: LoadedPackage,
    cli_version: str | None,
) -> LegPlan:
    executable = resolve_profile_executable(profile_path, profile.executable)
    config_home = resolve_config_home(profile_path, profile.config_home)
    concrete = profile.model_copy(
        update={"executable": str(executable), "config_home": str(config_home)}
    )
    model_by_harness = {o.harness: o.value for o in request.model_overrides}
    effort_by_harness = {o.harness: o.value for o in request.effort_overrides}
    requested = resolve_model_effort(
        harness=harness,
        cli_model=model_by_harness.get(harness),
        cli_effort=effort_by_harness.get(harness),
        request_model=None,
        request_effort=None,
        profile=concrete,
        hints=resolved.definition.harness_policy.model_hints,
    )
    return LegPlan(
        harness=harness,
        profile=concrete,
        requested=requested,
        cli_version=cli_version,
    )


def preflight(
    request: RunRequestV1,
    *,
    profile_path: Path,
    installed: Callable[[HarnessProfileV1], bool] | None = None,
    live: bool = False,
    environ: Mapping[str, str] | None = None,
    platform: str = sys.platform,
    version_reader: Callable[[HarnessProfileV1], str | None] | None = None,
) -> ResolvedRun:
    if request.overlay_refs:
        raise PreflightError("overlay_refs are reserved for M3 and must be empty in M1a")
    try:
        profile_set = load_profile_set(profile_path)
    except ProfileError as error:
        raise PreflightError(str(error)) from None
    try:
        package = load_package(Path(request.assistant))
        digest = hash_package(Path(request.assistant))
    except (PackageError, ArchiveContractError) as error:
        raise PreflightError(str(error)) from None

    installed_check = installed if installed is not None else _default_installed(profile_path)
    try:
        selection = select_harnesses(
            requested=list(request.harnesses),
            policy=package.definition.harness_policy,
            profiles=profile_set,
            installed=installed_check,
        )
    except SelectionError as error:
        raise PreflightError(str(error)) from None

    by_id = {profile.harness: profile for profile in profile_set.profiles}

    synthesis_planned = (
        request.synthesis.enabled
        if len(selection.chosen) > 1
        else "synthesis" in request.model_fields_set and request.synthesis.enabled
    )
    guarded = list(selection.chosen)
    if synthesis_planned:
        guarded.append(request.synthesis.harness)
    for harness in guarded:
        profile = by_id.get(harness)
        if profile is None:
            raise PreflightError(f"no profile for harness {harness.value}")
        if profile.kind is ProfileKind.API_TEST:
            raise PreflightError(
                f"profile {harness.value} is api-test; the M1a runner is native-only"
            )
    if synthesis_planned and not installed_check(by_id[request.synthesis.harness]):
        raise PreflightError(
            f"synthesis harness {request.synthesis.harness.value} is not installed"
        )

    current_versions: dict[HarnessId, str] = {}
    if live:
        parent = dict(os.environ if environ is None else environ)
        needs_skills = any(
            artifact.kind is ArtifactKind.AGENT_SKILL for artifact in package.definition.artifacts
        )
        live_problems: list[str] = []
        for harness in dict.fromkeys(guarded):
            raw_profile = by_id[harness]
            try:
                executable = resolve_profile_executable(profile_path, raw_profile.executable)
                config_home = resolve_config_home(profile_path, raw_profile.config_home)
            except ProfileError as error:
                raise PreflightError(str(error)) from None
            concrete = raw_profile.model_copy(
                update={"executable": str(executable), "config_home": str(config_home)}
            )
            if not config_home.is_dir():
                live_problems.append(f"{harness.value}: config home does not exist")
                continue
            try:
                build_environment(concrete, parent, platform=platform)
            except EnvironmentConflictError as error:
                live_problems.append(f"{harness.value}: {error}")
            current_version = (
                version_reader(concrete)
                if version_reader is not None
                else capture_version(concrete, parent=parent, platform=platform)
            )
            if current_version is None:
                live_problems.append(f"{harness.value}: --version failed")
            else:
                current_versions[harness] = current_version
            if (
                raw_profile.expected_version is not None
                and current_version != raw_profile.expected_version
            ):
                live_problems.append(
                    f"{harness.value}: expected version {raw_profile.expected_version!r}, "
                    f"found {current_version!r}"
                )
            live_problems.extend(
                f"{harness.value}: {problem}"
                for problem in readiness_problems(
                    raw_profile,
                    cli_version=current_version,
                    needs_skills=needs_skills,
                )
            )
        if live_problems:
            raise PreflightError(
                "live harness readiness is incomplete; run `atm profile doctor --probe`: "
                + "; ".join(live_problems)
            )

    legs = [
        _leg_plan(
            harness,
            profile=by_id[harness],
            profile_path=profile_path,
            request=request,
            resolved=package,
            cli_version=current_versions.get(harness),
        )
        for harness in selection.chosen
    ]
    synthesis_leg = (
        _leg_plan(
            request.synthesis.harness,
            profile=by_id[request.synthesis.harness],
            profile_path=profile_path,
            request=request,
            resolved=package,
            cli_version=current_versions.get(request.synthesis.harness),
        )
        if synthesis_planned
        else None
    )

    oracle_path: Path | None = None
    if request.acceptance.oracle is not None:
        oracle_path = Path(request.acceptance.oracle)
        if not oracle_path.is_file():
            raise PreflightError(f"acceptance oracle does not exist: {oracle_path}")

    timeout_seconds = min(
        request.limits.attempt_seconds or DEFAULT_TIMEOUT_SECONDS, DEFAULT_TIMEOUT_SECONDS
    )
    transient_retries = (
        request.limits.transient_retries
        if request.limits.transient_retries is not None
        else MAX_TRANSIENT_RETRIES
    )

    return ResolvedRun(
        request=request,
        profile_path=profile_path,
        profile_set=profile_set,
        package=package,
        digest=digest,
        selection=selection,
        legs=legs,
        synthesis_planned=synthesis_planned,
        synthesis_leg=synthesis_leg,
        oracle_path=oracle_path,
        timeout_seconds=timeout_seconds,
        transient_retries=transient_retries,
        live_ready=live,
    )
