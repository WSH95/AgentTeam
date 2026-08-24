"""`RunRequestV1` — the human-authored run request (plan sections 7-9).

Runtime IDs, timestamps, results, and subprocess state belong only in the
archive. `effective_definition_hash` is computed state and is never a request
field. `overlay_refs` is reserved for M3 and must be empty in M1a.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from agentteam.domain.common import HarnessId, RecordModel, SchemaVersion
from agentteam.domain.profile import MAX_ATTEMPT_SECONDS

MAX_TRANSIENT_RETRIES = 1  # plan section 9: the single transient retry


class SynthesisSettingsV1(RecordModel):
    """Fan-out legs are followed by one fresh synthesis invocation when enabled."""

    enabled: bool = True
    harness: HarnessId = HarnessId.CLAUDE_CODE


class HarnessOverrideV1(RecordModel):
    """One local per-harness override; `harness` uses the harness identifiers."""

    harness: HarnessId
    value: str = Field(min_length=1)


class EvidenceSettingsV1(RecordModel):
    retain_raw_streams: bool = Field(
        default=True, description="Keep raw vendor output in the local, gitignored archive."
    )


class AcceptanceSettingsV1(RecordModel):
    """Optional semantic-acceptance evaluation (plan section 14).

    The oracle is read only after synthesis (state-machine step 12); it is
    never copied into a leg workspace and never given to a leg or to
    synthesis. Without an oracle the semantic tier stays unevaluated.
    """

    oracle: str | None = Field(
        default=None,
        description=(
            "Path to the labelled oracle JSON; a relative path resolves against "
            "the request file's directory."
        ),
    )


class LimitsV1(RecordModel):
    """May lower but never raise the section 9 caps."""

    attempt_seconds: int | None = Field(default=None, ge=1, le=MAX_ATTEMPT_SECONDS)
    transient_retries: int | None = Field(default=None, ge=0, le=MAX_TRANSIENT_RETRIES)


class RunRequestV1(RecordModel):
    """What `atm run` consumes (file and/or flags)."""

    schema_version: SchemaVersion
    kind: Literal["run-request"]
    assistant: str = Field(min_length=1, description="Path to the Assistant package.")
    overlay_refs: list[str] = Field(
        default_factory=list, description="Reserved for M3 overlays; must be empty in M1a."
    )
    workspace: str = Field(min_length=1, description="Path to the workspace to review.")
    task_file: str = Field(min_length=1, description="Path to the task text file.")
    mode: Literal["direct"]
    harnesses: list[HarnessId] = Field(
        default_factory=list,
        description=(
            "Requested harnesses (unique). Empty: the Assistant's harness_policy decides "
            "and the run is solo."
        ),
    )
    synthesis: SynthesisSettingsV1 = Field(default_factory=SynthesisSettingsV1)
    model_overrides: list[HarnessOverrideV1] = Field(default_factory=list)
    effort_overrides: list[HarnessOverrideV1] = Field(default_factory=list)
    output_dir: str | None = None
    evidence: EvidenceSettingsV1 = Field(default_factory=EvidenceSettingsV1)
    acceptance: AcceptanceSettingsV1 = Field(default_factory=AcceptanceSettingsV1)
    limits: LimitsV1 = Field(default_factory=LimitsV1)

    @model_validator(mode="after")
    def _unique_harnesses(self) -> RunRequestV1:
        if len(set(self.harnesses)) != len(self.harnesses):
            raise ValueError("harnesses must be unique")
        for label, overrides in (
            ("model_overrides", self.model_overrides),
            ("effort_overrides", self.effort_overrides),
        ):
            ids = [o.harness for o in overrides]
            if len(set(ids)) != len(ids):
                raise ValueError(f"{label} harnesses must be unique")
        return self
