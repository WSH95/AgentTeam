"""Resolve catalog-addressed chat targets into immutable runtime snapshots."""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import yaml

from agentteam.domain.common import HarnessId
from agentteam.domain.interactive import (
    AssistantCatalogRefV1,
    CapabilityLevel,
    CatalogKind,
    CatalogRefV1,
    DynamicMemberPolicyDisabledV1,
    InteractiveRunRequestV1,
    MemberRuntimeOverrideV1,
    TeamMemberV2,
    TeamPreferencesV2,
    TeamTemplateV2,
    WorkspaceLayout,
)
from agentteam.domain.profile import HarnessProfileV1
from agentteam.domain.team import HandoffRulesV1
from agentteam.execution.direct_acp import (
    DirectAcpError,
    DirectAcpProvider,
    build_direct_acp_qualification_target,
    installed_runtime_path,
    installed_runtime_problems,
    installed_runtime_tree_hash,
    load_direct_acp_live_attestation,
    load_direct_acp_qualification,
)
from agentteam.interactive.archive import InteractiveArchive, InteractiveArchiveError
from agentteam.interactive.controller import MemberLaunch
from agentteam.library import LibraryError, LibraryStore, default_library_root
from agentteam.resolution.archive import ArchiveContractError, hash_package
from agentteam.resolution.interactive import load_team_template_v2
from agentteam.resolution.package import LoadedPackage, PackageError, check_package, load_package
from agentteam.resolution.profiles import (
    ProfileError,
    default_profile_path,
    load_profile_set,
    resolve_profile_executable,
)
from agentteam.resolution.selection import SelectionError, select_harnesses


class InteractiveResolutionError(ValueError):
    pass


@dataclass(frozen=True)
class PreparedChat:
    request: InteractiveRunRequestV1
    team: TeamTemplateV2
    team_source: bytes
    launches: Mapping[str, MemberLaunch]
    runs_root: Path
    reservations_root: Path


def prepare_attach(
    archive: InteractiveArchive,
    *,
    environ: Mapping[str, str] | None = None,
    profile_path: Path | None = None,
    platform: str = sys.platform,
) -> PreparedChat:
    env = dict(os.environ if environ is None else environ)
    request = archive.load_request()
    team_path = archive.root / "definitions" / "team.yaml"
    try:
        loaded = load_team_template_v2(team_path)
        packages = {
            member.name: load_package(archive.root / "definitions" / "assistants" / member.name)
            for member in loaded.definition.members
        }
    except (ValueError, OSError, PackageError) as error:
        raise InteractiveResolutionError(f"invalid archived definition snapshot: {error}") from None
    launch_request = _request_for_archived_launches(archive, request, loaded.definition)
    launches = _resolve_launches(
        request=launch_request,
        team=loaded.definition,
        packages=packages,
        environ=env,
        profile_path=profile_path,
        platform=platform,
    )
    _runs_root, reservations_root = default_interactive_roots(env)
    return PreparedChat(
        request=request,
        team=loaded.definition,
        team_source=loaded.source.encode("utf-8"),
        launches=launches,
        runs_root=archive.root.parent,
        reservations_root=reservations_root,
    )


def _request_for_archived_launches(
    archive: InteractiveArchive,
    request: InteractiveRunRequestV1,
    team: TeamTemplateV2,
) -> InteractiveRunRequestV1:
    overrides = dict(request.members)
    for member in team.members:
        try:
            row = archive.load_launch_record(member.name)
            provider = row.get("provider")
            harness_value = row.get("harness")
            model = row.get("model")
            if not isinstance(provider, str) or not isinstance(harness_value, str):
                raise InteractiveResolutionError(
                    f"archived launch identity is invalid for {member.name}"
                )
            if model is not None and not isinstance(model, str):
                raise InteractiveResolutionError(
                    f"archived launch model is invalid for {member.name}"
                )
            harness = HarnessId(harness_value)
        except (InteractiveArchiveError, ValueError) as error:
            raise InteractiveResolutionError(
                f"invalid archived launch for {member.name}: {error}"
            ) from None
        existing = overrides.get(member.name, MemberRuntimeOverrideV1())
        if existing.provider is not None and existing.provider != provider:
            raise InteractiveResolutionError(
                f"archived provider conflicts with the run request for {member.name}"
            )
        if existing.harness is not None and existing.harness is not harness:
            raise InteractiveResolutionError(
                f"archived harness conflicts with the run request for {member.name}"
            )
        if existing.model is not None and existing.model != model:
            raise InteractiveResolutionError(
                f"archived model conflicts with the run request for {member.name}"
            )
        overrides[member.name] = existing.model_copy(
            update={"provider": provider, "harness": harness, "model": model}
        )
    return request.model_copy(update={"members": overrides})


