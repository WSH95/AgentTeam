"""Optional ClawTeam seam qualification (plan section 10).

The whole directory skips cleanly when the `clawteam` extra is not installed
(the import guard lives in conftest.py); the core CI legs prove the skip.
Scenarios: seam contract (pin, one fixed root, owner-state refusal),
team/member lifecycle, task dependency auto-unblock, lock semantics, mailbox
send/receive, snapshot create/read/restore surviving cleanup, and two
namespaces with no API-level crossover.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from agentteam.compat.clawteam import (
    PINNED_REVISION,
    ClawTeamCompat,
    DataRootFixedError,
)


def test_info_records_the_exact_pin_and_isolation_level(seam_env: Any) -> None:
    seam = ClawTeamCompat(seam_env.data_root)
    info = seam.info()
    assert info.version == "0.3.0"
    assert info.revision == PINNED_REVISION
    assert info.isolation == "namespace"


def test_one_data_root_per_process(seam_env: Any) -> None:
    ClawTeamCompat(seam_env.data_root)
    ClawTeamCompat(seam_env.data_root)  # the same root is fine
    with pytest.raises(DataRootFixedError, match="already fixed"):
        ClawTeamCompat(seam_env.data_root.parent / "other-root")


def test_the_owners_default_state_is_refused(seam_env: Any) -> None:
    with pytest.raises(DataRootFixedError, match="clawteam"):
        ClawTeamCompat(seam_env.home / ".clawteam")
    with pytest.raises(DataRootFixedError, match="clawteam"):
        ClawTeamCompat(seam_env.home / ".clawteam" / "nested")


def test_team_and_member_lifecycle_stays_inside_the_data_root(seam_env: Any) -> None:
    seam = ClawTeamCompat(seam_env.data_root)
    space = seam.create_space(leader="atm-lead")
    assert space.startswith("atm-")
    seam.add_member(space, "atm-worker")
    members = seam.members(space)
    assert "atm-lead" in members
    assert "atm-worker" in members
    assert (seam_env.data_root / "teams" / space).is_dir()
    seam.cleanup(space)
    assert not (seam_env.data_root / "teams" / space).exists()
    assert not (seam_env.data_root / "tasks" / space).exists()
    outside = [
        path for path in seam_env.home.rglob("*") if ".clawteam" in path.parts and path.is_file()
    ]
    assert outside == [], "the seam wrote into the (patched) home"


def test_task_dependency_auto_unblock(seam_env: Any) -> None:
    seam = ClawTeamCompat(seam_env.data_root)
    space = seam.create_space(leader="atm-lead")
    blocker = seam.create_task(space, "the blocker")
    dependent = seam.create_task(space, "the dependent", blocked_by=[blocker])
    assert seam.task(space, dependent)["status"] == "blocked"
    seam.update_task(space, blocker, "in_progress", caller="atm-lead")
    seam.update_task(space, blocker, "completed", caller="atm-lead")
    after = seam.task(space, dependent)
    assert after["status"] != "blocked"
    assert blocker not in after["blocked_by"]


def test_lock_semantics_refuse_a_second_caller(seam_env: Any) -> None:
    from clawteam.store.base import TaskLockError

    seam = ClawTeamCompat(seam_env.data_root)
    space = seam.create_space(leader="atm-lead")
    task_id = seam.create_task(space, "contended work")
    seam.update_task(space, task_id, "in_progress", caller="atm-lead")
    with pytest.raises(TaskLockError):
        seam.update_task(space, task_id, "in_progress", caller="atm-rival")
    seam.update_task(space, task_id, "completed", caller="atm-lead")
    seam.update_task(space, task_id, "pending", caller="atm-rival")  # lock cleared


def test_mailbox_send_receive_consumes(seam_env: Any) -> None:
    seam = ClawTeamCompat(seam_env.data_root)
    space = seam.create_space(leader="atm-lead")
    seam.add_member(space, "atm-worker")
    seam.send(space, "atm-lead", "atm-worker", "please review the target")
    first = seam.receive(space, "atm-worker")
    assert len(first) == 1
    assert first[0]["content"] == "please review the target"
    assert seam.receive(space, "atm-worker") == []


def test_snapshot_survives_cleanup_and_restores(seam_env: Any) -> None:
    seam = ClawTeamCompat(seam_env.data_root)
    space = seam.create_space(leader="atm-lead")
    task_id = seam.create_task(space, "snapshot me")
    seam.send(space, "atm-lead", "atm-lead", "note to self")
    snapshot_id = seam.snapshot(space, "qualification")
    bundle = seam.read_snapshot(space, snapshot_id)
    assert {"config", "tasks", "events", "sessions", "costs", "inboxes"} <= set(bundle)
    seam.cleanup(space)
    assert not (seam_env.data_root / "teams" / space).exists()
    assert (seam_env.data_root / "snapshots" / space).is_dir()
    seam.restore(space, snapshot_id)
    restored = seam.tasks(space)
    assert [task["id"] for task in restored] == [task_id]


def test_two_namespaces_have_no_api_level_crossover(seam_env: Any) -> None:
    seam = ClawTeamCompat(seam_env.data_root)
    space_a = seam.create_space(leader="atm-lead")
    space_b = seam.create_space(leader="atm-lead")
    assert space_a != space_b
    task_a = seam.create_task(space_a, "only in a")
    seam.send(space_a, "atm-lead", "atm-lead", "a-mail")
    assert [task["id"] for task in seam.tasks(space_a)] == [task_a]
    assert seam.tasks(space_b) == []
    assert seam.receive(space_b, "atm-lead") == []
    received_a = seam.receive(space_a, "atm-lead")
    assert len(received_a) == 1
    assert (seam_env.data_root / "teams" / space_a).is_dir()
    assert (seam_env.data_root / "teams" / space_b).is_dir()


def test_unavailable_extra_raises_a_typed_error(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins

    from agentteam.compat import clawteam as seam_module

    real_import = builtins.__import__

    def blocked(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "clawteam":
            raise ImportError("blocked for the test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked)
    seam_module.ClawTeamCompat._reset_for_tests()
    with pytest.raises(seam_module.ClawTeamUnavailableError, match="extra"):
        seam_module.ClawTeamCompat(Path("/nonexistent-root"))
