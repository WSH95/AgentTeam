"""Vendor-facing structured-output contracts (plan section 7).

`NormalizedReviewV1` and `SynthesisReportV1` are consumed directly by Claude
`--json-schema`, Codex `--output-schema`, and Grok `--json-schema`, so they are
authored in the intersection of the vendors' structured-output dialects: every
property required, `additionalProperties: false`, nullable-required optionals,
no defaults, no patterns/formats, enums instead of `const`.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import Field

from agentteam.domain.common import RecordModel, SchemaVersion


class Severity(StrEnum):
    """Finding severity; section 14's semantic predicate keys on critical/high."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Verdict(StrEnum):
    APPROVE = "approve"
    REQUEST_CHANGES = "request-changes"
    REJECT = "reject"


class ReviewFindingV1(RecordModel):
    id: str
    severity: Severity
    category: str
    file: str | None
    line: int | None
    title: str
    rationale: str


class NormalizedReviewV1(RecordModel):
    """One leg's review in the shared normalized form."""

    schema_version: SchemaVersion
    kind: Literal["normalized-review"]
    target_sha256: str = Field(description="SHA-256 of the review target the leg was given.")
    findings: list[ReviewFindingV1]
    summary: str
    verdict: Verdict


_SOURCE_PAIR_DESCRIPTION = (
    'Each entry is a "<invocation-id>:<finding-id>" pair naming one real '
    "finding from the labelled input reports — never a bare invocation id."
)


class AgreementV1(RecordModel):
    title: str
    sources: list[str] = Field(description=_SOURCE_PAIR_DESCRIPTION)


class DisagreementV1(RecordModel):
    title: str
    asserted_by: list[str] = Field(
        description="Each entry is a bare invocation id exactly as labelled in the input."
    )
    not_asserted_by: list[str] = Field(
        description="Each entry is a bare invocation id exactly as labelled in the input."
    )


class MergedFindingV1(RecordModel):
    id: str
    severity: Severity
    category: str
    file: str | None
    line: int | None
    title: str
    rationale: str
    sources: list[str] = Field(description=_SOURCE_PAIR_DESCRIPTION)


class SynthesisReportV1(RecordModel):
    """The synthesis invocation's output over the leg reviews."""

    schema_version: SchemaVersion
    kind: Literal["synthesis-report"]
    inputs: list[str] = Field(
        description="Exactly the invocation ids of the labelled input reports."
    )
    agreements: list[AgreementV1]
    disagreements: list[DisagreementV1]
    merged_findings: list[MergedFindingV1]
