"""Provider-neutral coordination seam and immutable internal DTOs (M1b section 8)."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable

from agentteam.domain.team import IndependenceAchieved, SubstrateKind


class SubstrateTaskStatus(StrEnum):
    BLOCKED = "blocked"
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"


class SnapshotState(StrEnum):
    NONE = "none"
    RETAINED = "retained"
    REMOVED = "removed"
    UNKNOWN = "unknown"


class CleanupWarningCode(StrEnum):
    UPSTREAM_CLEANUP_FAILED = "upstream-cleanup-failed"
    SNAPSHOT_DELETION_FAILED = "snapshot-deletion-failed"


@dataclass(frozen=True, slots=True)
class SubstrateTask:
    id: str
    subject: str
    status: SubstrateTaskStatus
    blocked_by: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SubstrateMessage:
    sender: str
    recipient: str
    body: str


@dataclass(frozen=True, slots=True)
class SubstrateInfo:
    kind: SubstrateKind
    version: str
    revision: str
    achieved_isolation: IndependenceAchieved


@dataclass(frozen=True, slots=True)
class CleanupOutcome:
    space_closed: bool
    snapshot_state: SnapshotState
    warning_codes: tuple[CleanupWarningCode, ...]


class CoordinationError(RuntimeError):
    """Base for provider-neutral coordination failures."""


class SpaceUnavailableError(CoordinationError):
    """A space is unknown, closed, or otherwise inoperable."""


class TaskCycleError(CoordinationError):
    """The provider-neutral skeleton contains a cycle."""


class TaskClaimError(CoordinationError):
    """A caller tried to mutate work claimed by another member."""


class UnknownTaskError(CoordinationError):
    """A task id or blocker id is not present in the space."""


class UnknownRecipientError(CoordinationError):
    """A message recipient is not in the projected roster."""


class WaitTimeoutError(CoordinationError):
    """The bounded protocol polling helper expired."""


@runtime_checkable
class CoordinationSubstrate(Protocol):
    def info(self) -> SubstrateInfo: ...

    def create_space(self, *, lead: str) -> str: ...

    def add_member(self, space: str, name: str) -> None: ...

    def members(self, space: str) -> list[str]: ...

    def cleanup(self, space: str, *, copy_out_verified: bool) -> CleanupOutcome: ...

    def create_task(self, space: str, subject: str, *, blocked_by: list[str]) -> str: ...

    def task(self, space: str, task_id: str) -> SubstrateTask: ...

    def tasks(self, space: str) -> list[SubstrateTask]: ...

    def update_task(
        self,
        space: str,
        task_id: str,
        status: SubstrateTaskStatus,
        *,
        caller: str,
    ) -> None: ...

    def send(self, space: str, sender: str, recipient: str, body: str) -> None: ...

    def receive(self, space: str, recipient: str, *, limit: int) -> list[SubstrateMessage]: ...

    def snapshot(self, space: str, tag: str) -> str: ...

    def read_snapshot(self, space: str, snapshot_id: str) -> dict[str, Any]: ...

    def restore(self, space: str, snapshot_id: str) -> dict[str, Any]: ...


TaskPredicate = Callable[[list[SubstrateTask]], bool]


def wait_for_tasks(
    substrate: CoordinationSubstrate,
    space: str,
    predicate: TaskPredicate,
    *,
    timeout_seconds: float,
    poll_interval_seconds: float = 0.05,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> list[SubstrateTask]:
    """Poll `tasks()` deterministically until `predicate` holds or time expires."""
    if timeout_seconds < 0:
        raise ValueError("timeout_seconds must be non-negative")
    if poll_interval_seconds <= 0:
        raise ValueError("poll_interval_seconds must be positive")
    deadline = clock() + timeout_seconds
    while True:
        rows = substrate.tasks(space)
        if predicate(rows):
            return rows
        remaining = deadline - clock()
        if remaining <= 0:
            raise WaitTimeoutError("coordination task wait timed out")
        sleep(min(poll_interval_seconds, remaining))
