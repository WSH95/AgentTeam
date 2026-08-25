"""Validation and resolution for the M1b TeamRun branch."""

from __future__ import annotations

import os
import shutil
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import ValidationError

from agentteam.coordination import ProviderDisposition, provider_disposition
from agentteam.domain.assistant import ArtifactKind
from agentteam.domain.common import HarnessId
from agentteam.domain.profile import HarnessProfileSetV1, HarnessProfileV1, ProfileKind
from agentteam.domain.request import MAX_TRANSIENT_RETRIES
from agentteam.domain.team import TeamMemberV1, TeamRunRequestV1, WorkflowTaskV1
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
from agentteam.resolution.team import (
    LoadedTeamTemplate,
    TeamTemplateError,
    check_team_request,
    check_team_template,
    hash_team_template,
    load_team_template,
)
from agentteam.run.preflight import DEFAULT_TIMEOUT_SECONDS, LegPlan, PreflightError


@dataclass(frozen=True)
class TeamMemberPlan:
    member: TeamMemberV1
    task: WorkflowTaskV1
    package: LoadedPackage
    digest: PackageDigest
    selection: SelectionOutcome
    leg: LegPlan


@dataclass(frozen=True)
class ResolvedTeamRun:
    request: TeamRunRequestV1
    request_path: Path
    template: LoadedTeamTemplate
    template_hash: str
    profile_path: Path
    profile_set: HarnessProfileSetV1
    members: list[TeamMemberPlan]
    timeout_seconds: int
    transient_retries: int
    live_ready: bool


def request_kind(path: Path) -> str | None:
    """Read only the discriminator so `atm run` can preserve direct parsing."""
    if not path.is_file():
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError):
        return None
    return str(data.get("kind")) if isinstance(data, dict) and "kind" in data else None


