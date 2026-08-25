"""TeamTemplateV2 loading and non-destructive V1 migration."""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import ValidationError

from agentteam.domain.interactive import (
    AssistantCatalogRefV1,
    DynamicMemberPolicyDisabledV1,
    TeamMemberV2,
    TeamPreferencesV2,
    TeamTemplateV2,
    WorkspaceLayout,
)
from agentteam.resolution.archive import ArchiveContractError, hash_package
from agentteam.resolution.package import PackageError, load_package
from agentteam.resolution.team import LoadedTeamTemplate, TeamTemplateError, load_team_template


@dataclass(frozen=True)
class LoadedTeamTemplateV2:
    definition: TeamTemplateV2
    path: Path
    source: str


@dataclass(frozen=True)
class TeamMigrationResult:
    definition: TeamTemplateV2
    source: str
    diff: str


def _read_source(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise TeamTemplateError(f"team template is not a regular file: {path}")
    try:
        source = path.read_bytes().decode("utf-8")
    except UnicodeDecodeError as error:
        raise TeamTemplateError(f"{path.name}: not valid UTF-8 ({error})") from None
    if "\x00" in source:
        raise TeamTemplateError(f"{path.name}: binary content is outside the archive contract")
    return source.replace("\r\n", "\n").replace("\r", "\n")


def load_team_template_v2(path: Path) -> LoadedTeamTemplateV2:
    path = Path(path)
    source = _read_source(path)
    try:
        data = yaml.safe_load(source)
    except yaml.YAMLError as error:
        raise TeamTemplateError(f"{path.name}: not valid YAML/JSON: {error}") from None
    try:
        definition = TeamTemplateV2.model_validate(data)
    except ValidationError as error:
        details = "; ".join(
            f"{'.'.join(str(loc) for loc in item['loc'])}: {item['msg']}"
            for item in error.errors(include_url=False)
        )
        raise TeamTemplateError(f"{path.name}: {details}") from None
    return LoadedTeamTemplateV2(definition=definition, path=path, source=source)


def migrate_team_template_v1(
    path: Path,
    *,
    workspace_layout: WorkspaceLayout = WorkspaceLayout.PER_MEMBER_WORKTREE,
) -> TeamMigrationResult:
    """Resolve every V1 Assistant path and produce a V2 candidate in memory."""
    loaded: LoadedTeamTemplate = load_team_template(path)
    source_root = loaded.path.parent
    members: list[TeamMemberV2] = []
    for member in loaded.definition.members:
        package_root = source_root / member.assistant
        try:
            package = load_package(package_root)
            digest = hash_package(package_root)
        except (PackageError, ArchiveContractError) as error:
            raise TeamTemplateError(f"members.{member.name}.assistant: {error}") from None
        members.append(
            TeamMemberV2(
                name=member.name,
                assistant=AssistantCatalogRefV1(
                    id=package.definition.id,
                    version=package.definition.version,
                    content_hash=digest.package_hash,
                ),
                relationships=member.relationships,
                visibility=member.visibility,
            )
        )

    definition = TeamTemplateV2(
        schema_version=2,
        kind="team-template",
        id=loaded.definition.id,
        version=loaded.definition.version,
        summary=loaded.definition.summary,
        members=members,
        lead=loaded.definition.lead,
        handoff=loaded.definition.handoff,
        independence=loaded.definition.independence,
        preferences=TeamPreferencesV2(
            harness_preferences=loaded.definition.preferences.harness_preferences
        ),
        workflow_skeleton=loaded.definition.workflow_skeleton,
        workspace_layout=workspace_layout,
        dynamic_members=DynamicMemberPolicyDisabledV1(),
        constraints=loaded.definition.constraints,
    )
    rendered = yaml.safe_dump(
        definition.model_dump(mode="json", exclude_defaults=False),
        sort_keys=False,
        allow_unicode=True,
    )
    diff = "".join(
        difflib.unified_diff(
            loaded.source.splitlines(keepends=True),
            rendered.splitlines(keepends=True),
            fromfile=str(loaded.path),
            tofile=f"{loaded.path} (schema v2 candidate)",
        )
    )
    return TeamMigrationResult(definition=definition, source=rendered, diff=diff)


def write_team_migration(result: TeamMigrationResult, output: Path, *, input_path: Path) -> None:
    """Write only a new candidate; never replace input or an existing output."""
    output = Path(output)
    input_resolved = Path(input_path).resolve()
    if output.resolve() == input_resolved:
        raise TeamTemplateError("migration output must not overwrite the V1 input")
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(result.source)
    except FileExistsError:
        raise TeamTemplateError(f"migration output already exists: {output}") from None
