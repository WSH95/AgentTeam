"""The section-14 oracle matcher and the mechanical/semantic tier evaluators."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from agentteam.domain.common import RunStatus
from agentteam.domain.review import NormalizedReviewV1, ReviewFindingV1, SynthesisReportV1
from agentteam.domain.run import HarnessInvocationV1, TargetHashesV1, TimingV1
from agentteam.run.acceptance import (
    MechanicalInputs,
    OracleDefectV1,
    OracleV1,
    SemanticInputs,
    critical_findings_outside,
    evaluate_mechanical,
    evaluate_semantic,
    identified_defects,
    identifies,
    load_oracle,
)

Payloads = dict[str, dict[str, Any]]

H64 = "a" * 64
OTHER64 = "b" * 64

ORACLE = OracleV1.model_validate(
    {
        "schema_version": 1,
        "kind": "review-oracle",
        "defects": [
            {
                "id": "command-injection",
                "file": "src/publish.ts",
                "category": "command-injection",
                "aliases": ["shell-injection"],
                "line_start": 4,
                "line_end": 8,
            },
            {
                "id": "off-by-one",
                "file": "src/changelog.ts",
                "category": "off-by-one",
                "aliases": ["boundary"],
                "line_start": 3,
                "line_end": 9,
            },
            {
                "id": "input-mutation",
                "file": "src/notes.ts",
                "category": "input-mutation",
                "aliases": ["mutation"],
                "line_start": 7,
                "line_end": 11,
            },
        ],
    }
)


def _finding(
    *,
    id: str = "f1",
    severity: str = "critical",
    category: str = "command-injection",
    file: str | None = "src/publish.ts",
    line: int | None = 5,
    rationale: str = "Input reaches the shell.",
) -> ReviewFindingV1:
    return ReviewFindingV1.model_validate(
        {
            "id": id,
            "severity": severity,
            "category": category,
            "file": file,
            "line": line,
            "title": "A finding",
            "rationale": rationale,
        }
    )


def _review(*findings: ReviewFindingV1) -> NormalizedReviewV1:
    return NormalizedReviewV1.model_validate(
        {
            "schema_version": 1,
            "kind": "normalized-review",
            "target_sha256": H64,
            "findings": [finding.model_dump(mode="json") for finding in findings],
            "summary": "Review.",
            "verdict": "request-changes",
        }
    )


# -- matcher ------------------------------------------------------------------


def test_identifies_inside_the_window_including_both_edges() -> None:
    defect = ORACLE.defects[0]
    assert identifies(_finding(line=5), defect)
    assert identifies(_finding(line=4), defect)
    assert identifies(_finding(line=8), defect)
    assert not identifies(_finding(line=3), defect)
    assert not identifies(_finding(line=9), defect)


def test_identifies_requires_file_and_category_or_alias() -> None:
    defect = ORACLE.defects[0]
    assert not identifies(_finding(file="src/other.ts"), defect)
    assert not identifies(_finding(category="something-else"), defect)
    assert identifies(_finding(category="shell-injection"), defect)
    assert not identifies(_finding(line=None), defect)
    assert not identifies(_finding(file=None), defect)


def test_identified_defects_and_critical_outside() -> None:
    review = _review(
        _finding(id="f1"),
        _finding(
            id="f2", severity="medium", category="off-by-one", file="src/changelog.ts", line=4
        ),
        _finding(id="f3", severity="critical", category="invented", file="src/new.ts", line=1),
        _finding(id="f4", severity="low", category="style", file="src/new.ts", line=2),
    )
    assert identified_defects(review, ORACLE) == {"command-injection", "off-by-one"}
    outside = critical_findings_outside(review, ORACLE)
    assert [finding.id for finding in outside] == ["f3"]


def test_oracle_model_is_closed_and_window_ordered(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        OracleV1.model_validate(
            {"schema_version": 1, "kind": "review-oracle", "defects": [], "extra": 1}
        )
    with pytest.raises(ValidationError):
        OracleDefectV1.model_validate(
            {
                "id": "x",
                "file": "a.ts",
                "category": "c",
                "line_start": 9,
                "line_end": 3,
            }
        )
    path = tmp_path / "oracle.json"
    path.write_text(json.dumps(ORACLE.model_dump(mode="json")), encoding="utf-8")
    assert load_oracle(path) == ORACLE


# -- mechanical tier ----------------------------------------------------------


def _leg(
    payloads: Payloads,
    invocation_id: str,
    *,
    status: RunStatus = RunStatus.SUCCEEDED,
    before: str = H64,
    after: str | None = H64,
    bundle_hash: str = H64,
) -> HarnessInvocationV1:
    base = HarnessInvocationV1.model_validate(payloads["harness-invocation-v1.schema.json"])
    return base.model_copy(
        update={
            "invocation_id": invocation_id,
            "status": status,
            "effective_definition_hash": bundle_hash,
            "target": TargetHashesV1(before=before, after=after),
            "timing": TimingV1(
                started_at=datetime(2026, 8, 23, 12, 0, tzinfo=UTC),
                finished_at=datetime(2026, 8, 23, 12, 1, tzinfo=UTC),
                duration_ms=60_000,
            ),
        }
    )


def _mech(payloads: Payloads, **overrides: Any) -> MechanicalInputs:
    values: dict[str, Any] = {
        "legs": [_leg(payloads, "inv-claude-code"), _leg(payloads, "inv-codex")],
        "bundle_hash": H64,
        "package_rehash": H64,
        "manifest_problems": [],
        "redaction_problems": [],
    }
    values.update(overrides)
    return MechanicalInputs(**values)


def test_mechanical_all_conditions_pass(payloads: Payloads) -> None:
    result = evaluate_mechanical(_mech(payloads))
    assert result.passed is True
    assert [condition.id for condition in result.conditions] == [
        "cond-1",
        "cond-6",
        "cond-7",
        "cond-8",
    ]
    assert all(condition.passed for condition in result.conditions)


def test_mechanical_fails_on_a_failed_leg_or_target_mutation(payloads: Payloads) -> None:
    failed = evaluate_mechanical(
        _mech(
            payloads,
            legs=[
                _leg(payloads, "inv-claude-code"),
                _leg(payloads, "inv-codex", status=RunStatus.FAILED),
            ],
        )
    )
    assert failed.passed is False
    cond_1 = failed.conditions[0]
    assert cond_1.passed is False
    assert cond_1.detail is not None and "inv-codex" in cond_1.detail
    mutated = evaluate_mechanical(
        _mech(
            payloads,
            legs=[
                _leg(payloads, "inv-claude-code"),
                _leg(payloads, "inv-grok", after=OTHER64),
            ],
        )
    )
    assert mutated.passed is False
    assert mutated.conditions[0].passed is False


def test_mechanical_fails_on_package_rehash_manifest_or_redaction(payloads: Payloads) -> None:
    rehash = evaluate_mechanical(_mech(payloads, package_rehash=OTHER64))
    assert rehash.conditions[1].passed is False
    manifest = evaluate_mechanical(_mech(payloads, manifest_problems=["changed: run.json"]))
    assert manifest.conditions[2].passed is False
    redaction = evaluate_mechanical(
        _mech(payloads, redaction_problems=["legs/inv-codex/invocation.render.json leaks values"])
    )
    assert redaction.conditions[3].passed is False


# -- semantic tier ------------------------------------------------------------


def _happy_reviews() -> dict[str, NormalizedReviewV1]:
    return {
        "inv-claude-code": _review(
            _finding(id="c1"),
            _finding(
                id="c2",
                severity="medium",
                category="off-by-one",
                file="src/changelog.ts",
                line=4,
            ),
        ),
        "inv-codex": _review(
            _finding(id="x1", severity="high"),
            _finding(
                id="x2",
                severity="medium",
                category="input-mutation",
                file="src/notes.ts",
                line=9,
            ),
        ),
        "inv-grok": _review(
            _finding(id="g1"),
            _finding(id="g2", severity="low", category="boundary", file="src/changelog.ts", line=5),
        ),
    }


def _synthesis_report() -> SynthesisReportV1:
    def merged(id: str, category: str, file: str, line: int, sources: list[str]) -> dict[str, Any]:
        return {
            "id": id,
            "severity": "high",
            "category": category,
            "file": file,
            "line": line,
            "title": id,
            "rationale": "Merged.",
            "sources": sources,
        }

    return SynthesisReportV1.model_validate(
        {
            "schema_version": 1,
            "kind": "synthesis-report",
            "inputs": ["inv-claude-code", "inv-codex", "inv-grok"],
            "agreements": [
                {
                    "title": "Command injection",
                    "sources": ["inv-claude-code:c1", "inv-codex:x1", "inv-grok:g1"],
                }
            ],
            "disagreements": [
                {
                    "title": "Input mutation",
                    "asserted_by": ["inv-codex"],
                    "not_asserted_by": ["inv-claude-code", "inv-grok"],
                }
            ],
            "merged_findings": [
                merged(
                    "m1",
                    "command-injection",
                    "src/publish.ts",
                    5,
                    ["inv-claude-code:c1", "inv-codex:x1", "inv-grok:g1"],
                ),
                merged("m2", "off-by-one", "src/changelog.ts", 4, ["inv-claude-code:c2"]),
                merged("m3", "input-mutation", "src/notes.ts", 9, ["inv-codex:x2"]),
            ],
        }
    )


def _semantic(**overrides: Any) -> SemanticInputs:
    values: dict[str, Any] = {
        "oracle": ORACLE,
        "leg_reviews": _happy_reviews(),
        "synthesis_report": _synthesis_report(),
        "attribution_valid": True,
    }
    values.update(overrides)
    return SemanticInputs(**values)


def test_semantic_all_conditions_pass() -> None:
    result = evaluate_semantic(_semantic())
    assert result.passed is True
    assert [condition.id for condition in result.conditions] == [
        "cond-2",
        "cond-3",
        "cond-4",
        "cond-5",
        "cond-9",
    ]


def test_semantic_without_an_oracle_is_unevaluated() -> None:
    result = evaluate_semantic(_semantic(oracle=None))
    assert result.passed is None
    assert all(condition.passed is None for condition in result.conditions)


def test_semantic_miss_fails_cond_2_and_3() -> None:
    reviews = _happy_reviews()
    reviews["inv-grok"] = _review(_finding(id="g1"))  # injection only
    reviews["inv-codex"] = _review(_finding(id="x1", severity="high"))  # loses mutation
    result = evaluate_semantic(_semantic(leg_reviews=reviews))
    assert result.passed is False
    by_id = {condition.id: condition for condition in result.conditions}
    assert by_id["cond-2"].passed is False
    assert by_id["cond-2"].detail is not None and "inv-grok" in by_id["cond-2"].detail
    assert by_id["cond-3"].passed is False
    assert by_id["cond-3"].detail is not None and "input-mutation" in by_id["cond-3"].detail


def test_invented_critical_fails_cond_4() -> None:
    reviews = _happy_reviews()
    reviews["inv-codex"] = _review(
        _finding(id="x1", severity="high"),
        _finding(
            id="x2", severity="medium", category="input-mutation", file="src/notes.ts", line=9
        ),
        _finding(id="x9", severity="critical", category="invented", file="src/new.ts", line=1),
    )
    result = evaluate_semantic(_semantic(leg_reviews=reviews))
    by_id = {condition.id: condition for condition in result.conditions}
    assert by_id["cond-4"].passed is False
    assert by_id["cond-4"].detail is not None and "x9" in by_id["cond-4"].detail


def test_missing_rationale_fails_cond_2() -> None:
    reviews = _happy_reviews()
    reviews["inv-claude-code"] = _review(
        _finding(id="c1", rationale=" "),
        _finding(
            id="c2", severity="medium", category="off-by-one", file="src/changelog.ts", line=4
        ),
    )
    result = evaluate_semantic(_semantic(leg_reviews=reviews))
    by_id = {condition.id: condition for condition in result.conditions}
    assert by_id["cond-2"].passed is False


def test_synthesis_absent_leaves_cond_5_unevaluated_and_overall_incomplete() -> None:
    result = evaluate_semantic(_semantic(synthesis_report=None, attribution_valid=None))
    by_id = {condition.id: condition for condition in result.conditions}
    assert by_id["cond-5"].passed is None
    assert result.passed is None


def test_synthesis_coverage_gap_or_bad_attribution_fails_cond_5() -> None:
    report = _synthesis_report()
    trimmed = report.model_copy(update={"merged_findings": report.merged_findings[:2]})
    result = evaluate_semantic(_semantic(synthesis_report=trimmed))
    by_id = {condition.id: condition for condition in result.conditions}
    assert by_id["cond-5"].passed is False
    bad_attribution = evaluate_semantic(_semantic(attribution_valid=False))
    by_id = {condition.id: condition for condition in bad_attribution.conditions}
    assert by_id["cond-5"].passed is False
