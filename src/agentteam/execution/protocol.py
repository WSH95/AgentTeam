"""Exactly-one-owner execution SPI for one interactive Member."""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from agentteam.domain.common import HarnessId
from agentteam.domain.interactive import (
    CleanupFact,
    CloseFactsV1,
    ProviderCapabilitiesV1,
    ProviderDoctorV1,
)


@dataclass(frozen=True)
class ProviderDescriptor:
    provider_id: str
    version: str
    capabilities: ProviderCapabilitiesV1


@dataclass(frozen=True)
class OpenMemberSpec:
    run_id: str
    member: str
    session_id: str
    generation: int
    workspace: Path
    state_dir: Path
    harness: HarnessId
    executable: tuple[str, ...]
    config_home_variable: str | None = None
    config_home: Path | None = None
    environment: Mapping[str, str] = field(default_factory=dict)
    resume_session_ref: str | None = None
    system_prompt: str | None = None
    model: str | None = None
    allowed_tools: tuple[str, ...] = ()
    max_turns: int | None = None


@dataclass(frozen=True)
class ProviderSession:
    provider_id: str
    run_id: str
    member: str
    session_id: str
    generation: int
    provider_session_ref: str
    workspace: Path
    state_dir: Path
    continuity_verified: bool
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderSuspendFacts:
    process: CleanupFact
    local_state_retained: bool


@dataclass(frozen=True)
class RetireEmptyMemberSpec:
    run_id: str
    member: str
    session_id: str
    generation: int
    provider_session_ref: str
    state_dir: Path


@dataclass(frozen=True)
class TurnSpec:
    turn_id: str
    request_id: str
    text: str
    timeout_seconds: int | None = None


@dataclass(frozen=True)
class ProviderEvent:
    event: str
    text: str | None = None
    data: Mapping[str, str] = field(default_factory=dict)


class ProviderTurnStatus(StrEnum):
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass(frozen=True)
class ProviderTurnResult:
    status: ProviderTurnStatus
    text: str | None = None
    stop_reason: str | None = None
    error: str | None = None


class CancelDisposition(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    TERMINAL = "terminal"


class PermissionOutcome(StrEnum):
    ALLOW_ONCE = "allow_once"
    ALLOW_ALWAYS = "allow_always"
    REJECT_ONCE = "reject_once"
    REJECT_ALWAYS = "reject_always"
    CANCEL = "cancel"


class ActiveTurn(Protocol):
    request_id: str

    def __aiter__(self) -> AsyncIterator[ProviderEvent]: ...

    async def result(self) -> ProviderTurnResult: ...

    async def cancel(self, reason: str) -> CancelDisposition: ...

    async def respond_permission(self, permission_id: str, outcome: PermissionOutcome) -> None: ...


class MemberExecutionProvider(Protocol):
    """One implementation owns session/process/queue/cancel/cleanup per Member."""

    def describe(self) -> ProviderDescriptor: ...

    async def doctor(self) -> ProviderDoctorV1: ...

    async def open_member(self, spec: OpenMemberSpec) -> ProviderSession: ...

    async def start_turn(self, session: ProviderSession, spec: TurnSpec) -> ActiveTurn: ...

    async def cancel_turn(self, session: ProviderSession, reason: str) -> CancelDisposition: ...

    async def verify_continuity(self, session: ProviderSession) -> bool: ...

    async def suspend_member(
        self, session: ProviderSession, reason: str
    ) -> ProviderSuspendFacts: ...

    async def retire_empty_member(self, spec: RetireEmptyMemberSpec) -> CloseFactsV1: ...

    async def close_member(self, session: ProviderSession, reason: str) -> CloseFactsV1: ...

    async def dispose_run(self, run_id: str) -> CleanupFact: ...
