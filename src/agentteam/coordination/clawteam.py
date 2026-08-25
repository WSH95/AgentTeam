"""Optional protocol adapter over the qualified ClawTeam compatibility seam."""

from __future__ import annotations

import re
import shutil
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from agentteam.compat.clawteam import ClawTeamCompat
from agentteam.coordination.protocol import (
    CleanupOutcome,
    CleanupWarningCode,
    CoordinationError,
    SnapshotState,
    SpaceUnavailableError,
    SubstrateInfo,
    SubstrateMessage,
    SubstrateTask,
    SubstrateTaskStatus,
    TaskClaimError,
    UnknownRecipientError,
    UnknownTaskError,
)
from agentteam.domain.team import IndependenceAchieved, SubstrateKind

_SPACE_ID = re.compile(r"^atm-[0-9a-f]{8}$")
_FROM_UPSTREAM = {
    "blocked": SubstrateTaskStatus.BLOCKED,
    "pending": SubstrateTaskStatus.PENDING,
    "in_progress": SubstrateTaskStatus.RUNNING,
    "completed": SubstrateTaskStatus.COMPLETED,
}
_TO_UPSTREAM = {
    SubstrateTaskStatus.BLOCKED: "blocked",
    SubstrateTaskStatus.PENDING: "pending",
    SubstrateTaskStatus.RUNNING: "in_progress",
    SubstrateTaskStatus.COMPLETED: "completed",
}


