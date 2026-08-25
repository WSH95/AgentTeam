"""TeamTemplate loading, content hashing, and transitive reference validation."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import ValidationError

from agentteam.domain.team import TeamRunRequestV1, TeamTemplateV1, validate_request_members
from agentteam.resolution.archive import ArchiveContractError, hash_package
from agentteam.resolution.package import (
    PackageError,
    check_package,
    check_prohibited_text,
    load_package,
)


class TeamTemplateError(ValueError):
    """A TeamTemplate cannot be loaded under the portable V1 contract."""


@dataclass(frozen=True)
class LoadedTeamTemplate:
    definition: TeamTemplateV1
    path: Path
    source: str


def _read_template(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise TeamTemplateError(f"team template is not a regular file: {path}")
    try:
        raw = path.read_bytes()
        source = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise TeamTemplateError(f"{path.name}: not valid UTF-8 ({error})") from None
    if "\x00" in source:
        raise TeamTemplateError(f"{path.name}: binary content is outside V1")
    return source.replace("\r\n", "\n").replace("\r", "\n")


def load_team_template(path: Path) -> LoadedTeamTemplate:
    path = Path(path)
    source = _read_template(path)
    try:
        data = yaml.safe_load(source)
    except yaml.YAMLError as error:
        raise TeamTemplateError(f"{path.name}: not valid YAML/JSON: {error}") from None
    try:
        definition = TeamTemplateV1.model_validate(data)
    except ValidationError as error:
        details = "; ".join(
            f"{'.'.join(str(loc) for loc in item['loc'])}: {item['msg']}"
            for item in error.errors(include_url=False)
        )
        raise TeamTemplateError(f"{path.name}: {details}") from None
    return LoadedTeamTemplate(definition=definition, path=path, source=source)


def hash_team_template(loaded: LoadedTeamTemplate) -> str:
    """Hash normalized UTF-8 bytes, matching the portable file-content discipline."""
    return hashlib.sha256(loaded.source.encode("utf-8")).hexdigest()


def check_team_template(loaded: LoadedTeamTemplate) -> list[str]:
    """Validate prohibited content and every referenced Assistant package."""
    problems = check_prohibited_text(loaded.path.name, loaded.source)
    for member in loaded.definition.members:
        ref = Path(member.assistant)
        if ref.is_absolute():
            problems.append(f"members.{member.name}.assistant: absolute path is not portable")
            continue
        package_root = loaded.path.parent / ref
        try:
            package = load_package(package_root)
            hash_package(package_root)
        except (PackageError, ArchiveContractError) as error:
            problems.append(f"members.{member.name}.assistant: {error}")
            continue
        for problem in check_package(package, strict_content=True):
            problems.append(f"members.{member.name}.assistant: {problem}")
    return problems


def check_team_request(request: TeamRunRequestV1, template: TeamTemplateV1) -> list[str]:
    """Cross-record checks that require the referenced template roster."""
    try:
        validate_request_members(request, template)
    except ValueError as error:
        return [str(error)]
    return []
