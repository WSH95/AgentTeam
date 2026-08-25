"""Workspace observation, reservation, lease, and permission-policy regressions."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from agentteam.domain.assistant import PermissionsV1
from agentteam.domain.team import WorkspaceAccess
from agentteam.execution.fakes import OwnedProcessFakeProvider
from agentteam.execution.protocol import PermissionOutcome, ProviderEvent
from agentteam.interactive.permissions import PermissionClass, decide_permission
from agentteam.interactive.workspace import (
    ControllerLease,
    ControllerLeaseError,
    WorkspaceReservation,
    WorkspaceReservationError,
    checkpoint_workspace,
)


def _git(workspace: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(workspace), *arguments],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
    )


def test_checkpoint_observes_but_does_not_mutate_a_dirty_git_tree(tmp_path: Path) -> None:
    workspace = tmp_path / "project"
    workspace.mkdir()
    _git(workspace, "init", "-q")
    _git(workspace, "config", "user.email", "tests@example.invalid")
    _git(workspace, "config", "user.name", "AgentTeam tests")
    tracked = workspace / "tracked.txt"
    tracked.write_text("committed\n", encoding="utf-8")
    _git(workspace, "add", "tracked.txt")
    _git(workspace, "commit", "-qm", "fixture")
    tracked.write_text("owner dirty bytes\n", encoding="utf-8")
    (workspace / "untracked.txt").write_text("untracked owner bytes\n", encoding="utf-8")

    head_before = _git(workspace, "rev-parse", "HEAD").stdout
    status_before = _git(
        workspace,
        "status",
        "--porcelain=v2",
        "-z",
        "--untracked-files=all",
        "--ignored=no",
    ).stdout
    checkpoint = checkpoint_workspace(workspace)
    head_after = _git(workspace, "rev-parse", "HEAD").stdout
    status_after = _git(
        workspace,
        "status",
        "--porcelain=v2",
        "-z",
        "--untracked-files=all",
        "--ignored=no",
    ).stdout

    assert checkpoint.git_head == head_before.decode("ascii").strip()
    assert head_after == head_before
    assert status_after == status_before
    assert tracked.read_text(encoding="utf-8") == "owner dirty bytes\n"
    assert (workspace / "untracked.txt").read_text(encoding="utf-8") == ("untracked owner bytes\n")


def test_reservation_is_idempotent_for_owner_and_exclusive_for_other_runs(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "project"
    workspace.mkdir()
    reservations = WorkspaceReservation(tmp_path / "reservations")
    first = reservations.acquire(workspace, "run-owner-1")
    assert reservations.acquire(workspace, "run-owner-1") == first
    with pytest.raises(WorkspaceReservationError, match="run-owner-1"):
        reservations.acquire(workspace, "run-other-2")
    reservations.release(workspace, "run-owner-1")
    assert not first.exists()


def test_reservation_partial_write_does_not_leave_a_poison_record(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "project"
    workspace.mkdir()
    reservations = WorkspaceReservation(tmp_path / "reservations")

    def fail_fsync(_descriptor: int) -> None:
        raise OSError("injected fsync failure")

    monkeypatch.setattr(os, "fsync", fail_fsync)
    with pytest.raises(OSError, match="injected fsync failure"):
        reservations.acquire(workspace, "run-owner-1")
    assert not list((tmp_path / "reservations").glob("*.json"))


def test_reservation_can_be_released_after_the_workspace_disappears(tmp_path: Path) -> None:
    workspace = tmp_path / "project"
    workspace.mkdir()
    reservations = WorkspaceReservation(tmp_path / "reservations")
    reservation = reservations.acquire(workspace, "run-owner-1")

    workspace.rmdir()
    reservations.release(workspace, "run-owner-1")

    assert not reservation.exists()


def test_controller_lease_is_exclusive_and_recoverable_after_release(tmp_path: Path) -> None:
    path = tmp_path / "run" / "controller.lock"
    first = ControllerLease(path)
    second = ControllerLease(path)
    first.acquire()
    try:
        with pytest.raises(ControllerLeaseError, match="already has a controller"):
            second.acquire()
    finally:
        first.release()
    second.acquire()
    second.release()


def test_permission_intersection_rejects_escape_symlink_network_and_unknown(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "project"
    outside = tmp_path / "outside"
    workspace.mkdir()
    outside.mkdir()
    (outside / "secret.txt").write_text("outside\n", encoding="utf-8")
    link = workspace / "escape"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are not available on this test host")

    capabilities = OwnedProcessFakeProvider().describe().capabilities
    assistant = PermissionsV1(
        filesystem="read-write-workspace",
        network="allow",
        shell="allow",
    )

    inside_read = decide_permission(
        ProviderEvent(
            event="permission-request",
            data={
                "tool_kind": "read",
                "tool_input": json.dumps({"path": "inside.txt"}),
            },
        ),
        workspace=workspace,
        assistant=assistant,
        member_access=WorkspaceAccess.READ_ONLY,
        provider=capabilities,
        attended_approval=False,
    )
    assert inside_read.classification is PermissionClass.WORKSPACE_READ
    assert inside_read.outcome is PermissionOutcome.ALLOW_ONCE

    escaped = decide_permission(
        ProviderEvent(
            event="permission-request",
            data={
                "tool_kind": "read",
                "tool_input": json.dumps({"path": "escape/secret.txt"}),
            },
        ),
        workspace=workspace,
        assistant=assistant,
        member_access=WorkspaceAccess.WORKSPACE_WRITE,
        provider=capabilities,
        attended_approval=True,
    )
    assert escaped.classification is PermissionClass.OUTSIDE_WORKSPACE
    assert escaped.outcome is PermissionOutcome.REJECT_ONCE

    for classification in ("network", "native-spawn", "unknown"):
        denied = decide_permission(
            ProviderEvent(
                event="permission-request",
                data={"classification": classification},
            ),
            workspace=workspace,
            assistant=assistant,
            member_access=WorkspaceAccess.WORKSPACE_WRITE,
            provider=capabilities,
            attended_approval=True,
        )
        assert denied.outcome is PermissionOutcome.REJECT_ONCE


def test_workspace_write_needs_all_four_ceilings(tmp_path: Path) -> None:
    workspace = tmp_path / "project"
    workspace.mkdir()
    event = ProviderEvent(
        event="permission-request",
        data={
            "classification": "workspace-write",
            "tool_input": json.dumps({"path": "result.txt"}),
        },
    )
    capabilities = OwnedProcessFakeProvider().describe().capabilities

    allowed = decide_permission(
        event,
        workspace=workspace,
        assistant=PermissionsV1(filesystem="read-write-workspace"),
        member_access=WorkspaceAccess.WORKSPACE_WRITE,
        provider=capabilities,
        attended_approval=True,
    )
    assert allowed.outcome is PermissionOutcome.ALLOW_ONCE

    for assistant, access, attended in (
        (PermissionsV1(), WorkspaceAccess.WORKSPACE_WRITE, True),
        (
            PermissionsV1(filesystem="read-write-workspace"),
            WorkspaceAccess.READ_ONLY,
            True,
        ),
        (
            PermissionsV1(filesystem="read-write-workspace"),
            WorkspaceAccess.WORKSPACE_WRITE,
            False,
        ),
    ):
        denied = decide_permission(
            event,
            workspace=workspace,
            assistant=assistant,
            member_access=access,
            provider=capabilities,
            attended_approval=attended,
        )
        assert denied.outcome is PermissionOutcome.REJECT_ONCE


def test_explicit_workspace_classification_still_requires_safe_paths(tmp_path: Path) -> None:
    workspace = tmp_path / "project"
    workspace.mkdir()
    capabilities = OwnedProcessFakeProvider().describe().capabilities
    assistant = PermissionsV1(filesystem="read-write-workspace")

    missing_path = decide_permission(
        ProviderEvent(
            event="permission-request",
            data={"classification": "workspace-write"},
        ),
        workspace=workspace,
        assistant=assistant,
        member_access=WorkspaceAccess.WORKSPACE_WRITE,
        provider=capabilities,
        attended_approval=True,
    )
    escaped = decide_permission(
        ProviderEvent(
            event="permission-request",
            data={
                "classification": "workspace-read",
                "tool_input": json.dumps({"path": "../outside.txt"}),
            },
        ),
        workspace=workspace,
        assistant=assistant,
        member_access=WorkspaceAccess.WORKSPACE_WRITE,
        provider=capabilities,
        attended_approval=True,
    )

    assert missing_path.classification is PermissionClass.UNKNOWN
    assert missing_path.outcome is PermissionOutcome.REJECT_ONCE
    assert escaped.classification is PermissionClass.OUTSIDE_WORKSPACE
    assert escaped.outcome is PermissionOutcome.REJECT_ONCE


def test_full_access_has_no_implicit_attended_run_policy_grant(tmp_path: Path) -> None:
    workspace = tmp_path / "project"
    workspace.mkdir()
    decision = decide_permission(
        ProviderEvent(
            event="permission-request",
            data={"classification": "full-access"},
        ),
        workspace=workspace,
        assistant=PermissionsV1(
            filesystem="read-write-workspace",
            network="allow",
            shell="allow",
        ),
        member_access=WorkspaceAccess.WORKSPACE_WRITE,
        provider=OwnedProcessFakeProvider().describe().capabilities,
        attended_approval=True,
    )

    assert decision.outcome is PermissionOutcome.REJECT_ONCE
    assert "run policy has no approved full-access grant" in decision.reasons


def test_workspace_checkpoint_streams_file_content_without_path_read_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "project"
    workspace.mkdir()
    (workspace / "large.bin").write_bytes(b"x" * (2 * 1024 * 1024 + 17))

    def reject_read_bytes(_path: Path) -> bytes:
        raise AssertionError("workspace hashing must stream regular files")

    monkeypatch.setattr(Path, "read_bytes", reject_read_bytes)
    checkpoint = checkpoint_workspace(workspace)
    assert len(checkpoint.tree_sha256) == 64
