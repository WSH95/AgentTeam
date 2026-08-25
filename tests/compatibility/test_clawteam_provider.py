"""Shared conformance and provider-specific translations for the optional adapter."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import pytest
from tests.coordination_suite import CoordinationProviderContract

from agentteam.compat.clawteam import PINNED_REVISION
from agentteam.coordination import create_provider
from agentteam.coordination.clawteam import ClawTeamCoordinationProvider
from agentteam.coordination.protocol import (
    CleanupOutcome,
    CleanupWarningCode,
    CoordinationSubstrate,
    SnapshotState,
    SubstrateMessage,
    SubstrateTaskStatus,
    TaskClaimError,
    UnknownTaskError,
)
from agentteam.domain.team import IndependenceAchieved, SubstrateKind


@pytest.fixture()
def provider(seam_env: Any) -> CoordinationSubstrate:
    return ClawTeamCoordinationProvider(seam_env.data_root)


class TestClawTeamCoordinationProvider(CoordinationProviderContract):
    def expected_snapshot_state(self, copy_out_verified: bool) -> SnapshotState:
        return SnapshotState.REMOVED if copy_out_verified else SnapshotState.RETAINED


def test_info_and_namespace_record_the_qualified_identity(seam_env: Any) -> None:
    provider = ClawTeamCoordinationProvider(seam_env.data_root)
    assert provider.info().kind is SubstrateKind.CLAWTEAM
    assert provider.info().revision == PINNED_REVISION
    assert provider.info().achieved_isolation is IndependenceAchieved.NAMESPACE
    space = provider.create_space(lead="logical-lead")
    assert re.fullmatch(r"atm-[0-9a-f]{8}", space)
    assert provider.members(space) == ["logical-lead"]


def test_registry_uses_one_stable_agentteam_home_root(seam_env: Any, tmp_path: Path) -> None:
    agentteam_home = seam_env.home / "agentteam-home"
    provider = create_provider(
        SubstrateKind.CLAWTEAM,
        tmp_path / "run-a" / "coordination",
        environ={"AGENTTEAM_HOME": str(agentteam_home)},
        platform=sys.platform,
    )
    assert isinstance(provider, ClawTeamCoordinationProvider)
    assert provider.data_root == (agentteam_home / "clawteam").resolve()


def test_status_mapping_and_error_causes_are_explicit(seam_env: Any) -> None:
    provider = ClawTeamCoordinationProvider(seam_env.data_root)
    space = provider.create_space(lead="lead")
    provider.add_member(space, "worker")
    task_id = provider.create_task(space, "mapped", blocked_by=[])
    provider.update_task(space, task_id, SubstrateTaskStatus.RUNNING, caller="lead")

    task_file = next((seam_env.data_root / "tasks" / space).glob("task-*.json"))
    raw = json.loads(task_file.read_text(encoding="utf-8"))
    assert raw["status"] == "in_progress"
    assert provider.task(space, task_id).status is SubstrateTaskStatus.RUNNING

    with pytest.raises(TaskClaimError) as claim:
        provider.update_task(space, task_id, SubstrateTaskStatus.RUNNING, caller="worker")
    assert type(claim.value.__cause__).__name__ == "TaskLockError"
    with pytest.raises(UnknownTaskError) as unknown:
        provider.task(space, "missing")
    assert isinstance(unknown.value.__cause__, KeyError)


def test_message_content_and_roster_reconciliation_are_protocol_shaped(
    seam_env: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = ClawTeamCoordinationProvider(seam_env.data_root)
    space = provider.create_space(lead="lead")
    provider.add_member(space, "worker")
    provider.send(space, "lead", "worker", "mapped body")
    assert provider.receive(space, "worker", limit=1) == [
        SubstrateMessage(sender="lead", recipient="worker", body="mapped body")
    ]

    upstream_members = provider._compat.members
    monkeypatch.setattr(
        provider._compat,
        "members",
        lambda selected: [name for name in upstream_members(selected) if name != "lead"],
    )
    assert provider.members(space) == ["lead", "worker"]


def test_verified_cleanup_removes_only_the_selected_snapshot_subtree(seam_env: Any) -> None:
    provider = ClawTeamCoordinationProvider(seam_env.data_root)
    selected = provider.create_space(lead="selected")
    neighbor = provider.create_space(lead="neighbor")
    provider.snapshot(selected, "selected")
    provider.snapshot(neighbor, "neighbor")

    outcome = provider.cleanup(selected, copy_out_verified=True)
    assert outcome == CleanupOutcome(
        space_closed=True,
        snapshot_state=SnapshotState.REMOVED,
        warning_codes=(),
    )
    assert not (seam_env.data_root / "snapshots" / selected).exists()
    assert (seam_env.data_root / "snapshots" / neighbor).is_dir()
    assert provider.members(neighbor) == ["neighbor"]


def test_cleanup_attempts_snapshot_deletion_after_upstream_failure(
    seam_env: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = ClawTeamCoordinationProvider(seam_env.data_root)
    space = provider.create_space(lead="lead")
    provider.snapshot(space, "evidence")

    def fail_cleanup(_space: str) -> None:
        raise OSError("injected upstream failure")

    monkeypatch.setattr(provider._compat, "cleanup", fail_cleanup)
    outcome = provider.cleanup(space, copy_out_verified=True)
    assert outcome == CleanupOutcome(
        space_closed=False,
        snapshot_state=SnapshotState.REMOVED,
        warning_codes=(CleanupWarningCode.UPSTREAM_CLEANUP_FAILED,),
    )
    assert not (seam_env.data_root / "snapshots" / space).exists()
    assert "injected" not in repr(outcome)


def test_snapshot_deletion_failure_is_path_free_and_retains_evidence(seam_env: Any) -> None:
    def fail_remove(_path: Path) -> None:
        raise RuntimeError("owner path must not escape")

    provider = ClawTeamCoordinationProvider(seam_env.data_root, remove_tree=fail_remove)
    space = provider.create_space(lead="lead")
    provider.snapshot(space, "evidence")
    outcome = provider.cleanup(space, copy_out_verified=True)
    assert outcome == CleanupOutcome(
        space_closed=True,
        snapshot_state=SnapshotState.RETAINED,
        warning_codes=(CleanupWarningCode.SNAPSHOT_DELETION_FAILED,),
    )
    assert (seam_env.data_root / "snapshots" / space).is_dir()
    assert str(seam_env.data_root) not in repr(outcome)
