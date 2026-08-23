"""`AssistantDefinitionV1` — the portable Assistant definition (plan section 7).

Aligned with `docs/discovery/assistant-domain-model.md` section 3: stable
metadata, separate persona/principle/method instruction files, semantic
capability requirements, explicit artifact references (Skills are
`agent-skill` artifacts with vendored sources), portable permission intent, a
portable `harness_policy` with abstract model hints only, optional
substrate-neutral collaboration guidance, and prohibited-content checks. It
never contains a concrete project, session, credential, provider endpoint, or
permanent harness binding.
"""

from __future__ import annotations

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


class RequirementLevel(StrEnum):
    REQUIRED = "required"
    PREFERRED = "preferred"


class ArtifactKind(StrEnum):
    AGENT_SKILL = "agent-skill"
    LOCAL_SCRIPT = "local-script"
    PLUGIN = "plugin"
    MCP_SERVER = "mcp-server"
    BINARY = "binary"


class VendoredSourceV1(RecordModel):
    """Where an artifact's content lives inside the portable package."""

    vendored: RelPath = Field(description="Path inside the package (directory or file).")


class ArtifactRequirementV1(RecordModel):
    """An explicit demand for one concrete artifact (never substituted)."""

    ref: Slug
    kind: ArtifactKind
    source: VendoredSourceV1
    level: RequirementLevel = RequirementLevel.REQUIRED


class CapabilityRequirementV1(RecordModel):
    """A semantic ability requirement satisfiable natively or by different artifacts."""

    capability: Slug
    level: RequirementLevel = RequirementLevel.REQUIRED


class PermissionsV1(RecordModel):
    """Harness-neutral permission intent; each adapter renders it natively."""

    filesystem: Literal["read-only", "read-write-workspace"] = "read-only"
    network: Literal["allow", "deny"] = "deny"
    shell: Literal["allow", "deny"] = "deny"


class PreferenceV1(RecordModel):
    """One user-independent stable working preference."""

    name: Slug
    value: str


class CollaborationV1(RecordModel):
    """Substrate-neutral hand-off, review, and escalation guidance (AD-03)."""

    handoff: str | None = None
    review: str | None = None
    escalate_when: list[str] = Field(default_factory=list)


class ModelHintsV1(RecordModel):
    """Abstract model hints only — never a concrete model or provider."""

    tier: Literal["fast", "balanced", "strong"] | None = None
    reasoning: Literal["low", "medium", "high"] | None = None


class HarnessPolicyV1(RecordModel):
    """Assistant-level harness selection preferences as data (HB-03)."""

    preferred: list[HarnessId] = Field(default_factory=list)
    allowed: list[HarnessId] = Field(
        default_factory=list,
        description="Empty means no restriction beyond `forbidden` (plan section 11 step 3).",
    )
    forbidden: list[HarnessId] = Field(default_factory=list)
    required_capabilities: list[Slug] = Field(default_factory=list)
    model_hints: ModelHintsV1 = Field(default_factory=ModelHintsV1)

    @model_validator(mode="after")
    def _consistent(self) -> HarnessPolicyV1:
        forbidden = set(self.forbidden)
        clash = forbidden & (set(self.preferred) | set(self.allowed))
        if clash:
            names = ", ".join(sorted(h.value for h in clash))
            raise ValueError(
                f"harness_policy lists {names} as both forbidden and preferred/allowed"
            )
        return self


class PresentationDefaultsV1(RecordModel):
    """Optional presentation hints; never an account, topic, or token."""

    display_name: str | None = None
    emoji: str | None = None


class ProposalTarget(StrEnum):
    PRINCIPLES = "principles"
    PREFERENCES = "preferences"
    COLLABORATION = "collaboration"
    HARNESS_POLICY = "harness_policy"
    FAILURE_MODES = "failure_modes"


class EvolutionV1(RecordModel):
    """Which sections accept reviewed proposals (EV-01..EV-05); overlays arrive in M3."""

    accepts_proposals_for: list[ProposalTarget] = Field(default_factory=list)
    failure_modes: RelPath | None = None


class ProhibitedContentCheck(StrEnum):
    """Content classes that must never appear in a definition (ADM section 4)."""

    WORKSPACE_PATHS = "workspace-paths"
    BRANCH_NAMES = "branch-names"
    SESSION_IDENTIFIERS = "session-identifiers"
    SURFACE_TOPOLOGY = "surface-topology"
    BOUND_HARNESS = "bound-harness"
    SECRETS = "secrets"
    RUNTIME_MEMORY = "runtime-memory"


ALL_PROHIBITED_CONTENT_CHECKS: tuple[ProhibitedContentCheck, ...] = tuple(ProhibitedContentCheck)


class AssistantDefinitionV1(RecordModel):
    """The portable, reusable definition of one Assistant (AD-01..AD-06, AD-08)."""

    schema_version: SchemaVersion
    kind: Literal["assistant-definition"]
    id: Slug
    version: PositiveInt = Field(
        description="Base Definition version; overlays are versioned separately."
    )
    summary: str = Field(min_length=1)
    persona: RelPath = Field(description="Persona instruction file inside the package.")
    purpose: list[str] = Field(min_length=1, description="Responsibilities; what done means.")
    principles: RelPath = Field(
        description="Judgment-principle instruction file inside the package."
    )
    methods: RelPath | None = Field(default=None, description="Working-method instruction file.")
    preferences: list[PreferenceV1] = Field(default_factory=list)
    capabilities: list[CapabilityRequirementV1] = Field(default_factory=list)
    artifacts: list[ArtifactRequirementV1] = Field(default_factory=list)
    permissions: PermissionsV1 = Field(default_factory=PermissionsV1)
    collaboration: CollaborationV1 | None = None
    harness_policy: HarnessPolicyV1 = Field(default_factory=HarnessPolicyV1)
    presentation_defaults: PresentationDefaultsV1 | None = None
    evolution: EvolutionV1 | None = None
    prohibited_content: list[ProhibitedContentCheck] = Field(
        default_factory=lambda: list(ALL_PROHIBITED_CONTENT_CHECKS),
        description="Content checks the validator enforces on this definition.",
    )

    @model_validator(mode="after")
    def _unique_names(self) -> AssistantDefinitionV1:
        refs = [a.ref for a in self.artifacts]
        if len(set(refs)) != len(refs):
            raise ValueError("artifact refs must be unique")
        return self
