"""Portable Team templates, team-run requests, and member results (M1b section 6)."""

from __future__ import annotations

from collections import Counter
from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from agentteam.domain.common import (
    HarnessId,
    PositiveInt,
    RecordModel,
    RelPath,
    SchemaVersion,
    Slug,
)
from agentteam.domain.request import EvidenceSettingsV1, LimitsV1


class SubstrateKind(StrEnum):
    """Coordination provider selected for one team run."""

    LOCAL = "local"
    CLAWTEAM = "clawteam"


class WorkspaceAccess(StrEnum):
    READ_ONLY = "read-only"
    WORKSPACE_WRITE = "workspace-write"


class HandoffField(StrEnum):
    TASK_ID = "task_id"
    SUMMARY = "summary"
    DELIVERABLES = "deliverables"
    RISKS = "risks"
    DONE_WHEN = "done_when"


class HandoffAck(StrEnum):
    ACK = "ACK"
    DONE = "DONE"
    BLOCKED = "BLOCKED"


class IndependenceDeclared(StrEnum):
    ADVISORY = "advisory"
    MECHANICAL = "mechanical"


class IndependenceAchieved(StrEnum):
    NAMESPACE = "namespace"
    DATA_DIR = "data-dir"
    MECHANICAL = "mechanical"


class TeamTaskStatus(StrEnum):
    BLOCKED = "blocked"
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ABANDONED = "abandoned"


class TeamMemberV1(RecordModel):
    name: Slug
    assistant: str = Field(min_length=1, description="Path to an Assistant package.")
    relationships: dict[Slug, list[Slug]] = Field(default_factory=dict)
    visibility: Literal["visible"] = "visible"

    @model_validator(mode="after")
    def _unique_relationship_targets(self) -> TeamMemberV1:
        for relation, targets in self.relationships.items():
            if len(set(targets)) != len(targets):
                raise ValueError(f"relationship {relation!r} targets must be unique")
        return self


class HandoffRulesV1(RecordModel):
    required_fields: list[HandoffField]
    acks: list[HandoffAck]

    @model_validator(mode="after")
    def _unique_vocabulary(self) -> HandoffRulesV1:
        if len(set(self.required_fields)) != len(self.required_fields):
            raise ValueError("handoff required_fields must be unique")
        if len(set(self.acks)) != len(self.acks):
            raise ValueError("handoff acks must be unique")
        return self


class IndependenceRuleV1(RecordModel):
    between: tuple[Slug, Slug]
    declared: IndependenceDeclared
    means: list[Slug]

    @model_validator(mode="after")
    def _valid_pair(self) -> IndependenceRuleV1:
        if self.between[0] == self.between[1]:
            raise ValueError("independence pair must name two distinct members")
        if len(set(self.means)) != len(self.means):
            raise ValueError("independence means must be unique")
        return self


class TeamRunDefaultsV1(RecordModel):
    fresh_instances: Literal[True] = True
    archive: Literal["always"] = "always"
    worktree_per_member: Literal[True] = True


class TeamPreferencesV1(RecordModel):
    harness_preferences: dict[Slug, list[HarnessId]] = Field(default_factory=dict)
    run_defaults: TeamRunDefaultsV1 = Field(default_factory=TeamRunDefaultsV1)

    @model_validator(mode="after")
    def _unique_harness_preferences(self) -> TeamPreferencesV1:
        for member, harnesses in self.harness_preferences.items():
            if len(set(harnesses)) != len(harnesses):
                raise ValueError(f"harness_preferences.{member} must be unique")
        return self


class WorkflowTaskV1(RecordModel):
    id: Slug
    subject: str = Field(min_length=1)
    owner: Slug
    blocked_by: list[Slug] = Field(default_factory=list)
    workspace_access: WorkspaceAccess = WorkspaceAccess.READ_ONLY

    @model_validator(mode="after")
    def _valid_shape(self) -> WorkflowTaskV1:
        contains_control = any(ord(char) < 32 or ord(char) == 127 for char in self.subject)
        if not self.subject.strip() or contains_control:
            raise ValueError("workflow subject must be non-empty and single-line")
        remainder = self.subject.replace("{goal}", "")
        if "{" in remainder or "}" in remainder:
            raise ValueError("workflow subject supports only the {goal} placeholder")
        if len(set(self.blocked_by)) != len(self.blocked_by):
            raise ValueError("blocked_by references must be unique")
        return self


