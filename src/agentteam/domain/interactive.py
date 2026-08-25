"""Portable contracts for interactive TeamRuns (M1c r2).

These records deliberately use a distinct ``interactive-run-record`` kind.
The V1 direct/batch ``run-record`` union remains unchanged.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import AwareDatetime, Field, model_validator

from agentteam.domain.common import (
    HarnessId,
    NonNegativeInt,
    PositiveInt,
    RecordModel,
    RelPath,
    RunId,
    SchemaVersion,
    SchemaVersionV2,
    Sha256,
    Slug,
)
from agentteam.domain.request import EvidenceSettingsV1, LimitsV1
from agentteam.domain.team import (
    HandoffRulesV1,
    IndependenceDeclared,
    IndependenceRuleV1,
    TeamTaskStatus,
    WorkflowTaskV1,
    WorkspaceAccess,
)


class CatalogKind(StrEnum):
    ASSISTANT = "assistant-definition"
    TEAM = "team-template"


class CatalogRefV1(RecordModel):
    kind: CatalogKind
    id: Slug
    version: PositiveInt
    content_hash: Sha256


class AssistantCatalogRefV1(RecordModel):
    id: Slug
    version: PositiveInt
    content_hash: Sha256


class WorkspaceLayout(StrEnum):
    SHARED_SUPPLIED = "shared-supplied"
    PER_MEMBER_WORKTREE = "per-member-worktree"


class TeamMemberV2(RecordModel):
    name: Slug
    assistant: AssistantCatalogRefV1
    relationships: dict[Slug, list[Slug]] = Field(default_factory=dict)
    visibility: Literal["visible"] = "visible"

    @model_validator(mode="after")
    def _unique_relationship_targets(self) -> TeamMemberV2:
        for relation, targets in self.relationships.items():
            if len(set(targets)) != len(targets):
                raise ValueError(f"relationship {relation!r} targets must be unique")
        return self


class TeamRunDefaultsV2(RecordModel):
    fresh_instances: Literal[True] = True
    archive: Literal["always"] = "always"


class TeamPreferencesV2(RecordModel):
    harness_preferences: dict[Slug, list[HarnessId]] = Field(default_factory=dict)
    run_defaults: TeamRunDefaultsV2 = Field(default_factory=TeamRunDefaultsV2)

    @model_validator(mode="after")
    def _unique_harness_preferences(self) -> TeamPreferencesV2:
        for member, harnesses in self.harness_preferences.items():
            if len(set(harnesses)) != len(harnesses):
                raise ValueError(f"harness_preferences.{member} must be unique")
        return self


class DynamicMemberPolicyDisabledV1(RecordModel):
    """Closed M1c carrier. M1d activates policy in a later contract."""

    enabled: Literal[False] = False


class TeamTemplateV2(RecordModel):
    schema_version: SchemaVersionV2
    kind: Literal["team-template"]
    id: Slug
    version: PositiveInt
    summary: str = Field(min_length=1)
    members: list[TeamMemberV2] = Field(min_length=1)
    lead: Slug
    handoff: HandoffRulesV1
    independence: list[IndependenceRuleV1]
    preferences: TeamPreferencesV2
    workflow_skeleton: list[WorkflowTaskV1] = Field(default_factory=list)
    workspace_layout: WorkspaceLayout = WorkspaceLayout.PER_MEMBER_WORKTREE
    dynamic_members: DynamicMemberPolicyDisabledV1 = Field(
        default_factory=DynamicMemberPolicyDisabledV1
    )
    constraints: list[str] = Field(
        default_factory=list,
        max_length=0,
        description="Reserved pending HB-03; must remain empty.",
    )

    @model_validator(mode="after")
    def _consistent_composition(self) -> TeamTemplateV2:
        names = [member.name for member in self.members]
        roster = set(names)
        if len(names) != len(roster):
            raise ValueError("member names must be unique")
        if "synthesis" in roster:
            raise ValueError("member name 'synthesis' is reserved")
        if self.lead not in roster:
            raise ValueError("lead must name a member in the roster")

        for member in self.members:
            for relation, targets in member.relationships.items():
                unknown = set(targets) - roster
                if unknown:
                    raise ValueError(
                        f"relationship {member.name}.{relation} names unknown members: "
                        + ", ".join(sorted(unknown))
                    )
        unknown_preferences = set(self.preferences.harness_preferences) - roster
        if unknown_preferences:
            raise ValueError(
                "harness_preferences names unknown members: "
                + ", ".join(sorted(unknown_preferences))
            )

        pairs: set[frozenset[str]] = set()
        for rule in self.independence:
            if rule.declared is IndependenceDeclared.MECHANICAL:
                raise ValueError("mechanical independence is not enforceable in M1c")
            unknown = set(rule.between) - roster
            if unknown:
                raise ValueError(
                    "independence pair names unknown members: " + ", ".join(sorted(unknown))
                )
            pair = frozenset(rule.between)
            if pair in pairs:
                raise ValueError("independence pairs must be unique")
            pairs.add(pair)

        tasks = {task.id: task for task in self.workflow_skeleton}
        if len(tasks) != len(self.workflow_skeleton):
            raise ValueError("workflow task ids must be unique")
        for task in self.workflow_skeleton:
            if task.owner not in roster:
                raise ValueError(f"workflow task {task.id!r} names unknown owner {task.owner!r}")
            unknown = set(task.blocked_by) - set(tasks)
            if unknown:
                raise ValueError(
                    f"task {task.id!r} has unknown blockers: " + ", ".join(sorted(unknown))
                )
            if task.id in task.blocked_by:
                raise ValueError(f"task {task.id!r} cannot block itself")

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(task_id: str) -> None:
            if task_id in visiting:
                raise ValueError("workflow_skeleton must be acyclic")
            if task_id in visited:
                return
            visiting.add(task_id)
            for blocker in tasks[task_id].blocked_by:
                visit(blocker)
            visiting.remove(task_id)
            visited.add(task_id)

        for task_id in tasks:
            visit(task_id)
        return self


class MemberRuntimeOverrideV1(RecordModel):
    provider: Slug | None = None
    harness: HarnessId | None = None
    profile: str | None = Field(default=None, min_length=1)
    model: str | None = Field(default=None, min_length=1)
    effort: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def _qualified_values(self) -> MemberRuntimeOverrideV1:
        if (self.model is not None or self.effort is not None) and self.harness is None:
            raise ValueError("model or effort requires a harness override")
        return self


class InteractiveRunRequestV1(RecordModel):
    schema_version: SchemaVersion
    kind: Literal["interactive-run-request"]
    target: CatalogRefV1
    workspace: str = Field(min_length=1)
    workspace_layout: Literal["shared-supplied"] = "shared-supplied"
    goal: str = Field(min_length=1, max_length=2000)
    done_when: list[str] = Field(default_factory=list)
    members: dict[Slug, MemberRuntimeOverrideV1] = Field(default_factory=dict)
    output_dir: str | None = None
    evidence: EvidenceSettingsV1 = Field(default_factory=EvidenceSettingsV1)
    limits: LimitsV1 = Field(default_factory=LimitsV1)

    @model_validator(mode="after")
    def _content(self) -> InteractiveRunRequestV1:
        if not self.goal.strip():
            raise ValueError("goal must be non-empty")
        if any(not item.strip() for item in self.done_when):
            raise ValueError("done_when entries must be non-empty")
        return self


class InteractiveRunPhase(StrEnum):
    INITIALIZING = "initializing"
    OPEN = "open"
    COMPLETION_PENDING = "completion-pending"
    INTERRUPTED = "interrupted"
    RECOVERY_REQUIRED = "recovery-required"
    CLOSING = "closing"
    CLOSE_FAILED = "close-failed"
    CLOSED = "closed"


class InteractiveRunOutcome(StrEnum):
    SUCCEEDED = "succeeded"
    CANCELLED = "cancelled"
    FAILED = "failed"
    TIMED_OUT = "timed-out"
    ABANDONED = "abandoned"


class SessionStatus(StrEnum):
    OPENING = "opening"
    OPEN = "open"
    TURN_RUNNING = "turn-running"
    CONTINUITY_UNVERIFIED = "continuity-unverified"
    CLOSING = "closing"
    CLOSED = "closed"
    CLOSE_FAILED = "close-failed"


class TurnStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CleanupFact(StrEnum):
    CONFIRMED = "confirmed"
    NOT_APPLICABLE = "not-applicable"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"
    FAILED = "failed"


class CloseFactsV1(RecordModel):
    logical_session: CleanupFact
    process: CleanupFact
    local_state: CleanupFact
    provider_history: CleanupFact


class WorkspaceCheckpointV1(RecordModel):
    canonical_path: str = Field(min_length=1)
    git_head: str | None = Field(default=None, min_length=1)
    git_status_sha256: Sha256
    tree_sha256: Sha256
    observed_at: AwareDatetime


class InteractiveMemberRecordV1(RecordModel):
    name: Slug
    assistant: AssistantCatalogRefV1
    origin: Literal["persistent", "synthetic"]
    visibility: Literal["visible", "hidden"]
    session_id: Slug


class InteractiveRunRecordV1(RecordModel):
    schema_version: SchemaVersion
    kind: Literal["interactive-run-record"]
    run_id: RunId
    target: CatalogRefV1
    goal: str = Field(min_length=1)
    done_when: list[str]
    workspace: str = Field(min_length=1)
    workspace_layout: Literal["shared-supplied"]
    phase: InteractiveRunPhase
    outcome: InteractiveRunOutcome | None = None
    members: list[InteractiveMemberRecordV1] = Field(min_length=1)
    work_items: list[Slug]
    sessions: list[Slug] = Field(min_length=1)
    turns: list[Slug]
    completion_proposals: list[Slug]
    workspace_reservation: RelPath
    events: RelPath
    initial_checkpoint: WorkspaceCheckpointV1
    final_checkpoint: WorkspaceCheckpointV1 | None = None
    cleanup: CloseFactsV1 | None = None
    created_at: AwareDatetime
    updated_at: AwareDatetime
    failure_reason: str | None = None

    @model_validator(mode="after")
    def _lifecycle(self) -> InteractiveRunRecordV1:
        if len(set(self.sessions)) != len(self.sessions):
            raise ValueError("session ids must be unique")
        if len({member.name for member in self.members}) != len(self.members):
            raise ValueError("member names must be unique")
        if len({member.session_id for member in self.members}) != len(self.members):
            raise ValueError("member session ids must be unique")
        if {member.session_id for member in self.members} != set(self.sessions):
            raise ValueError("members and sessions must reference the same session ids")
        if self.phase is InteractiveRunPhase.CLOSED:
            if self.outcome is None or self.cleanup is None or self.final_checkpoint is None:
                raise ValueError("closed run requires outcome, cleanup, and final checkpoint")
            required = (
                self.cleanup.logical_session,
                self.cleanup.process,
                self.cleanup.local_state,
            )
            if any(
                fact not in {CleanupFact.CONFIRMED, CleanupFact.NOT_APPLICABLE} for fact in required
            ):
                raise ValueError("closed run requires terminal required cleanup facts")
        elif self.phase is InteractiveRunPhase.CLOSE_FAILED:
            if (
                self.outcome is not None
                or self.cleanup is None
                or self.final_checkpoint is None
                or not self.failure_reason
                or not self.failure_reason.strip()
            ):
                raise ValueError(
                    "close-failed run requires no outcome plus cleanup, final checkpoint, "
                    "and failure reason"
                )
        elif self.outcome is not None:
            raise ValueError("outcome is set only when phase is closed")
        return self


class MemberSessionV1(RecordModel):
    schema_version: SchemaVersion
    kind: Literal["member-session"]
    run_id: RunId
    session_id: Slug
    member: Slug
    generation: PositiveInt
    provider: Slug
    provider_session_ref: str = Field(min_length=1)
    status: SessionStatus
    continuity_verified: bool
    opened_at: AwareDatetime
    closed_at: AwareDatetime | None = None
    close: CloseFactsV1 | None = None

    @model_validator(mode="after")
    def _closed_has_facts(self) -> MemberSessionV1:
        terminal = self.status in {SessionStatus.CLOSED, SessionStatus.CLOSE_FAILED}
        if terminal and (self.closed_at is None or self.close is None):
            raise ValueError("terminal session requires closed_at and close facts")
        if not terminal and (self.closed_at is not None or self.close is not None):
            raise ValueError("nonterminal session cannot carry close facts")
        return self


class TurnRecordV1(RecordModel):
    schema_version: SchemaVersion
    kind: Literal["turn-record"]
    run_id: RunId
    turn_id: Slug
    member: Slug
    session_id: Slug
    generation: PositiveInt
    prompt_sha256: Sha256
    status: TurnStatus
    events: RelPath
    queued_at: AwareDatetime
    started_at: AwareDatetime | None = None
    finished_at: AwareDatetime | None = None
    result_sha256: Sha256 | None = None
    failure_reason: str | None = None

    @model_validator(mode="after")
    def _terminal_finished(self) -> TurnRecordV1:
        if self.status in {TurnStatus.COMPLETED, TurnStatus.FAILED, TurnStatus.CANCELLED} and (
            self.finished_at is None or self.result_sha256 is None
        ):
            raise ValueError("terminal turn requires finished_at and result_sha256")
        return self


class WorkItemV1(RecordModel):
    schema_version: SchemaVersion
    kind: Literal["work-item"]
    run_id: RunId
    id: Slug
    subject: str = Field(min_length=1)
    owner: Slug
    status: TeamTaskStatus
    blocked_by: list[Slug] = Field(default_factory=list)
    workspace_access: WorkspaceAccess = WorkspaceAccess.READ_ONLY
    result_ref: Slug | None = None

    @model_validator(mode="after")
    def _shape(self) -> WorkItemV1:
        if not self.subject.strip():
            raise ValueError("work item subject must be non-empty")
        if len(set(self.blocked_by)) != len(self.blocked_by):
            raise ValueError("blocked_by references must be unique")
        if self.id in self.blocked_by:
            raise ValueError("work item cannot block itself")
        return self


class ControlAction(StrEnum):
    WORK_CREATE = "work.create"
    WORK_UPDATE = "work.update"
    WORK_ASSIGN = "work.assign"
    COMPLETION_PROPOSE = "completion.propose"


class ControlActor(StrEnum):
    USER = "user"
    LEAD = "lead"
    MEMBER = "member"


class ControlRequestV1(RecordModel):
    schema_version: SchemaVersion
    kind: Literal["control-request"]
    request_id: Slug
    run_id: RunId
    source_turn_id: Slug | None = None
    actor: ControlActor
    actor_member: Slug | None = None
    action: ControlAction
    work_item: WorkItemV1 | None = None
    work_item_id: Slug | None = None
    status: TeamTaskStatus | None = None
    owner: Slug | None = None
    completion_proposal: Slug | None = None

    @model_validator(mode="after")
    def _action_payload(self) -> ControlRequestV1:
        allowed: dict[ControlAction, tuple[str, ...]] = {
            ControlAction.WORK_CREATE: ("work_item",),
            ControlAction.WORK_UPDATE: ("work_item_id", "status"),
            ControlAction.WORK_ASSIGN: ("work_item_id", "owner"),
            ControlAction.COMPLETION_PROPOSE: ("completion_proposal",),
        }
        present = {
            name
            for name in ("work_item", "work_item_id", "status", "owner", "completion_proposal")
            if getattr(self, name) is not None
        }
        expected = set(allowed[self.action])
        if present != expected:
            raise ValueError(
                f"control action {self.action.value!r} requires exactly: "
                + ", ".join(sorted(expected))
            )
        if self.actor is ControlActor.USER and self.actor_member is not None:
            raise ValueError("user control request cannot set actor_member")
        if self.actor is not ControlActor.USER and self.actor_member is None:
            raise ValueError("member/lead control request requires actor_member")
        return self


class ReceiptStatus(StrEnum):
    QUEUED = "queued"
    APPLIED = "applied"
    DENIED = "denied"
    FAILED = "failed"


class ControlReceiptV1(RecordModel):
    schema_version: SchemaVersion
    kind: Literal["control-receipt"]
    request_id: Slug
    run_id: RunId
    status: ReceiptStatus
    queued_at: AwareDatetime
    committed_source_sequence: NonNegativeInt | None = None
    applied_at: AwareDatetime | None = None
    reason: str | None = None

    @model_validator(mode="after")
    def _terminal_receipt(self) -> ControlReceiptV1:
        if self.status is not ReceiptStatus.QUEUED and self.applied_at is None:
            raise ValueError("terminal control receipt requires applied_at")
        return self


class CompletionProposalStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class CompletionCriterionV1(RecordModel):
    criterion: str = Field(min_length=1)
    evidence: list[str] = Field(default_factory=list)


class CompletionProposalV1(RecordModel):
    schema_version: SchemaVersion
    kind: Literal["completion-proposal"]
    run_id: RunId
    proposal_id: Slug
    proposed_by: Slug
    source_turn_id: Slug
    summary: str = Field(min_length=1)
    criteria: list[CompletionCriterionV1]
    work_items: list[Slug]
    status: CompletionProposalStatus = CompletionProposalStatus.PENDING
    proposed_at: AwareDatetime
    decided_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def _decision_time(self) -> CompletionProposalV1:
        if self.status is CompletionProposalStatus.PENDING and self.decided_at is not None:
            raise ValueError("pending proposal cannot have decided_at")
        if self.status is not CompletionProposalStatus.PENDING and self.decided_at is None:
            raise ValueError("decided proposal requires decided_at")
        return self


RunEventValue = str | int | bool | None


class RunEventV1(RecordModel):
    schema_version: SchemaVersion
    kind: Literal["run-event"]
    run_id: RunId
    sequence: NonNegativeInt
    event: Slug
    occurred_at: AwareDatetime
    correlation_id: Slug | None = None
    data: dict[str, RunEventValue] = Field(default_factory=dict)


class CapabilityLevel(StrEnum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"


class ProviderCapabilitiesV1(RecordModel):
    schema_version: SchemaVersion
    kind: Literal["provider-capabilities"]
    provider: Slug
    version: str = Field(min_length=1)
    persistent_turns: CapabilityLevel
    recovery: CapabilityLevel
    permission_events: CapabilityLevel
    workspace_enforcement: CapabilityLevel
    tool_filtering: CapabilityLevel
    native_spawn_control: CapabilityLevel
    process_stop_observability: CapabilityLevel
    local_state_deletion: CapabilityLevel
    provider_history_deletion: CapabilityLevel


class DoctorCheckV1(RecordModel):
    name: Slug
    status: Literal["pass", "fail", "unsupported"]
    detail: str | None = None


class ProviderDoctorV1(RecordModel):
    schema_version: SchemaVersion
    kind: Literal["provider-doctor"]
    provider: Slug
    checked_at: AwareDatetime
    status: Literal["pass", "fail", "unsupported"]
    capabilities: ProviderCapabilitiesV1
    checks: list[DoctorCheckV1]
    model_calls: Literal[0] = 0


class CatalogEntryV1(RecordModel):
    kind: CatalogKind
    id: Slug
    version: PositiveInt
    content_hash: Sha256
    object_path: RelPath
    active: bool = True


class CatalogIndexV1(RecordModel):
    schema_version: SchemaVersion
    kind: Literal["catalog-index"]
    generation: NonNegativeInt
    entries: list[CatalogEntryV1]
    updated_at: AwareDatetime

    @model_validator(mode="after")
    def _unique_coordinates(self) -> CatalogIndexV1:
        coordinates = [(entry.kind, entry.id, entry.version) for entry in self.entries]
        if len(set(coordinates)) != len(coordinates):
            raise ValueError("catalog coordinates must be unique")
        return self
