"""Managed-library and V1-to-V2 CLI flows."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import cast

import pytest
from typer.testing import CliRunner

from agentteam.cli import app
from agentteam.domain.common import HarnessId
from agentteam.domain.interactive import CatalogKind
from agentteam.execution.fakes import ExternalHostFakeProvider
from agentteam.interactive.controller import MemberLaunch
from agentteam.interactive.resolution import (
    InteractiveResolutionError,
    prepare_assistant_chat,
    prepare_team_chat,
)
from agentteam.library import LibraryStore, default_library_root
from agentteam.resolution.archive import hash_package
from agentteam.resolution.package import LoadedPackage

runner = CliRunner()
REPO_ROOT = Path(__file__).resolve().parents[2]
V1_TEAM = REPO_ROOT / "examples" / "teams" / "development.yaml"
REVIEWER = REPO_ROOT / "examples" / "assistants" / "code-reviewer"
IMPLEMENTER = REPO_ROOT / "examples" / "assistants" / "implementer"


def test_cli_import_list_show_and_non_destructive_migration(tmp_path: Path) -> None:
    env = {"AGENTTEAM_HOME": str(tmp_path / "home")}
    for package in (REVIEWER, IMPLEMENTER):
        result = runner.invoke(app, ["assistant", "import", str(package), "--json"], env=env)
        assert result.exit_code == 0, result.output
        assert json.loads(result.output)["kind"] == "assistant-definition"

    listed = runner.invoke(app, ["assistant", "list", "--json"], env=env)
    assert listed.exit_code == 0, listed.output
    assert len(json.loads(listed.output)["entries"]) == 2
    shown = runner.invoke(
        app,
        ["assistant", "show", "code-reviewer", "--version", "1", "--json"],
        env=env,
    )
    assert shown.exit_code == 0, shown.output
    assert json.loads(shown.output)["id"] == "code-reviewer"

    output = tmp_path / "development.v2.yaml"
    migrated = runner.invoke(
        app,
        [
            "team",
            "migrate",
            str(V1_TEAM),
            "--to",
            "2",
            "--shared-supplied",
            "--output",
            str(output),
            "--json",
        ],
        env=env,
    )
    assert migrated.exit_code == 0, migrated.output
    assert output.is_file()
    assert json.loads(migrated.output)["workspace_layout"] == "shared-supplied"
    assert "schema_version: 1" in V1_TEAM.read_text(encoding="utf-8")

    validated = runner.invoke(app, ["team", "validate", str(output), "--json"], env=env)
    assert validated.exit_code == 0, validated.output
    assert json.loads(validated.output)["member_count"] == 3
    imported = runner.invoke(app, ["team", "import", str(output), "--json"], env=env)
    assert imported.exit_code == 0, imported.output
    assert json.loads(imported.output)["kind"] == "team-template"
    teams = runner.invoke(app, ["team", "list", "--json"], env=env)
    assert teams.exit_code == 0, teams.output
    assert len(json.loads(teams.output)["entries"]) == 1


def test_cli_team_import_is_atomic_when_reference_missing(tmp_path: Path) -> None:
    env = {"AGENTTEAM_HOME": str(tmp_path / "home")}
    migrated = tmp_path / "development.v2.yaml"
    result = runner.invoke(
        app,
        ["team", "migrate", str(V1_TEAM), "--output", str(migrated)],
        env=env,
    )
    assert result.exit_code == 0, result.output
    rejected = runner.invoke(app, ["team", "import", str(migrated)], env=env)
    assert rejected.exit_code == 2
    assert "unresolved exact Assistant references" in rejected.output
    assert not (tmp_path / "home" / "library" / "catalog.json").exists()


def test_catalog_chat_resolution_is_exact_and_assistant_chat_synthesizes_team(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    environ = {"AGENTTEAM_HOME": str(tmp_path / "home")}
    store = LibraryStore(default_library_root(environ))
    assistant_entry = store.import_assistant(IMPLEMENTER)

    def fake_launches(**kwargs: object) -> dict[str, MemberLaunch]:
        packages = cast(Mapping[str, LoadedPackage], kwargs["packages"])
        return {
            member: MemberLaunch(
                member=member,
                assistant=package,
                provider=ExternalHostFakeProvider(),
                harness=HarnessId.CODEX,
                executable=("fake",),
                environment={},
            )
            for member, package in packages.items()
        }

    monkeypatch.setattr(
        "agentteam.interactive.resolution._resolve_launches",
        fake_launches,
    )
    assistant = prepare_assistant_chat(
        item_id=assistant_entry.id,
        version=assistant_entry.version,
        path=None,
        workspace=tmp_path,
        goal="catalog Assistant goal",
        done_when=["owner reviews"],
        environ=environ,
    )
    assert assistant.request.target.kind is CatalogKind.ASSISTANT
    assert assistant.request.target.content_hash == assistant_entry.content_hash
    assert assistant.team.lead == "assistant"
    assert [member.name for member in assistant.team.members] == ["assistant"]
    assert assistant.team.members[0].assistant.content_hash == assistant_entry.content_hash

    migrated = tmp_path / "development.v2.yaml"
    result = runner.invoke(
        app,
        [
            "team",
            "migrate",
            str(V1_TEAM),
            "--to",
            "2",
            "--shared-supplied",
            "--output",
            str(migrated),
        ],
        env=environ,
    )
    assert result.exit_code == 0, result.output
    store.import_assistant(REVIEWER)
    team_entry = store.import_team(migrated)
    team = prepare_team_chat(
        item_id=team_entry.id,
        version=team_entry.version,
        path=None,
        workspace=tmp_path,
        goal="catalog Team goal",
        done_when=[],
        environ=environ,
    )
    assert team.request.target.kind is CatalogKind.TEAM
    assert team.request.target.content_hash == team_entry.content_hash
    assert set(team.launches) == {member.name for member in team.team.members}

    with pytest.raises(InteractiveResolutionError, match="cannot be combined"):
        prepare_assistant_chat(
            item_id=assistant_entry.id,
            version=assistant_entry.version,
            path=IMPLEMENTER,
            workspace=tmp_path,
            goal="invalid mixed addressing",
            done_when=[],
            environ=environ,
        )
    assert hash_package(IMPLEMENTER).package_hash == assistant_entry.content_hash