def default_interactive_roots(
    environ: Mapping[str, str] | None = None,
) -> tuple[Path, Path]:
    env = os.environ if environ is None else environ
    configured = env.get("AGENTTEAM_HOME")
    home = Path(configured).expanduser() if configured else Path.home() / ".agentteam"
    return home / "runs", home / "workspace-reservations"


def prepare_assistant_chat(
    *,
    item_id: str | None,
    version: int | None,
    path: Path | None,
    workspace: Path,
    goal: str,
    done_when: list[str],
    member_override: MemberRuntimeOverrideV1 | None = None,
    environ: Mapping[str, str] | None = None,
    profile_path: Path | None = None,
    platform: str = sys.platform,
) -> PreparedChat:
    env = dict(os.environ if environ is None else environ)
    target, package = _resolve_assistant(
        item_id=item_id,
        version=version,
        path=path,
        environ=env,
        platform=platform,
    )
    member_name = "assistant"
    assistant_ref = AssistantCatalogRefV1(
        id=target.id,
        version=target.version,
        content_hash=target.content_hash,
    )
    team = TeamTemplateV2(
        schema_version=2,
        kind="team-template",
        id=_synthetic_team_id(target.id),
        version=target.version,
        summary=f"One-Member interactive Team for Assistant {target.id}.",
        members=[TeamMemberV2(name=member_name, assistant=assistant_ref)],
        lead=member_name,
        handoff=HandoffRulesV1(required_fields=[], acks=[]),
        independence=[],
        preferences=TeamPreferencesV2(),
        workflow_skeleton=[],
        workspace_layout=WorkspaceLayout.SHARED_SUPPLIED,
        dynamic_members=DynamicMemberPolicyDisabledV1(),
    )
    source = yaml.safe_dump(team.model_dump(mode="json"), sort_keys=False).encode("utf-8")
    overrides = {member_name: member_override} if member_override is not None else {}
    request = InteractiveRunRequestV1(
        schema_version=1,
        kind="interactive-run-request",
        target=target,
        workspace=str(Path(workspace).expanduser()),
        goal=goal,
        done_when=done_when,
        members=overrides,
    )
    launches = _resolve_launches(
        request=request,
        team=team,
        packages={member_name: package},
        environ=env,
        profile_path=profile_path,
        platform=platform,
    )
    runs_root, reservations_root = default_interactive_roots(env)
    return PreparedChat(request, team, source, launches, runs_root, reservations_root)


def prepare_team_chat(
    *,
    item_id: str | None,
    version: int | None,
    path: Path | None,
    workspace: Path,
    goal: str,
    done_when: list[str],
    member_overrides: Mapping[str, MemberRuntimeOverrideV1] | None = None,
    environ: Mapping[str, str] | None = None,
    profile_path: Path | None = None,
    platform: str = sys.platform,
) -> PreparedChat:
    env = dict(os.environ if environ is None else environ)
    target, team, source = _resolve_team(
        item_id=item_id,
        version=version,
        path=path,
        environ=env,
        platform=platform,
    )
    store = LibraryStore(default_library_root(env), platform=platform)
    packages = {}
    for member in team.members:
        try:
            package_path = store.resolve(
                CatalogKind.ASSISTANT,
                member.assistant.id,
                member.assistant.version,
                member.assistant.content_hash,
            )
            packages[member.name] = load_package(package_path)
        except (LibraryError, PackageError) as error:
            raise InteractiveResolutionError(
                f"cannot resolve Assistant for Member {member.name}: {error}"
            ) from None
    request = InteractiveRunRequestV1(
        schema_version=1,
        kind="interactive-run-request",
        target=target,
        workspace=str(Path(workspace).expanduser()),
        goal=goal,
        done_when=done_when,
        members=dict(member_overrides or {}),
    )
    launches = _resolve_launches(
        request=request,
        team=team,
        packages=packages,
        environ=env,
        profile_path=profile_path,
        platform=platform,
    )
    runs_root, reservations_root = default_interactive_roots(env)
    return PreparedChat(request, team, source, launches, runs_root, reservations_root)


