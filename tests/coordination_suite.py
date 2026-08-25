"""Shared CoordinationSubstrate conformance base; imported by provider suites."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any, cast

import pytest

from agentteam.coordination.protocol import (
    CleanupOutcome,
    CoordinationSubstrate,
    SnapshotState,
    SpaceUnavailableError,
    SubstrateInfo,
    SubstrateMessage,
    SubstrateTask,
    SubstrateTaskStatus,
    TaskClaimError,
    UnknownRecipientError,
    UnknownTaskError,
    WaitTimeoutError,
    wait_for_tasks,
)
from agentteam.domain.team import IndependenceAchieved, SubstrateKind


class CoordinationProviderContract:
    """Provider-neutral scenarios; concrete test classes supply `provider`."""

    def expected_snapshot_state(self, copy_out_verified: bool) -> SnapshotState:
        raise NotImplementedError

    def test_info_identity(self, provider: CoordinationSubstrate) -> None:
        info = provider.info()
        assert isinstance(info, SubstrateInfo)
        assert info.kind in set(SubstrateKind)
        assert info.version
        assert info.revision
        assert info.achieved_isolation in set(IndependenceAchieved)

    def test_space_lifecycle_records_lead_and_full_roster(
        self, provider: CoordinationSubstrate
    ) -> None:
        space = provider.create_space(lead="lead")
        assert provider.members(space) == ["lead"]
        provider.add_member(space, "implementer")
        provider.add_member(space, "reviewer")
        provider.add_member(space, "reviewer")
        assert provider.members(space) == ["lead", "implementer", "reviewer"]

    def test_task_dtos_remaining_blockers_auto_unblock_and_claims(
        self, provider: CoordinationSubstrate
    ) -> None:
        space = provider.create_space(lead="lead")
        provider.add_member(space, "worker")
        blocker = provider.create_task(space, "plan", blocked_by=[])
        dependent = provider.create_task(space, "implement", blocked_by=[blocker])
        assert provider.task(space, blocker) == SubstrateTask(
            id=blocker,
            subject="plan",
            status=SubstrateTaskStatus.PENDING,
            blocked_by=(),
        )
        assert provider.task(space, dependent).blocked_by == (blocker,)
        assert provider.task(space, dependent).status is SubstrateTaskStatus.BLOCKED
        assert [task.id for task in provider.tasks(space)] == [blocker, dependent]

        provider.update_task(space, blocker, SubstrateTaskStatus.RUNNING, caller="lead")
        with pytest.raises(TaskClaimError):
            provider.update_task(space, blocker, SubstrateTaskStatus.RUNNING, caller="worker")
        provider.update_task(space, blocker, SubstrateTaskStatus.COMPLETED, caller="lead")
        unblocked = provider.task(space, dependent)
        assert unblocked.status is SubstrateTaskStatus.PENDING
        assert unblocked.blocked_by == ()

        with pytest.raises((FrozenInstanceError, AttributeError)):
            cast(Any, unblocked).status = SubstrateTaskStatus.COMPLETED

    def test_unknown_task_referents_and_non_protocol_status_fail(
        self, provider: CoordinationSubstrate
    ) -> None:
        space = provider.create_space(lead="lead")
        with pytest.raises(UnknownTaskError):
            provider.create_task(space, "bad", blocked_by=["t-404"])
        with pytest.raises(UnknownTaskError):
            provider.task(space, "t-404")
        with pytest.raises(UnknownTaskError):
            provider.update_task(space, "t-404", SubstrateTaskStatus.RUNNING, caller="lead")
        task_id = provider.create_task(space, "valid", blocked_by=[])
        with pytest.raises(ValueError):
            provider.update_task(space, task_id, cast(Any, "failed"), caller="lead")

    def test_mailbox_claims_once_in_deterministic_order(
        self, provider: CoordinationSubstrate
    ) -> None:
        space = provider.create_space(lead="lead")
        provider.add_member(space, "reviewer")
        provider.send(space, "lead", "reviewer", "first")
        provider.send(space, "lead", "reviewer", "second")
        assert provider.receive(space, "reviewer", limit=1) == [
            SubstrateMessage(sender="lead", recipient="reviewer", body="first")
        ]
        assert provider.receive(space, "reviewer", limit=10) == [
            SubstrateMessage(sender="lead", recipient="reviewer", body="second")
        ]
        assert provider.receive(space, "reviewer", limit=10) == []
        with pytest.raises(UnknownRecipientError):
            provider.send(space, "lead", "outsider", "no")
        with pytest.raises(UnknownRecipientError):
            provider.receive(space, "outsider", limit=1)

    def test_snapshot_read_restore_round_trip(self, provider: CoordinationSubstrate) -> None:
        space = provider.create_space(lead="lead")
        provider.add_member(space, "reviewer")
        task_id = provider.create_task(space, "snapshot task", blocked_by=[])
        provider.send(space, "lead", "reviewer", "snapshot message")
        snapshot_id = provider.snapshot(space, "round-trip")
        bundle = provider.read_snapshot(space, snapshot_id)
        assert isinstance(bundle, dict)

        provider.update_task(space, task_id, SubstrateTaskStatus.RUNNING, caller="lead")
        provider.update_task(space, task_id, SubstrateTaskStatus.COMPLETED, caller="lead")
        assert provider.receive(space, "reviewer", limit=1)
        provider.add_member(space, "later")

        restored = provider.restore(space, snapshot_id)
        assert restored == bundle
        assert provider.task(space, task_id).status is SubstrateTaskStatus.PENDING
        assert provider.members(space) == ["lead", "reviewer"]
        assert provider.receive(space, "reviewer", limit=1) == [
            SubstrateMessage(sender="lead", recipient="reviewer", body="snapshot message")
        ]

    @pytest.mark.parametrize("copy_out_verified", [False, True])
    def test_cleanup_shapes_inoperability_and_archive_copy_survival(
        self,
        provider: CoordinationSubstrate,
        tmp_path: Path,
        copy_out_verified: bool,
    ) -> None:
        space = provider.create_space(lead="lead")
        task_id = provider.create_task(space, "archive me", blocked_by=[])
        snapshot_id = provider.snapshot(space, "final")
        bundle = provider.read_snapshot(space, snapshot_id)
        archive_copy = tmp_path / f"archive-copy-{copy_out_verified}.json"
        archive_copy.write_text(json.dumps(bundle, sort_keys=True), encoding="utf-8")

        outcome = provider.cleanup(space, copy_out_verified=copy_out_verified)
        assert outcome == CleanupOutcome(
            space_closed=True,
            snapshot_state=self.expected_snapshot_state(copy_out_verified),
            warning_codes=(),
        )
        assert str(tmp_path) not in repr(outcome)
        assert json.loads(archive_copy.read_text(encoding="utf-8")) == bundle

        operations: list[Callable[[], object]] = [
            lambda: provider.members(space),
            lambda: provider.tasks(space),
            lambda: provider.task(space, task_id),
            lambda: provider.add_member(space, "later"),
            lambda: provider.create_task(space, "later", blocked_by=[]),
            lambda: provider.send(space, "lead", "lead", "later"),
            lambda: provider.receive(space, "lead", limit=1),
            lambda: provider.snapshot(space, "later"),
            lambda: provider.read_snapshot(space, snapshot_id),
            lambda: provider.restore(space, snapshot_id),
            lambda: provider.cleanup(space, copy_out_verified=True),
        ]
        for operation in operations:
            with pytest.raises(SpaceUnavailableError):
                operation()

    def test_cleanup_without_snapshot_reports_none(self, provider: CoordinationSubstrate) -> None:
        space = provider.create_space(lead="lead")
        assert provider.cleanup(space, copy_out_verified=False) == CleanupOutcome(
            space_closed=True,
            snapshot_state=SnapshotState.NONE,
            warning_codes=(),
        )

    def test_two_spaces_have_no_task_or_message_crossover(
        self, provider: CoordinationSubstrate
    ) -> None:
        first = provider.create_space(lead="first")
        second = provider.create_space(lead="second")
        first_task = provider.create_task(first, "first-only", blocked_by=[])
        second_task = provider.create_task(second, "second-only", blocked_by=[])
        provider.send(first, "first", "first", "first-message")
        assert [task.id for task in provider.tasks(first)] == [first_task]
        assert [task.id for task in provider.tasks(second)] == [second_task]
        assert provider.receive(second, "second", limit=10) == []
        assert provider.receive(first, "first", limit=10)[0].body == "first-message"

    def test_protocol_wait_helper_is_bounded_and_injected_clock_deterministic(
        self, provider: CoordinationSubstrate
    ) -> None:
        space = provider.create_space(lead="lead")
        task_id = provider.create_task(space, "wait", blocked_by=[])
        ready = wait_for_tasks(
            provider,
            space,
            lambda tasks: tasks[0].status is SubstrateTaskStatus.PENDING,
            timeout_seconds=0,
        )
        assert ready[0].id == task_id

        current = [0.0]
        sleeps: list[float] = []

        def clock() -> float:
            return current[0]

        def sleep(duration: float) -> None:
            sleeps.append(duration)
            current[0] += duration

        with pytest.raises(WaitTimeoutError, match="timed out"):
            wait_for_tasks(
                provider,
                space,
                lambda _tasks: False,
                timeout_seconds=0.25,
                poll_interval_seconds=0.1,
                clock=clock,
                sleep=sleep,
            )
        assert sleeps == pytest.approx([0.1, 0.1, 0.05])