class TeamTemplateV1(RecordModel):
    schema_version: SchemaVersion
    kind: Literal["team-template"]
    id: Slug
    version: PositiveInt
    summary: str = Field(min_length=1)
    members: list[TeamMemberV1] = Field(min_length=2)
    lead: Slug
    handoff: HandoffRulesV1
    independence: list[IndependenceRuleV1]
    preferences: TeamPreferencesV1
    workflow_skeleton: list[WorkflowTaskV1] = Field(min_length=2)
    dynamic_members: list[object] = Field(
        default_factory=list,
        max_length=0,
        description="Reserved for M1c; must remain empty in M1b.",
    )
    constraints: list[str] = Field(
        default_factory=list,
        max_length=0,
        description="Reserved pending the HB-03 decision; must remain empty in M1b.",
    )

    @model_validator(mode="after")
    def _consistent_composition(self) -> TeamTemplateV1:
        names = [member.name for member in self.members]
        roster = set(names)
        if len(roster) != len(names):
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
                raise ValueError("mechanical independence is not enforceable in M1b")
            unknown = set(rule.between) - roster
            if unknown:
                raise ValueError(
                    "independence pair names unknown members: " + ", ".join(sorted(unknown))
                )
            pair = frozenset(rule.between)
            if pair in pairs:
                raise ValueError("independence pairs must be unique")
            pairs.add(pair)

        task_ids = [task.id for task in self.workflow_skeleton]
        task_set = set(task_ids)
        if len(task_set) != len(task_ids):
            raise ValueError("workflow task ids must be unique")
        owners = Counter(task.owner for task in self.workflow_skeleton)
        if set(owners) != roster or any(count != 1 for count in owners.values()):
            raise ValueError("workflow owners must form a one-task-per-member bijection")
        tasks = {task.id: task for task in self.workflow_skeleton}
        for task in self.workflow_skeleton:
            unknown = set(task.blocked_by) - task_set
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

        for task_id in task_ids:
            visit(task_id)
        return self


class MemberOverridesV1(RecordModel):
    harness: HarnessId | None = None
    model: str | None = Field(default=None, min_length=1)
    effort: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def _harness_qualifies_vendor_values(self) -> MemberOverridesV1:
        if self.harness is None and (self.model is not None or self.effort is not None):
            raise ValueError("model or effort requires harness in the same member override")
        return self


class TeamRunRequestV1(RecordModel):
    schema_version: SchemaVersion
    kind: Literal["team-run-request"]
    template: str = Field(min_length=1)
    workspace: str = Field(min_length=1)
    task_file: str = Field(min_length=1)
    goal: str = Field(
        min_length=1,
        max_length=200,
        pattern=r"^[^\x00-\x1f\x7f]{1,200}$",
    )
    substrate: SubstrateKind = SubstrateKind.LOCAL
    members: dict[Slug, MemberOverridesV1] = Field(default_factory=dict)
    output_dir: str | None = None
    evidence: EvidenceSettingsV1 = Field(default_factory=EvidenceSettingsV1)
    limits: LimitsV1 = Field(default_factory=LimitsV1)
    overlay_refs: list[str] = Field(
        default_factory=list,
        max_length=0,
        description="Reserved for M3 overlays; must remain empty in M1b.",
    )

    @model_validator(mode="after")
    def _goal_has_content(self) -> TeamRunRequestV1:
        if not self.goal.strip():
            raise ValueError("goal must be non-empty")
        return self


class MemberResultV1(RecordModel):
    """Vendor-facing structured output from one team-member invocation."""

    schema_version: SchemaVersion
    kind: Literal["member-result"]
    summary: str
    deliverables: list[str]
    risks: list[str]

    @model_validator(mode="after")
    def _nonempty_summary(self) -> MemberResultV1:
        if not self.summary.strip():
            raise ValueError("summary must be non-empty")
        return self


class DeliverableRefV1(RecordModel):
    path: RelPath
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class HandoffPayloadV1(RecordModel):
    task_id: Slug
    summary: str = Field(min_length=1)
    deliverables: list[DeliverableRefV1]
    risks: list[str]
    done_when: str = Field(min_length=1)


def validate_request_members(request: TeamRunRequestV1, template: TeamTemplateV1) -> None:
    """Reject request override keys outside the referenced template roster."""
    roster = {member.name for member in template.members}
    unknown = set(request.members) - roster
    if unknown:
        raise ValueError("member overrides name unknown members: " + ", ".join(sorted(unknown)))
