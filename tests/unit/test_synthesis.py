"""Synthesis instructions, the labelled-reports document, and report validation
(plan section 12 steps 10-12)."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import pytest

from agentteam.domain.review import NormalizedReviewV1, SynthesisReportV1
from agentteam.run.synthesis import (
    INSTRUCTIONS_FILE,
    SynthesisValidationError,
    build_synthesis_task,
    instruction_hash,
    validate_synthesis,
)

Payloads = dict[str, dict[str, Any]]


def _review(payloads: Payloads, finding_id: str) -> NormalizedReviewV1:
    data = dict(payloads["normalized-review-v1.schema.json"])
    data["findings"] = [dict(data["findings"][0], id=finding_id)]
    return NormalizedReviewV1.model_validate(data)


def _report(payloads: Payloads, **overrides: Any) -> SynthesisReportV1:
    data: dict[str, Any] = {
        "schema_version": 1,
        "kind": "synthesis-report",
        "inputs": ["inv-claude-code", "inv-codex"],
        "agreements": [
            {"title": "Command injection", "sources": ["inv-claude-code:a1", "inv-codex:b1"]}
        ],
        "disagreements": [
            {
                "title": "Only claude saw it",
                "asserted_by": ["inv-claude-code"],
                "not_asserted_by": ["inv-codex"],
            }
        ],
        "merged_findings": [
            dict(
                payloads["normalized-review-v1.schema.json"]["findings"][0],
                id="m1",
                sources=["inv-claude-code:a1", "inv-codex:b1"],
            )
        ],
    }
    data.update(overrides)
    return SynthesisReportV1.model_validate(data)


def _legs(payloads: Payloads) -> dict[str, NormalizedReviewV1]:
    return {
        "inv-claude-code": _review(payloads, "a1"),
        "inv-codex": _review(payloads, "b1"),
    }


def test_committed_instructions_exist_and_speak_in_invocation_ids() -> None:
    text = INSTRUCTIONS_FILE.read_text(encoding="utf-8")
    assert "invocation" in text
    assert "Never invent" in text


def test_instruction_hash_is_lf_normalised_and_stable(tmp_path: Path) -> None:
    digest = instruction_hash()
    assert re.fullmatch(r"[0-9a-f]{64}", digest)
    assert digest == instruction_hash()
    lf = tmp_path / "lf.md"
    lf.write_bytes(b"line one\nline two\n")
    crlf = tmp_path / "crlf.md"
    crlf.write_bytes(b"line one\r\nline two\r\n")
    assert instruction_hash(lf) == instruction_hash(crlf)
    assert instruction_hash(lf) == hashlib.sha256(b"line one\nline two\n").hexdigest()


def test_labelled_document_carries_headers_and_reviews_in_order(payloads: Payloads) -> None:
    legs = [
        ("inv-claude-code", "claude-code", _review(payloads, "a1")),
        ("inv-codex", "codex", _review(payloads, "b1")),
    ]
    document = build_synthesis_task(legs)
    headers = re.findall(r"^### leg (\S+) harness (\S+)$", document, flags=re.MULTILINE)
    assert headers == [("inv-claude-code", "claude-code"), ("inv-codex", "codex")]
    assert '"a1"' in document
    assert '"b1"' in document
    assert document.index("inv-claude-code") < document.index("inv-codex")


def test_validate_accepts_a_well_formed_report_and_returns_attribution(
    payloads: Payloads,
) -> None:
    attribution = validate_synthesis(_report(payloads), _legs(payloads))
    assert [row.merged_finding_id for row in attribution] == ["m1"]
    assert attribution[0].sources == ["inv-claude-code:a1", "inv-codex:b1"]


def test_validate_rejects_an_inputs_mismatch(payloads: Payloads) -> None:
    with pytest.raises(SynthesisValidationError, match="inputs"):
        validate_synthesis(_report(payloads, inputs=["inv-claude-code"]), _legs(payloads))
    with pytest.raises(SynthesisValidationError, match="inputs"):
        validate_synthesis(
            _report(payloads, inputs=["inv-claude-code", "inv-codex", "inv-grok"]),
            _legs(payloads),
        )


def test_validate_rejects_unknown_or_malformed_sources(payloads: Payloads) -> None:
    bad_finding = _report(
        payloads,
        merged_findings=[
            dict(
                payloads["normalized-review-v1.schema.json"]["findings"][0],
                id="m1",
                sources=["inv-claude-code:no-such-finding"],
            )
        ],
    )
    with pytest.raises(SynthesisValidationError, match="no-such-finding"):
        validate_synthesis(bad_finding, _legs(payloads))
    bad_leg = _report(
        payloads,
        merged_findings=[
            dict(
                payloads["normalized-review-v1.schema.json"]["findings"][0],
                id="m1",
                sources=["inv-grok:a1"],
            )
        ],
    )
    with pytest.raises(SynthesisValidationError, match="inv-grok"):
        validate_synthesis(bad_leg, _legs(payloads))
    malformed = _report(
        payloads,
        merged_findings=[
            dict(
                payloads["normalized-review-v1.schema.json"]["findings"][0],
                id="m1",
                sources=["not-a-pair"],
            )
        ],
    )
    with pytest.raises(SynthesisValidationError, match="not-a-pair"):
        validate_synthesis(malformed, _legs(payloads))


def test_validate_rejects_single_leg_agreements(payloads: Payloads) -> None:
    lonely = _report(
        payloads,
        agreements=[{"title": "Solo agreement", "sources": ["inv-claude-code:a1"]}],
    )
    with pytest.raises(SynthesisValidationError, match="agreement"):
        validate_synthesis(lonely, _legs(payloads))


def test_validate_rejects_bad_disagreements(payloads: Payloads) -> None:
    overlapping = _report(
        payloads,
        disagreements=[
            {
                "title": "Both sides",
                "asserted_by": ["inv-claude-code"],
                "not_asserted_by": ["inv-claude-code"],
            }
        ],
    )
    with pytest.raises(SynthesisValidationError, match="disagreement"):
        validate_synthesis(overlapping, _legs(payloads))
    unknown = _report(
        payloads,
        disagreements=[
            {
                "title": "Stranger",
                "asserted_by": ["inv-grok"],
                "not_asserted_by": ["inv-codex"],
            }
        ],
    )
    with pytest.raises(SynthesisValidationError, match="inv-grok"):
        validate_synthesis(unknown, _legs(payloads))


def test_validation_error_aggregates_every_problem(payloads: Payloads) -> None:
    broken = _report(
        payloads,
        inputs=["inv-claude-code"],
        agreements=[{"title": "Solo", "sources": ["inv-claude-code:a1"]}],
    )
    with pytest.raises(SynthesisValidationError) as excinfo:
        validate_synthesis(broken, _legs(payloads))
    message = str(excinfo.value)
    assert "inputs" in message
    assert "agreement" in message