class ClawTeamCoordinationProvider:
    """Translate the shared coordination protocol onto one contained seam root."""

    def __init__(
        self,
        data_root: Path,
        *,
        remove_tree: Callable[[Path], None] = shutil.rmtree,
    ) -> None:
        self.data_root = Path(data_root).resolve()
        self._compat = ClawTeamCompat(self.data_root)
        self._leaders: dict[str, str] = {}
        self._task_order: dict[str, list[str]] = {}
        self._closed: set[str] = set()
        self._remove_tree = remove_tree

    def info(self) -> SubstrateInfo:
        info = self._compat.info()
        return SubstrateInfo(
            kind=SubstrateKind.CLAWTEAM,
            version=info.version,
            revision=info.revision,
            achieved_isolation=IndependenceAchieved.NAMESPACE,
        )

    # -- space lifecycle ---------------------------------------------------

    def create_space(self, *, lead: str) -> str:
        space = self._compat.create_space(leader=lead)
        if _SPACE_ID.fullmatch(space) is None:
            raise CoordinationError("the optional provider returned an unsafe namespace")
        self._leaders[space] = lead
        self._task_order[space] = []
        return space

    def add_member(self, space: str, name: str) -> None:
        self._require_open(space)
        if name not in self.members(space):
            self._compat.add_member(space, name)

    def members(self, space: str) -> list[str]:
        lead = self._require_open(space)
        upstream = self._compat.members(space)
        return [lead, *(name for name in upstream if name != lead)]

    def cleanup(self, space: str, *, copy_out_verified: bool) -> CleanupOutcome:
        self._require_open(space)
        snapshot_path = self._snapshot_path(space)
        snapshot_state = self._inspect_snapshot(snapshot_path)
        warnings: list[CleanupWarningCode] = []
        space_closed = False

        try:
            self._compat.cleanup(space)
        except Exception:
            warnings.append(CleanupWarningCode.UPSTREAM_CLEANUP_FAILED)
        else:
            self._closed.add(space)
            space_closed = True

        if copy_out_verified and snapshot_state is not SnapshotState.NONE:
            try:
                if snapshot_path.is_symlink() or not snapshot_path.is_dir():
                    raise OSError("unsafe snapshot subtree")
                self._remove_tree(snapshot_path)
            except Exception:
                warnings.append(CleanupWarningCode.SNAPSHOT_DELETION_FAILED)
                snapshot_state = self._inspect_snapshot(snapshot_path)
            else:
                snapshot_state = SnapshotState.REMOVED

        return CleanupOutcome(
            space_closed=space_closed,
            snapshot_state=snapshot_state,
            warning_codes=tuple(warnings),
        )

    # -- task store --------------------------------------------------------

    def create_task(self, space: str, subject: str, *, blocked_by: list[str]) -> str:
        self._require_open(space)
        if len(set(blocked_by)) != len(blocked_by):
            raise CoordinationError("task blockers must be unique")
        known = set(self._task_order[space])
        unknown = set(blocked_by) - known
        if unknown:
            raise UnknownTaskError("unknown blocker ids: " + ", ".join(sorted(unknown)))
        task_id = self._compat.create_task(space, subject, blocked_by=blocked_by)
        self._task_order[space].append(task_id)
        return task_id

    def task(self, space: str, task_id: str) -> SubstrateTask:
        self._require_open(space)
        try:
            row = self._compat.task(space, task_id)
        except KeyError as error:
            raise UnknownTaskError(f"unknown task id: {task_id}") from error
        return self._task_dto(row)

    def tasks(self, space: str) -> list[SubstrateTask]:
        self._require_open(space)
        rows = {str(row.get("id")): row for row in self._compat.tasks(space)}
        return [self._task_dto(rows[task_id]) for task_id in self._task_order[space]]

    def update_task(
        self,
        space: str,
        task_id: str,
        status: SubstrateTaskStatus,
        *,
        caller: str,
    ) -> None:
        self._require_open(space)
        try:
            requested = SubstrateTaskStatus(status)
        except ValueError as error:
            raise ValueError(f"unsupported protocol task status: {status!r}") from error
        try:
            self._compat.task(space, task_id)
        except KeyError as error:
            raise UnknownTaskError(f"unknown task id: {task_id}") from error
        try:
            self._compat.update_task(
                space,
                task_id,
                _TO_UPSTREAM[requested],
                caller=caller,
            )
        except Exception as error:
            error_type = type(error)
            if (
                error_type.__module__ == "clawteam.store.base"
                and error_type.__name__ == "TaskLockError"
            ):
                raise TaskClaimError(f"task {task_id} is claimed by another member") from error
            raise

    # -- mailbox -----------------------------------------------------------

    def send(self, space: str, sender: str, recipient: str, body: str) -> None:
        roster = self.members(space)
        if recipient not in roster:
            raise UnknownRecipientError(f"unknown message recipient: {recipient}")
        if sender not in roster:
            raise CoordinationError(f"unknown message sender: {sender}")
        self._compat.send(space, sender, recipient, body)

    def receive(self, space: str, recipient: str, *, limit: int) -> list[SubstrateMessage]:
        if recipient not in self.members(space):
            raise UnknownRecipientError(f"unknown message recipient: {recipient}")
        if limit < 0:
            raise ValueError("message limit must be non-negative")
        return [
            self._message_dto(row) for row in self._compat.receive(space, recipient, limit=limit)
        ]

    # -- snapshots ---------------------------------------------------------

    def snapshot(self, space: str, tag: str) -> str:
        self._require_open(space)
        return self._compat.snapshot(space, tag)

    def read_snapshot(self, space: str, snapshot_id: str) -> dict[str, Any]:
        self._require_open(space)
        return self._compat.read_snapshot(space, snapshot_id)

    def restore(self, space: str, snapshot_id: str) -> dict[str, Any]:
        self._require_open(space)
        bundle = self._compat.read_snapshot(space, snapshot_id)
        self._compat.restore(space, snapshot_id)
        return bundle

    # -- translations and guards ------------------------------------------

    def _require_open(self, space: str) -> str:
        lead = self._leaders.get(space)
        if lead is None or space in self._closed:
            raise SpaceUnavailableError(f"coordination space is unavailable: {space}")
        return lead

    def _snapshot_path(self, space: str) -> Path:
        if _SPACE_ID.fullmatch(space) is None:
            raise SpaceUnavailableError("coordination space is unavailable")
        return self.data_root / "snapshots" / space

    @staticmethod
    def _inspect_snapshot(path: Path) -> SnapshotState:
        try:
            if path.is_symlink():
                return SnapshotState.UNKNOWN
            if path.is_dir():
                return SnapshotState.RETAINED
            if path.exists():
                return SnapshotState.UNKNOWN
        except OSError:
            return SnapshotState.UNKNOWN
        return SnapshotState.NONE

    @staticmethod
    def _task_dto(row: dict[str, Any]) -> SubstrateTask:
        try:
            status = _FROM_UPSTREAM[str(row["status"])]
            blocked_by = row["blocked_by"]
            if not isinstance(blocked_by, list) or not all(
                isinstance(item, str) for item in blocked_by
            ):
                raise TypeError
            return SubstrateTask(
                id=str(row["id"]),
                subject=str(row["subject"]),
                status=status,
                blocked_by=tuple(blocked_by),
            )
        except (KeyError, TypeError) as error:
            raise CoordinationError("the optional provider returned an invalid task") from error

    @staticmethod
    def _message_dto(row: dict[str, Any]) -> SubstrateMessage:
        sender = row.get("from_agent")
        recipient = row.get("to")
        body = row.get("content")
        if (
            not isinstance(sender, str)
            or not isinstance(recipient, str)
            or not isinstance(body, str)
        ):
            raise CoordinationError("the optional provider returned an invalid message")
        return SubstrateMessage(sender=sender, recipient=recipient, body=body)


def create_provider(
    coordination_root: Path,
    *,
    environ: Mapping[str, str],
    platform: str,
) -> ClawTeamCoordinationProvider:
    """Create a process-rooted provider; the run-owned root is intentionally unused."""
    del coordination_root, platform
    configured_home = environ.get("AGENTTEAM_HOME")
    agentteam_home = Path(configured_home) if configured_home else Path.home() / ".agentteam"
    return ClawTeamCoordinationProvider(agentteam_home / "clawteam")
