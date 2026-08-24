"""Archive records: `RunRecordV1`, `HarnessInvocationV1`, `EnsembleRecordV1`.

Plan section 7. `RunRecordV1` (`run.json`) is the one-Member subset of the
later TeamRun record: its single Member is bound to exactly one execution — a
`HarnessInvocationV1` (solo mode) or an `EnsembleRecordV1` (legs plus
synthesis). `HarnessInvocationV1` is the invocation ledger entry; cost is never
fabricated and Codex remains `cost_source: unavailable`.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import AwareDatetime, Field, model_validator

from agentteam.domain.bundle import AssistantRefV1
from agentteam.domain.common import (
    TERMINAL_STATUSES,
    EnsembleId,
    HarnessId,
    InvocationId,
    NonNegativeInt,
    RecordModel,
    RelPath,
    RunId,
    RunStatus,
    SchemaVersion,
    Sha256,
    Slug,
)

# --- run record ----------------------------------------------------------------


class ExecutionKind(StrEnum):
    INVOCATION = "invocation"
    ENSEMBLE = "ensemble"


class ExecutionBindingV1(RecordModel):
    """A Member is bound to one execution at a time (TEM section 4, M1a r3)."""

    kind: ExecutionKind
    ref: str = Field(min_length=1, description="The invocation id or ensemble id.")

    @model_validator(mode="after")
    def _ref_matches_kind(self) -> ExecutionBindingV1:
        expected = "inv-" if self.kind is ExecutionKind.INVOCATION else "ens-"
        if not self.ref.startswith(expected):
            raise ValueError(f"execution ref {self.ref!r} does not match kind {self.kind.value!r}")
        return self


class TimingV1(RecordModel):
    started_at: AwareDatetime
    finished_at: AwareDatetime | None = None
    duration_ms: NonNegativeInt | None = None


class MemberRecordV1(RecordModel):
    name: Slug
    assistant: AssistantRefV1
    effective_definition_hash: Sha256
    execution: ExecutionBindingV1


class RunRecordV1(RecordModel):
    """The archive manifest (`run.json`); written `pending` before any side effect.

    `effective_definition_hash` lives on the Member (the one-Member subset of
    the later TeamRun record; M1b members each carry their own).
    """

    schema_version: SchemaVersion
    kind: Literal["run-record"]
    run_id: RunId
    mode: Literal["direct"]
    member: MemberRecordV1
    timing: TimingV1
    status: RunStatus
    failure_reason: str | None = None

    @model_validator(mode="after")
    def _terminal_is_finished(self) -> RunRecordV1:
        if self.status in TERMINAL_STATUSES and self.timing.finished_at is None:
            raise ValueError(f"terminal status {self.status.value!r} requires timing.finished_at")
        return self


# --- harness invocation --------------------------------------------------------


class DecidedBy(StrEnum):
    """Who decided the harness; `team` and forced variants are reserved for M1b."""

    USER = "user"
    ASSISTANT = "assistant"
    DEFAULT = "default"


class SelectionV1(RecordModel):
    decided_by: DecidedBy
    candidates: list[HarnessId] = Field(default_factory=list)


class RequestedV1(RecordModel):
    harness: HarnessId
    version: str | None = None
    model: str | None = None
    effort: str | None = None


class ObservedV1(RecordModel):
    harness: HarnessId | None = None
    version: str | None = None
    model: str | None = None
    effort: str | None = None


class RenderedPartV1(RecordModel):
    """Which channel carried one definition part (persona, principles, skill:<name>, ...)."""

    part: str = Field(min_length=1)
    channel: str = Field(min_length=1)


class DegradedPartV1(RecordModel):
    """An optional part that could not be delivered; required parts fail before launch."""

    part: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class InjectionV1(RecordModel):
    render: list[RenderedPartV1] = Field(default_factory=list)
    degraded: list[DegradedPartV1] = Field(default_factory=list)
    undeliverable_required_parts: list[DegradedPartV1] = Field(
        default_factory=list,
        description="Required parts that could not be delivered; render fails before launch.",
    )


class TargetHashesV1(RecordModel):
    """AgentTeam-computed hashes of the leg workspace; detect target mutation."""

    before: Sha256
    after: Sha256 | None = None


class LauncherPolicy(StrEnum):
    """Branch of the plan section 9 launcher policy that was taken."""

    POSIX_DIRECT = "posix-direct"
    NATIVE_EXE = "native-exe"
    PYTHON_SCRIPT = "python-script"
    RESOLVED_CMD_SHIM = "resolved-cmd-shim"
    ALLOWLISTED_CMD = "allowlisted-cmd"
    REFUSED = "refused"


class CommandV1(RecordModel):
    """Redacted argv (typed placeholders, never raw paths or content)."""

    argv_redacted: list[str] = Field(min_length=1)
    launcher: str = Field(
        min_length=1, description="Resolved launcher, as a placeholder or basename."
    )
    launcher_policy: LauncherPolicy
    cwd: str = Field(min_length=1, description="Placeholder for the working directory.")


class EnvironmentV1(RecordModel):
    """Environment names and policy outcomes only — never values."""

    names: list[str] = Field(default_factory=list)
    config_home_variable: str = Field(min_length=1)
    conflicts_detected: list[str] = Field(default_factory=list)


class PlaceholderV1(RecordModel):
    """Typed path placeholder used in argv/env records (e.g. <WORKSPACE>)."""

    token: str = Field(min_length=1)
    role: str = Field(min_length=1)


class Attendance(StrEnum):
    ATTENDED = "attended"
    UNATTENDED = "unattended"


class InvocationAuthMode(StrEnum):
    NATIVE_SUBSCRIPTION = "native-subscription"


class ArtifactRefV1(RecordModel):
    role: str = Field(
        min_length=1, description="stdout, stderr, rendered-prompt, normalized-review, ..."
    )
    path: RelPath = Field(description="Relative to the run archive.")
    sha256: Sha256


class CostSource(StrEnum):
    VENDOR = "vendor"
    UNAVAILABLE = "unavailable"


class UsageV1(RecordModel):
    """Vendor-reported usage; telemetry, never subscription billing."""

    input_tokens: NonNegativeInt | None = None
    output_tokens: NonNegativeInt | None = None
    cost_amount: float | None = None
    cost_currency: str | None = None
    cost_source: CostSource = CostSource.UNAVAILABLE

    @model_validator(mode="after")
    def _no_fabricated_cost(self) -> UsageV1:
        if self.cost_source is CostSource.UNAVAILABLE and self.cost_amount is not None:
            raise ValueError("cost_amount requires cost_source=vendor")
        if self.cost_amount is not None and self.cost_currency is None:
            raise ValueError("cost_amount requires cost_currency")
        return self


class RetryClassification(StrEnum):
    NONE = "none"
    TRANSIENT = "transient"
    PERMANENT = "permanent"


class RetryV1(RecordModel):
    """Attempt identity is (invocation_id, attempt); section 9 allows one retry."""

    classification: RetryClassification = RetryClassification.NONE
    attempt: Annotated[int, Field(ge=1, le=2)] = 1
    max_attempts: Annotated[int, Field(ge=1, le=2)] = 2


class ExitV1(RecordModel):
    code: int | None = None
    signal: str | None = None


class SchemaOutcome(StrEnum):
    VALID = "valid"
    INVALID = "invalid"
    MISSING = "missing"
    NOT_REQUESTED = "not-requested"


class HarnessInvocationV1(RecordModel):
    """One execution of one harness for one Member/task — the ledger entry."""

    schema_version: SchemaVersion
    kind: Literal["harness-invocation"]
    invocation_id: InvocationId
    run_id: RunId
    ensemble_id: EnsembleId | None = None
    requested: RequestedV1
    observed: ObservedV1 = Field(default_factory=ObservedV1)
    selection: SelectionV1
    effective_definition_hash: Sha256
    target: TargetHashesV1
    injection: InjectionV1 = Field(default_factory=InjectionV1)
    command: CommandV1
    environment: EnvironmentV1
    placeholders: list[PlaceholderV1] = Field(default_factory=list)
    attendance: Attendance
    auth_mode: InvocationAuthMode
    timing: TimingV1
    artifacts: list[ArtifactRefV1] = Field(default_factory=list)
    usage: UsageV1 = Field(default_factory=UsageV1)
    retry: RetryV1 = Field(default_factory=RetryV1)
    exit: ExitV1 = Field(default_factory=ExitV1)
    schema_outcome: SchemaOutcome = SchemaOutcome.NOT_REQUESTED
    problems: list[str] = Field(
        default_factory=list,
        description="Parser and vendor-telemetry problems retained for evidence fidelity.",
    )
    status: RunStatus

    @model_validator(mode="after")
    def _terminal_is_finished(self) -> HarnessInvocationV1:
        if self.status in TERMINAL_STATUSES and self.timing.finished_at is None:
            raise ValueError(f"terminal status {self.status.value!r} requires timing.finished_at")
        return self


# --- ensemble record -----------------------------------------------------------


class SynthesisLinkV1(RecordModel):
    invocation_id: InvocationId | None = None
    inputs: list[InvocationId] = Field(default_factory=list)
    instruction_hash: Sha256 = Field(
        description=(
            "SHA-256 of the committed synthesis instruction "
            "(src/agentteam/synthesis/instructions.md)."
        )
    )


class AttributionV1(RecordModel):
    """Links a merged finding to the leg findings it came from."""

    merged_finding_id: str = Field(min_length=1)
    sources: list[str] = Field(
        default_factory=list, description="<invocation_id>:<finding_id> references."
    )


class ConditionResultV1(RecordModel):
    id: str = Field(min_length=1)
    passed: bool | None = None
    detail: str | None = None


class AcceptanceResultV1(RecordModel):
    passed: bool | None = None
    conditions: list[ConditionResultV1] = Field(default_factory=list)


class AcceptanceV1(RecordModel):
    """Mechanical (architecture gate) and semantic (product-useful gate) results, kept apart."""

    mechanical: AcceptanceResultV1 = Field(default_factory=AcceptanceResultV1)
    semantic: AcceptanceResultV1 = Field(default_factory=AcceptanceResultV1)


class EnsembleRecordV1(RecordModel):
    schema_version: SchemaVersion
    kind: Literal["ensemble-record"]
    ensemble_id: EnsembleId
    run_id: RunId
    legs: list[InvocationId] = Field(min_length=1)
    synthesis: SynthesisLinkV1
    attribution: list[AttributionV1] = Field(default_factory=list)
    status: RunStatus
    acceptance: AcceptanceV1 = Field(default_factory=AcceptanceV1)

    @model_validator(mode="after")
    def _unique_legs(self) -> EnsembleRecordV1:
        if len(set(self.legs)) != len(self.legs):
            raise ValueError("legs must be unique")
        return self