def load_team_request(
    request_file: Path,
    *,
    output_dir: Path | None = None,
) -> TeamRunRequestV1:
    """Load a team request and resolve every filesystem field against its file."""
    if not request_file.is_file():
        raise PreflightError(f"request file does not exist: {request_file}")
    try:
        data = yaml.safe_load(request_file.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise PreflightError(f"{request_file}: not valid YAML/JSON: {error}") from None
    if not isinstance(data, dict):
        raise PreflightError(f"{request_file}: the request must be a mapping")
    base = request_file.parent.resolve()
    for field in ("template", "workspace", "task_file", "output_dir"):
        value = data.get(field)
        if isinstance(value, str):
            path = Path(value)
            data[field] = str(path if path.is_absolute() else (base / path).resolve())
    if output_dir is not None:
        data["output_dir"] = str(output_dir.resolve())
    try:
        return TeamRunRequestV1.model_validate(data)
    except ValidationError as error:
        details = "; ".join(
            f"{'.'.join(str(loc) for loc in item['loc'])}: {item['msg']}"
            for item in error.errors(include_url=False)
        )
        raise PreflightError(f"invalid team run request: {details}") from None


def _default_installed(profile_path: Path) -> Callable[[HarnessProfileV1], bool]:
    def installed(profile: HarnessProfileV1) -> bool:
        executable = resolve_profile_executable(profile_path, profile.executable)
        return executable.is_file() or shutil.which(str(profile.executable)) is not None

    return installed


def preflight_team(
    request: TeamRunRequestV1,
    *,
    request_path: Path,
    profile_path: Path,
    installed: Callable[[HarnessProfileV1], bool] | None = None,
    live: bool = False,
    environ: Mapping[str, str] | None = None,
    platform: str = sys.platform,
    version_reader: Callable[[HarnessProfileV1], str | None] | None = None,
) -> ResolvedTeamRun:
    """Resolve a complete team without creating a run directory or provider space."""
    if request.overlay_refs:
        raise PreflightError("overlay_refs are reserved for M3 and must be empty in M1b")
    disposition = provider_disposition(request.substrate)
    if disposition is not ProviderDisposition.SUPPORTED:
        raise PreflightError(
            f"coordination substrate {request.substrate.value!r} is unavailable in M1b "
            f"(disposition: {disposition.value})"
        )
    try:
        template = load_team_template(Path(request.template))
    except TeamTemplateError as error:
        raise PreflightError(str(error)) from None
    template_problems = check_team_template(template)
    if template_problems:
        raise PreflightError("invalid team template: " + "; ".join(template_problems))
    request_problems = check_team_request(request, template.definition)
    if request_problems:
        raise PreflightError("invalid team run request: " + "; ".join(request_problems))
    workspace = Path(request.workspace)
    task_file = Path(request.task_file)
    if not workspace.is_dir() or workspace.is_symlink():
        raise PreflightError(f"workspace is not a real directory: {workspace}")
    if not task_file.is_file() or task_file.is_symlink():
        raise PreflightError(f"task file is not a regular file: {task_file}")

    try:
        profile_set = load_profile_set(profile_path)
    except ProfileError as error:
        raise PreflightError(str(error)) from None
    by_harness = {profile.harness: profile for profile in profile_set.profiles}
    installed_check = installed if installed is not None else _default_installed(profile_path)
    tasks_by_owner = {task.owner: task for task in template.definition.workflow_skeleton}
    versions: dict[tuple[str, HarnessId], str] = {}
    member_inputs: list[
        tuple[TeamMemberV1, WorkflowTaskV1, LoadedPackage, PackageDigest, SelectionOutcome]
    ] = []

    for member in template.definition.members:
        package_root = (template.path.parent / member.assistant).resolve()
        try:
            package = load_package(package_root)
            digest = hash_package(package_root)
        except (PackageError, ArchiveContractError) as error:
            raise PreflightError(f"member {member.name}: {error}") from None
        override = request.members.get(member.name)
        requested = [override.harness] if override is not None and override.harness else []
        try:
            selection = select_harnesses(
                requested=requested,
                policy=package.definition.harness_policy,
                profiles=profile_set,
                installed=installed_check,
                team_preferred=template.definition.preferences.harness_preferences.get(
                    member.name, []
                ),
            )
        except SelectionError as error:
            raise PreflightError(f"member {member.name}: {error}") from None
        harness = selection.chosen[0]
        raw_profile = by_harness.get(harness)
        if raw_profile is None:
            raise PreflightError(f"member {member.name}: no profile for harness {harness.value}")
        if raw_profile.kind is ProfileKind.API_TEST:
            raise PreflightError(
                f"member {member.name}: profile {harness.value} is api-test; "
                "the M1b runner is native-only"
            )
        if harness is HarnessId.GROK and platform == "win32":
            raise PreflightError("Grok team-member sandboxing is unsupported on Windows in M1b")
        member_inputs.append((member, tasks_by_owner[member.name], package, digest, selection))

    if live:
        parent = dict(os.environ if environ is None else environ)
        problems: list[str] = []
        for member, _task, package, _digest, selection in member_inputs:
            harness = selection.chosen[0]
            raw_profile = by_harness[harness]
            try:
                executable = resolve_profile_executable(profile_path, raw_profile.executable)
                config_home = resolve_config_home(profile_path, raw_profile.config_home)
            except ProfileError as error:
                raise PreflightError(str(error)) from None
            concrete = raw_profile.model_copy(
                update={"executable": str(executable), "config_home": str(config_home)}
            )
            if not config_home.is_dir():
                problems.append(f"{member.name}/{harness.value}: config home does not exist")
                continue
            try:
                build_environment(concrete, parent, platform=platform)
            except EnvironmentConflictError as error:
                problems.append(f"{member.name}/{harness.value}: {error}")
            version = (
                version_reader(concrete)
                if version_reader is not None
                else capture_version(concrete, parent=parent, platform=platform)
            )
            if version is None:
                problems.append(f"{member.name}/{harness.value}: --version failed")
            else:
                versions[(member.name, harness)] = version
            if raw_profile.expected_version is not None and version != raw_profile.expected_version:
                problems.append(
                    f"{member.name}/{harness.value}: expected version "
                    f"{raw_profile.expected_version!r}, found {version!r}"
                )
            needs_skills = any(
                artifact.kind is ArtifactKind.AGENT_SKILL
                for artifact in package.definition.artifacts
            )
            problems.extend(
                f"{member.name}/{harness.value}: {problem}"
                for problem in readiness_problems(
                    raw_profile,
                    cli_version=version,
                    needs_skills=needs_skills,
                )
            )
        if problems:
            raise PreflightError(
                "live harness readiness is incomplete; run `atm profile doctor --probe`: "
                + "; ".join(problems)
            )

    plans: list[TeamMemberPlan] = []
    for member, task, package, digest, selection in member_inputs:
        harness = selection.chosen[0]
        raw_profile = by_harness[harness]
        executable = resolve_profile_executable(profile_path, raw_profile.executable)
        config_home = resolve_config_home(profile_path, raw_profile.config_home)
        concrete = raw_profile.model_copy(
            update={"executable": str(executable), "config_home": str(config_home)}
        )
        override = request.members.get(member.name)
        requested_model = resolve_model_effort(
            harness=harness,
            cli_model=override.model if override is not None else None,
            cli_effort=override.effort if override is not None else None,
            request_model=None,
            request_effort=None,
            profile=concrete,
            hints=package.definition.harness_policy.model_hints,
        )
        plans.append(
            TeamMemberPlan(
                member=member,
                task=task,
                package=package,
                digest=digest,
                selection=selection,
                leg=LegPlan(
                    harness=harness,
                    profile=concrete,
                    requested=requested_model,
                    cli_version=versions.get((member.name, harness)),
                ),
            )
        )

    timeout_seconds = min(
        request.limits.attempt_seconds or DEFAULT_TIMEOUT_SECONDS,
        DEFAULT_TIMEOUT_SECONDS,
    )
    retries = (
        request.limits.transient_retries
        if request.limits.transient_retries is not None
        else MAX_TRANSIENT_RETRIES
    )
    return ResolvedTeamRun(
        request=request,
        request_path=request_path.resolve(),
        template=template,
        template_hash=hash_team_template(template),
        profile_path=profile_path,
        profile_set=profile_set,
        members=plans,
        timeout_seconds=timeout_seconds,
        transient_retries=retries,
        live_ready=live,
    )
