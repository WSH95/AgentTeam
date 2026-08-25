"""Shared conformance plus local-only file guarantees (M1b G2)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest
from tests.coordination_suite import CoordinationProviderContract

from agentteam.coordination.local import LocalCoordinationProvider
from agentteam.coordination.protocol import (
    CoordinationError,
    CoordinationSubstrate,
    SnapshotState,
    SpaceUnavailableError,
    SubstrateTaskStatus,
)


@pytest.fixture()
def coordination_root(tmp_path: Path) -> Path:
    return tmp_path / "coordination"


@pytest.fixture()
def provider(coordination_root: Path) -> CoordinationSubstrate:
    return LocalCoordinationProvider(coordination_root)


class TestLocalCoordinationProvider(CoordinationProviderContract):
    def expected_snapshot_state(self, copy_out_verified: bool) -> SnapshotState:
        return SnapshotState.RETAINED


def test_first_space_uses_the_canonical_archive_path(coordination_root: Path) -> None:
    provider = LocalCoordinationProvider(coordination_root)
    space = provider.create_space(lead="lead")
    assert space == "space"
    assert (coordination_root / "space").is_dir()


def test_unknown_space_is_unavailable(coordination_root: Path) -> None:
    provider = LocalCoordinationProvider(coordination_root)
    with pytest.raises(SpaceUnavailableError):
        provider.members("space")


def test_member_and_snapshot_identifiers_cannot_escape_the_space(
    coordination_root: Path,
) -> None:
    provider = LocalCoordinationProvider(coordination_root)
    with pytest.raises(CoordinationError, match="member name"):
        provider.create_space(lead="../outside")
    space = provider.create_space(lead="lead")
    with pytest.raises(CoordinationError, match="member name"):
        provider.add_member(space, "../outside")
    with pytest.raises(CoordinationError, match="snapshot"):
        provider.read_snapshot(space, "../../outside")
    assert not (coordination_root.parent / "outside.json").exists()


def test_strict_local_task_transitions(coordination_root: Path) -> None:
    provider = LocalCoordinationProvider(coordination_root)
    space = provider.create_space(lead="lead")
    task_id = provider.create_task(space, "strict", blocked_by=[])
    with pytest.raises(CoordinationError, match="pending -> completed"):
        provider.update_task(space, task_id, SubstrateTaskStatus.COMPLETED, caller="lead")
    provider.update_task(space, task_id, SubstrateTaskStatus.RUNNING, caller="lead")
    with pytest.raises(CoordinationError, match="running -> pending"):
        provider.update_task(space, task_id, SubstrateTaskStatus.PENDING, caller="lead")
    provider.update_task(space, task_id, SubstrateTaskStatus.COMPLETED, caller="lead")
    with pytest.raises(CoordinationError, match="completed -> running"):
        provider.update_task(space, task_id, SubstrateTaskStatus.RUNNING, caller="lead")


def test_consumed_messages_are_retained_and_snapshot_includes_history(
    coordination_root: Path,
) -> None:
    provider = LocalCoordinationProvider(coordination_root)
    space = provider.create_space(lead="lead")
    provider.add_member(space, "reviewer")
    provider.send(space, "lead", "reviewer", "keep me")
    assert provider.receive(space, "reviewer", limit=1)
    consumed = coordination_root / space / "consumed" / "reviewer" / "m-1.json"
    assert consumed.is_file()
    snapshot_id = provider.snapshot(space, "history")
    bundle = provider.read_snapshot(space, snapshot_id)
    assert any(item["location"] == "consumed" for item in bundle["messages"])
    assert bundle["events"]


@pytest.mark.parametrize("copy_out_verified", [False, True])
def test_cleanup_tombstone_retains_every_file_and_records_the_handshake(
    coordination_root: Path, copy_out_verified: bool
) -> None:
    provider = LocalCoordinationProvider(coordination_root)
    space = provider.create_space(lead="lead")
    task_id = provider.create_task(space, "retained", blocked_by=[])
    snapshot_id = provider.snapshot(space, "retained")
    task_path = coordination_root / space / "tasks" / f"{task_id}.json"
    snapshot_path = coordination_root / space / "snapshots" / f"{snapshot_id}.json"
    outcome = provider.cleanup(space, copy_out_verified=copy_out_verified)
    assert outcome.snapshot_state is SnapshotState.RETAINED
    assert task_path.is_file() and snapshot_path.is_file()
    tombstone = json.loads((coordination_root / space / "closed").read_text(encoding="utf-8"))
    assert tombstone == {"copy_out_verified": copy_out_verified}


def test_atomic_replace_failure_keeps_old_state_and_removes_temporary_file(
    coordination_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    provider = LocalCoordinationProvider(coordination_root)
    space = provider.create_space(lead="lead")
    metadata = coordination_root / space / "metadata.json"
    before = metadata.read_bytes()
    real_replace = os.replace

    def fail_metadata(source: str | os.PathLike[str], destination: str | os.PathLike[str]) -> None:
        if Path(destination) == metadata:
            raise OSError("injected replace failure")
        real_replace(source, destination)

    monkeypatch.setattr("agentteam.coordination.local.os.replace", fail_metadata)
    with pytest.raises(OSError, match="injected"):
        provider.add_member(space, "worker")
    assert metadata.read_bytes() == before
    assert list(metadata.parent.glob(".metadata.json.*.tmp")) == []


def test_local_state_is_owner_only_on_posix(coordination_root: Path) -> None:
    provider = LocalCoordinationProvider(coordination_root)
    space = provider.create_space(lead="lead")
    provider.add_member(space, "worker")
    task_id = provider.create_task(space, "modes", blocked_by=[])
    provider.send(space, "lead", "worker", "mode message")
    provider.receive(space, "worker", limit=1)
    provider.snapshot(space, "modes")
    provider.cleanup(space, copy_out_verified=True)
    assert task_id == "t-1"
    if sys.platform == "win32":
        return
    for path in coordination_root.rglob("*"):
        expected = 0o700 if path.is_dir() else 0o600
        assert path.stat().st_mode & 0o777 == expected, path


def test_ids_and_ordering_do_not_depend_on_wall_clock(tmp_path: Path) -> None:
    observed: list[tuple[str, list[str], list[str]]] = []
    for index in range(2):
        provider = LocalCoordinationProvider(tmp_path / f"coordination-{index}")
        space = provider.create_space(lead="lead")
        tasks = [
            provider.create_task(space, f"task {number}", blocked_by=[]) for number in range(12)
        ]
        provider.send(space, "lead", "lead", "first")
        provider.send(space, "lead", "lead", "second")
        bodies = [message.body for message in provider.receive(space, "lead", limit=10)]
        observed.append((space, tasks, bodies))
    assert observed[0] == observed[1]
    assert observed[0][1][-1] == "t-12"
