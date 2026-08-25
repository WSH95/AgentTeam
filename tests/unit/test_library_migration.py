"""M1c immutable library and non-destructive TeamTemplate migration."""

from __future__ import annotations

import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from agentteam.domain.interactive import CatalogIndexV1, CatalogKind, WorkspaceLayout
from agentteam.library import LibraryError, LibraryStore
from agentteam.resolution.interactive import (
    load_team_template_v2,
    migrate_team_template_v1,
    write_team_migration,
)
from agentteam.resolution.team import TeamTemplateError

REPO_ROOT = Path(__file__).resolve().parents[2]
V1_TEAM = REPO_ROOT / "examples" / "teams" / "development.yaml"
REVIEWER = REPO_ROOT / "examples" / "assistants" / "code-reviewer"
IMPLEMENTER = REPO_ROOT / "examples" / "assistants" / "implementer"
NOW = datetime(2026, 8, 25, 12, 0, tzinfo=UTC)


def _store(root: Path) -> LibraryStore:
    return LibraryStore(root, clock=lambda: NOW)


def test_migration_defaults_faithfully_and_shared_is_explicit(tmp_path: Path) -> None:
    original = V1_TEAM.read_bytes()
    faithful = migrate_team_template_v1(V1_TEAM)
    assert faithful.definition.workspace_layout is WorkspaceLayout.PER_MEMBER_WORKTREE
    assert len(faithful.definition.workflow_skeleton) == 3
    assert faithful.definition.members[0].assistant.id == "code-reviewer"
    assert len(faithful.definition.members[0].assistant.content_hash) == 64
    assert "schema_version: 2" in faithful.source
    assert "workspace_layout: per-member-worktree" in faithful.source

    shared = migrate_team_template_v1(V1_TEAM, workspace_layout=WorkspaceLayout.SHARED_SUPPLIED)
    assert "workspace_layout: shared-supplied" in shared.source
    assert faithful.source != shared.source
    assert V1_TEAM.read_bytes() == original

    output = tmp_path / "development.v2.yaml"
    write_team_migration(shared, output, input_path=V1_TEAM)
    assert (
        load_team_template_v2(output).definition.workspace_layout is WorkspaceLayout.SHARED_SUPPLIED
    )
    with pytest.raises(TeamTemplateError, match="already exists"):
        write_team_migration(shared, output, input_path=V1_TEAM)
    with pytest.raises(TeamTemplateError, match="must not overwrite"):
        write_team_migration(shared, V1_TEAM, input_path=V1_TEAM)


def test_library_import_is_content_addressed_idempotent_and_exact(tmp_path: Path) -> None:
    store = _store(tmp_path / "library")
    reviewer = store.import_assistant(REVIEWER)
    implementer = store.import_assistant(IMPLEMENTER)
    assert reviewer.kind is CatalogKind.ASSISTANT
    assert store.import_assistant(REVIEWER) == reviewer

    migrated = migrate_team_template_v1(V1_TEAM, workspace_layout=WorkspaceLayout.SHARED_SUPPLIED)
    team_file = tmp_path / "development.v2.yaml"
    write_team_migration(migrated, team_file, input_path=V1_TEAM)
    team = store.import_team(team_file)
    assert team.kind is CatalogKind.TEAM
    assert store.import_team(team_file) == team
    assert store.resolve(
        CatalogKind.ASSISTANT,
        reviewer.id,
        reviewer.version,
        reviewer.content_hash,
    ).is_dir()
    assert store.resolve(CatalogKind.TEAM, team.id, team.version, team.content_hash).is_file()

    index = CatalogIndexV1.model_validate_json((store.root / "catalog.json").read_bytes())
    assert index.generation == 3
    assert len(index.entries) == 3
    assert implementer.active


def test_team_reference_resolution_is_all_or_nothing(tmp_path: Path) -> None:
    store = _store(tmp_path / "library")
    store.import_assistant(REVIEWER)
    migrated = migrate_team_template_v1(V1_TEAM)
    team_file = tmp_path / "development.v2.yaml"
    write_team_migration(migrated, team_file, input_path=V1_TEAM)

    before = (store.root / "catalog.json").read_bytes()
    with pytest.raises(LibraryError, match="unresolved exact Assistant references"):
        store.import_team(team_file)
    assert (store.root / "catalog.json").read_bytes() == before
    assert not (store.root / "objects" / "team-template").exists()


def test_coordinate_collision_refuses_before_publication(tmp_path: Path) -> None:
    store = _store(tmp_path / "library")
    original = store.import_assistant(REVIEWER)
    changed = tmp_path / "changed-reviewer"
    shutil.copytree(REVIEWER, changed)
    persona = changed / "persona.md"
    persona.write_text(persona.read_text(encoding="utf-8") + "\nBe concise.\n", encoding="utf-8")

    with pytest.raises(LibraryError, match="immutable catalog collision"):
        store.import_assistant(changed)
    entries = store.entries(kind=CatalogKind.ASSISTANT)
    assert entries == [original]


def test_tampered_catalog_object_is_rejected_by_resolve_reimport_and_team_import(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path / "library")
    reviewer = store.import_assistant(REVIEWER)
    store.import_assistant(IMPLEMENTER)
    object_root = store.root / reviewer.object_path
    persona = object_root / "persona.md"
    persona.write_text(persona.read_text(encoding="utf-8") + "\ntampered\n", encoding="utf-8")

    with pytest.raises(LibraryError, match="identity mismatch"):
        store.resolve(
            CatalogKind.ASSISTANT,
            reviewer.id,
            reviewer.version,
            reviewer.content_hash,
        )
    with pytest.raises(LibraryError, match="identity mismatch"):
        store.import_assistant(REVIEWER)

    migrated = migrate_team_template_v1(V1_TEAM)
    team_file = tmp_path / "development.v2.yaml"
    write_team_migration(migrated, team_file, input_path=V1_TEAM)
    with pytest.raises(LibraryError, match="identity mismatch"):
        store.import_team(team_file)


def test_import_rehashes_the_copied_staging_tree_before_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = _store(tmp_path / "library")
    original_secure = store._secure_tree

    def secure_then_mutate(staging: Path) -> None:
        original_secure(staging)
        persona = staging / "persona.md"
        persona.write_text(
            persona.read_text(encoding="utf-8") + "\nraced mutation\n",
            encoding="utf-8",
        )

    monkeypatch.setattr(store, "_secure_tree", secure_then_mutate)
    with pytest.raises(LibraryError, match="identity mismatch"):
        store.import_assistant(REVIEWER)
    assert not store.index_path.exists()
    assert not list((store.root / "objects" / "assistant-definition").glob("*"))


@pytest.mark.skipif(sys.platform == "win32", reason="fcntl is POSIX-only")
def test_library_lock_closes_descriptor_when_acquisition_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import fcntl
    import os

    observed: list[int] = []

    def fail_lock(fd: int, _operation: int) -> None:
        observed.append(fd)
        raise OSError("injected lock failure")

    monkeypatch.setattr(fcntl, "flock", fail_lock)
    with pytest.raises(LibraryError, match="cannot acquire library lock"):
        _store(tmp_path / "library").entries()
    assert observed
    with pytest.raises(OSError):
        os.fstat(observed[0])