def _resolve_assistant(
    *,
    item_id: str | None,
    version: int | None,
    path: Path | None,
    environ: Mapping[str, str],
    platform: str,
) -> tuple[CatalogRefV1, LoadedPackage]:
    if path is not None:
        if item_id is not None or version is not None:
            raise InteractiveResolutionError("--path cannot be combined with catalog id/version")
        try:
            package = load_package(path)
            problems = check_package(package, strict_content=True)
            digest = hash_package(path).package_hash
        except (PackageError, ArchiveContractError) as error:
            raise InteractiveResolutionError(str(error)) from None
        if problems:
            raise InteractiveResolutionError("invalid unmanaged Assistant: " + "; ".join(problems))
        return (
            CatalogRefV1(
                kind=CatalogKind.ASSISTANT,
                id=package.definition.id,
                version=package.definition.version,
                content_hash=digest,
            ),
            package,
        )
    if item_id is None or version is None:
        raise InteractiveResolutionError("catalog chat requires an id and --version")
    store = LibraryStore(default_library_root(environ), platform=platform)
    try:
        entry = store.get(CatalogKind.ASSISTANT, item_id, version)
        package = load_package(
            store.resolve(CatalogKind.ASSISTANT, item_id, version, entry.content_hash)
        )
    except (LibraryError, PackageError) as error:
        raise InteractiveResolutionError(str(error)) from None
    return (
        CatalogRefV1(
            kind=CatalogKind.ASSISTANT,
            id=entry.id,
            version=entry.version,
            content_hash=entry.content_hash,
        ),
        package,
    )


def _resolve_team(
    *,
    item_id: str | None,
    version: int | None,
    path: Path | None,
    environ: Mapping[str, str],
    platform: str,
) -> tuple[CatalogRefV1, TeamTemplateV2, bytes]:
    if path is not None:
        if item_id is not None or version is not None:
            raise InteractiveResolutionError("--path cannot be combined with catalog id/version")
        try:
            loaded = load_team_template_v2(path)
        except (ValueError, OSError) as error:
            raise InteractiveResolutionError(str(error)) from None
        source = loaded.source.encode("utf-8")
        digest = hashlib.sha256(source).hexdigest()
        target = CatalogRefV1(
            kind=CatalogKind.TEAM,
            id=loaded.definition.id,
            version=loaded.definition.version,
            content_hash=digest,
        )
        return target, loaded.definition, source
    if item_id is None or version is None:
        raise InteractiveResolutionError("catalog chat requires an id and --version")
    store = LibraryStore(default_library_root(environ), platform=platform)
    try:
        entry = store.get(CatalogKind.TEAM, item_id, version)
        team_path = store.resolve(CatalogKind.TEAM, item_id, version, entry.content_hash)
        loaded = load_team_template_v2(team_path)
    except (LibraryError, ValueError, OSError) as error:
        raise InteractiveResolutionError(str(error)) from None
    return (
        CatalogRefV1(
            kind=CatalogKind.TEAM,
            id=entry.id,
            version=entry.version,
            content_hash=entry.content_hash,
        ),
        loaded.definition,
        loaded.source.encode("utf-8"),
    )


