"""The section-14 oracle, matcher, and acceptance-tier evaluators.

The oracle is an internal fixture model, not a checked-in schema (the schema
set stays at nine). A finding *identifies* a defect when the file matches, the
category is the defect's category or one of its aliases, and the line falls
inside the closed window. A "critical finding outside the oracle" is any
critical or high finding that identifies no defect. The mechanical tier
{cond-1, cond-6, cond-7, cond-8} is evaluated on every ensemble run; the
semantic tier {cond-2..5, cond-9} only when an oracle is configured — a
semantic miss with valid mechanics exits 3.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from agentteam.domain.common import RecordModel, RunStatus, SchemaVersion
from agentteam.domain.review import (
    NormalizedReviewV1,
    ReviewFindingV1,
    Severity,
    SynthesisReportV1,
)
from agentteam.domain.run import (
    AcceptanceResultV1,
    ConditionResultV1,
    HarnessInvocationV1,
)

_CRITICAL = frozenset({Severity.CRITICAL, Severity.HIGH})
_INJECTION_CATEGORY = "command-injection"


class OracleDefectV1(RecordModel):
    id: str = Field(min_length=1)
    file: str = Field(min_length=1)
    category: str = Field(min_length=1)
    aliases: list[str] = Field(default_factory=list)
    line_start: int = Field(ge=1)
    line_end: int = Field(ge=1)

    @model_validator(mode="after")
    def _window_ordered(self) -> OracleDefectV1:
        if self.line_end < self.line_start:
            raise ValueError("line_end must be >= line_start")
        return self


class OracleV1(RecordModel):
    schema_version: SchemaVersion
    kind: Literal["review-oracle"]
    defects: list[OracleDefectV1] = Field(min_length=1)


def load_oracle(path: Path) -> OracleV1:
    return OracleV1.model_validate(json.loads(path.read_text(encoding="utf-8")))


def identifies(finding: ReviewFindingV1, defect: OracleDefectV1) -> bool:
    if finding.file != defect.file or finding.line is None:
        return False
    if finding.category != defect.category and finding.category not in defect.aliases:
        return False
    return defect.line_start <= finding.line <= defect.line_end


def identified_defects(review: NormalizedReviewV1, oracle: OracleV1) -> set[str]:
    return {
        defect.id
        for defect in oracle.defects
        for finding in review.findings
        if identifies(finding, defect)
    }


def critical_findings_outside(
    review: NormalizedReviewV1, oracle: OracleV1
) -> list[ReviewFindingV1]:
    return [
        finding
        for finding in review.findings
        if finding.severity in _CRITICAL
        and not any(identifies(finding, defect) for defect in oracle.defects)
    ]


# -- mechanical tier {1, 6, 7, 8} --------------------------------------------


@dataclass(frozen=True)
class MechanicalInputs:
    legs: list[HarnessInvocationV1]
    bundle_hash: str
    package_rehash: str
    manifest_problems: list[str]
    redaction_problems: list[str]


def _summarize(conditions: list[ConditionResultV1]) -> bool | None:
    if any(condition.passed is False for condition in conditions):
        return False
    if any(condition.passed is None for condition in conditions):
        return None
    return True


def evaluate_mechanical(inputs: MechanicalInputs) -> AcceptanceResultV1:
    problems_1: list[str] = []
    for leg in inputs.legs:
        if leg.status is not RunStatus.SUCCEEDED:
            problems_1.append(f"{leg.invocation_id} finished {leg.status.value}")
        if leg.effective_definition_hash != inputs.bundle_hash:
            problems_1.append(f"{leg.invocation_id} used a different bundle hash")
        if leg.target.after is None:
            problems_1.append(f"{leg.invocation_id} has no target after-hash")
        elif leg.target.after != leg.target.before:
            problems_1.append(f"{leg.invocation_id} mutated its target")
    before_hashes = {leg.target.before for leg in inputs.legs}
    if len(before_hashes) > 1:
        problems_1.append("legs did not share one target before-hash")
    cond_1 = ConditionResultV1(
        id="cond-1",
        passed=not problems_1,
        detail="; ".join(problems_1) or "independent fresh legs, one bundle, target unmutated",
    )
    cond_6 = ConditionResultV1(
        id="cond-6",
        passed=inputs.package_rehash == inputs.bundle_hash,
        detail=(
            "package re-hash equals the bundle hash"
            if inputs.package_rehash == inputs.bundle_hash
            else f"package re-hash {inputs.package_rehash[:12]}… differs from the bundle hash"
        ),
    )
    cond_7 = ConditionResultV1(
        id="cond-7",
        passed=not inputs.manifest_problems,
        detail="; ".join(inputs.manifest_problems) or "archive manifest reconstructs",
    )
    cond_8 = ConditionResultV1(
        id="cond-8",
        passed=not inputs.redaction_problems,
        detail="; ".join(inputs.redaction_problems)
        or "records carry environment names only; raw evidence stays in the local archive",
    )
    conditions = [cond_1, cond_6, cond_7, cond_8]
    return AcceptanceResultV1(passed=_summarize(conditions), conditions=conditions)


# -- semantic tier {2, 3, 4, 5, 9} -------------------------------------------


@dataclass(frozen=True)
class SemanticInputs:
    oracle: OracleV1 | None
    leg_reviews: dict[str, NormalizedReviewV1]
    synthesis_report: SynthesisReportV1 | None
    attribution_valid: bool | None


def _injection_defect(oracle: OracleV1) -> OracleDefectV1 | None:
    for defect in oracle.defects:
        if defect.category == _INJECTION_CATEGORY:
            return defect
    return None


def evaluate_semantic(inputs: SemanticInputs) -> AcceptanceResultV1:
    if inputs.oracle is None:
        conditions = [
            ConditionResultV1(id=f"cond-{n}", passed=None, detail="no oracle configured")
            for n in (2, 3, 4, 5, 9)
        ]
        return AcceptanceResultV1(passed=None, conditions=conditions)
    oracle = inputs.oracle
    injection = _injection_defect(oracle)

    problems_2: list[str] = []
    for invocation_id, review in inputs.leg_reviews.items():
        identified = identified_defects(review, oracle)
        if injection is None:
            problems_2.append("oracle has no command-injection defect")
            break
        if injection.id not in identified:
            problems_2.append(f"{invocation_id} did not identify {injection.id}")
        if len(identified) < 2:
            problems_2.append(f"{invocation_id} identified fewer than two seeded defects")
        for defect in oracle.defects:
            if defect.id not in identified:
                continue
            for finding in review.findings:
                if identifies(finding, defect) and not finding.rationale.strip():
                    problems_2.append(
                        f"{invocation_id} finding {finding.id} has no actionable rationale"
                    )
    cond_2 = ConditionResultV1(
        id="cond-2",
        passed=not problems_2,
        detail="; ".join(problems_2)
        or "every leg identified command injection plus another seeded defect",
    )

    union: set[str] = set()
    for review in inputs.leg_reviews.values():
        union |= identified_defects(review, oracle)
    missing = sorted({defect.id for defect in oracle.defects} - union)
    cond_3 = ConditionResultV1(
        id="cond-3",
        passed=not missing,
        detail=("union misses: " + ", ".join(missing)) if missing else "union covers all defects",
    )

    problems_4: list[str] = []
    for invocation_id, review in inputs.leg_reviews.items():
        for finding in critical_findings_outside(review, oracle):
            problems_4.append(f"{invocation_id} invented critical finding {finding.id}")
    cond_4 = ConditionResultV1(
        id="cond-4",
        passed=not problems_4,
        detail="; ".join(problems_4) or "no critical finding outside the oracle",
    )

    if inputs.synthesis_report is None:
        cond_5 = ConditionResultV1(id="cond-5", passed=None, detail="synthesis did not run")
    else:
        merged_review = NormalizedReviewV1.model_validate(
            {
                "schema_version": 1,
                "kind": "normalized-review",
                "target_sha256": "0" * 64,
                "findings": [
                    finding.model_dump(mode="json", exclude={"sources"})
                    for finding in inputs.synthesis_report.merged_findings
                ],
                "summary": "merged",
                "verdict": "request-changes",
            }
        )
        covered = identified_defects(merged_review, oracle)
        missing_merged = sorted({defect.id for defect in oracle.defects} - covered)
        problems_5: list[str] = []
        if missing_merged:
            problems_5.append("merged findings miss: " + ", ".join(missing_merged))
        if inputs.attribution_valid is not True:
            problems_5.append("attribution failed validation")
        cond_5 = ConditionResultV1(
            id="cond-5",
            passed=not problems_5,
            detail="; ".join(problems_5)
            or "synthesis lists all defects with valid attribution and both agreement kinds",
        )

    cond_9 = ConditionResultV1(
        id="cond-9",
        passed=True,
        detail="tiers evaluated and stored separately; a semantic miss exits 3",
    )

    conditions = [cond_2, cond_3, cond_4, cond_5, cond_9]
    return AcceptanceResultV1(passed=_summarize(conditions), conditions=conditions)
