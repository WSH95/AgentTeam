"""`HarnessProfileSetV1` — local, gitignored harness profiles (plan sections 7, 11).

Each Claude, Codex, and Grok entry records the executable, expected version and
capabilities, the dedicated vendor config home, the native-subscription auth
mode, optional local model/effort defaults and mappings, timeouts, proxy
policy, and environment-variable *names* only. Each capability row carries a
verification level plus `cli_version` and `verified_at`; `atm profile doctor
--probe` updates them. A later `api-test` profile kind remains structurally
possible but is rejected by the M1a runner.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import AwareDatetime, Field, model_validator

from agentteam.domain.common import HarnessId, RecordModel, SchemaVersion, Slug

MAX_ATTEMPT_SECONDS = 15 * 60  # plan section 9: 15-minute attempt limit


class Verification(StrEnum):
    """verified = observed under the AgentTeam runner; observed = in --help/docs only."""

    VERIFIED = "verified"
    OBSERVED = "observed"
    UNVERIFIED = "unverified"


class ProfileKind(StrEnum):
    NATIVE = "native"
    API_TEST = "api-test"


class AuthMode(StrEnum):
    NATIVE_SUBSCRIPTION = "native-subscription"


class ProxyPolicy(StrEnum):
    DENY = "deny"
    INHERIT = "inherit"


class CapabilityRecordV1(RecordModel):
    """One harness capability row with its verification level."""

    name: Slug
    verification: Verification = Verification.UNVERIFIED
    cli_version: str | None = None
    verified_at: AwareDatetime | None = None


class ModelDefaultsV1(RecordModel):
    """Optional local defaults; concrete model names live only here, never in a definition."""

    model: str | None = None
    effort: str | None = None


class ModelMappingV1(RecordModel):
    """Maps the abstract `tier` model hint to a local concrete model name."""

    tier: Literal["fast", "balanced", "strong"]
    model: str


class EffortMappingV1(RecordModel):
    """Maps the abstract `reasoning` hint to a local vendor effort value."""

    reasoning: Literal["low", "medium", "high"]
    effort: str


class TimeoutsV1(RecordModel):
    attempt_seconds: int = Field(default=MAX_ATTEMPT_SECONDS, ge=1, le=MAX_ATTEMPT_SECONDS)


class EnvironmentNamesV1(RecordModel):
    """Environment-variable names only; values are never recorded."""

    config_home_variable: str = Field(
        min_length=1, description="e.g. CLAUDE_CONFIG_DIR, CODEX_HOME, GROK_HOME"
    )
    passthrough: list[str] = Field(
        default_factory=list, description="Names allowed through to the vendor process."
    )
    conflicts: list[str] = Field(
        default_factory=list,
        description=(
            "Names that make a native run fail closed when set (API keys, base URLs, proxies)."
        ),
    )


class HarnessProfileV1(RecordModel):
    """The description of one installed harness as data."""

    harness: HarnessId
    kind: ProfileKind = ProfileKind.NATIVE
    executable: str = Field(min_length=1, description="Command name or path.")
    expected_version: str | None = None
    config_home: str = Field(min_length=1, description="Dedicated vendor config home used by runs.")
    auth_mode: AuthMode = AuthMode.NATIVE_SUBSCRIPTION
    capabilities: list[CapabilityRecordV1] = Field(default_factory=list)
    model_defaults: ModelDefaultsV1 = Field(default_factory=ModelDefaultsV1)
    model_mappings: list[ModelMappingV1] = Field(default_factory=list)
    effort_mappings: list[EffortMappingV1] = Field(default_factory=list)
    timeouts: TimeoutsV1 = Field(default_factory=TimeoutsV1)
    proxy_policy: ProxyPolicy = ProxyPolicy.DENY
    environment: EnvironmentNamesV1

    @model_validator(mode="after")
    def _unique_rows(self) -> HarnessProfileV1:
        names = [c.name for c in self.capabilities]
        if len(set(names)) != len(names):
            raise ValueError("capability names must be unique")
        tiers = [m.tier for m in self.model_mappings]
        if len(set(tiers)) != len(tiers):
            raise ValueError("model_mappings tiers must be unique")
        levels = [m.reasoning for m in self.effort_mappings]
        if len(set(levels)) != len(levels):
            raise ValueError("effort_mappings reasoning levels must be unique")
        return self


class HarnessProfileSetV1(RecordModel):
    """The local profile set (`~/.agentteam/profiles.yaml`; never committed)."""

    schema_version: SchemaVersion
    kind: Literal["harness-profile-set"]
    profiles: list[HarnessProfileV1] = Field(default_factory=list)
    default_harness: HarnessId | None = Field(
        default=None,
        description="Chosen when the Assistant expresses no preference (decided_by: default).",
    )

    @model_validator(mode="after")
    def _consistent(self) -> HarnessProfileSetV1:
        ids = [p.harness for p in self.profiles]
        if len(set(ids)) != len(ids):
            raise ValueError("at most one profile per harness")
        if self.default_harness is not None and self.default_harness not in ids:
            raise ValueError("default_harness must name a listed profile")
        return self