def _resolve_launches(
    *,
    request: InteractiveRunRequestV1,
    team: TeamTemplateV2,
    packages: Mapping[str, LoadedPackage],
    environ: Mapping[str, str],
    profile_path: Path | None,
    platform: str,
) -> dict[str, MemberLaunch]:
    selected_profile_path = profile_path or default_profile_path(environ)
    try:
        profiles = load_profile_set(selected_profile_path)
    except ProfileError as error:
        raise InteractiveResolutionError(str(error)) from None
    runtime_path = installed_runtime_path(environ)
    runtime_problems = installed_runtime_problems(runtime_path)
    if runtime_problems:
        raise InteractiveResolutionError(
            "direct-acp runtime is not ready: "
            + "; ".join(runtime_problems)
            + " (run `atm runtime install direct-acp`)"
        )
    try:
        runtime_tree_hash = installed_runtime_tree_hash(runtime_path)
    except DirectAcpError as error:
        raise InteractiveResolutionError(f"direct-acp runtime is not ready: {error}") from None
    node = shutil.which("node", path=environ.get("PATH"))
    if node is None:
        raise InteractiveResolutionError("node is not available for direct-acp")

    by_harness = {profile.harness: profile for profile in profiles.profiles}

    def installed(profile: HarnessProfileV1) -> bool:
        try:
            candidate = resolve_profile_executable(selected_profile_path, profile.executable)
        except (AttributeError, ProfileError):
            return False
        return candidate.is_file() and (platform == "win32" or os.access(candidate, os.X_OK))

    launches: dict[str, MemberLaunch] = {}
    for member in team.members:
        package = packages[member.name]
        override = request.members.get(member.name, MemberRuntimeOverrideV1())
        if override.provider not in {None, "direct-acp"}:
            raise InteractiveResolutionError(
                f"unsupported provider override for {member.name}: {override.provider}"
            )
        if override.profile is not None:
            raise InteractiveResolutionError(
                "named profile overrides are not representable in the V1 profile set: "
                + member.name
            )
        if override.effort is not None:
            raise InteractiveResolutionError(
                f"direct-acp has not qualified an effort control for {member.name}"
            )
        try:
            selection = select_harnesses(
                requested=[] if override.harness is None else [override.harness],
                policy=package.definition.harness_policy,
                profiles=profiles,
                installed=installed,
                team_preferred=team.preferences.harness_preferences.get(member.name, []),
            )
        except (SelectionError, AttributeError) as error:
            raise InteractiveResolutionError(f"{member.name}: {error}") from None
        harness = selection.chosen[0]
        profile = by_harness[harness]
        try:
            target = build_direct_acp_qualification_target(
                profile,
                profile_path=selected_profile_path,
                runtime_path=runtime_path,
                node=node,
                environ=environ,
                platform=platform,
                runtime_tree_hash=runtime_tree_hash,
            )
            qualification, qualification_problems = load_direct_acp_qualification(
                target,
                environ=environ,
                platform=platform,
            )
        except DirectAcpError as error:
            raise InteractiveResolutionError(f"{member.name}: {error}") from None
        if qualification is None:
            raise InteractiveResolutionError(
                f"{member.name}: direct-acp is not currently qualified for {harness.value}: "
                + "; ".join(qualification_problems)
                + f" (run `atm runtime doctor direct-acp --harness {harness.value}`)"
            )
        attestation, attestation_problems = load_direct_acp_live_attestation(
            target,
            environ=environ,
            platform=platform,
        )
        if attestation is None:
            raise InteractiveResolutionError(
                f"{member.name}: direct-acp has no current live recovery attestation for "
                f"{harness.value}: "
                + "; ".join(attestation_problems)
                + (
                    " (run the attended `atm runtime qualify-live direct-acp "
                    f"--harness {harness.value}` after explicit approval)"
                )
            )
        effective_capabilities = qualification.capabilities.model_copy(
            update={
                "persistent_turns": CapabilityLevel.SUPPORTED,
                "recovery": CapabilityLevel.SUPPORTED,
            }
        )
        effective_doctor = qualification.model_copy(update={"capabilities": effective_capabilities})
        provider = DirectAcpProvider(
            runtime_path=runtime_path,
            environment=target.environment,
            node=node,
            capabilities=effective_capabilities,
            doctor_report=effective_doctor,
            platform=platform,
        )
        launches[member.name] = MemberLaunch(
            member=member.name,
            assistant=package,
            provider=provider,
            harness=harness,
            executable=target.command,
            environment=target.environment,
            config_home_variable=target.config_home_variable,
            config_home=target.config_home,
            model=override.model or profile.model_defaults.model,
        )
    return launches


def _synthetic_team_id(assistant_id: str) -> str:
    candidate = f"chat-{assistant_id}"
    return candidate[:64].rstrip("-")
