"""The synthesis leg's inputs and validation (plan section 12 steps 10-12).

Synthesis receives only the labelled leg reports — never the target tree and
never the oracle. Attribution is validated against source pairs that actually
exist; a report that references anything else is a runtime failure, not a
semantic one.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from pathlib import Path

from agentteam.domain.review import NormalizedReviewV1, SynthesisReportV1
from agentteam.domain.run import AttributionV1
from agentteam.synthesis import INSTRUCTIONS_FILE

__all__ = [
    "INSTRUCTIONS_FILE",
    "SynthesisValidationError",
    "build_synthesis_task",
    "instruction_hash",
    "validate_synthesis",
]


class SynthesisValidationError(ValueError):
    """The synthesis report failed schema-adjacent validation (exit 1)."""


def instruction_hash(path: Path = INSTRUCTIONS_FILE) -> str:
    """SHA-256 of the instruction bytes after CRLF/CR -> LF normalisation."""
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def build_synthesis_task(legs: Sequence[tuple[str, str, NormalizedReviewV1]]) -> str:
    """The labelled-reports document handed to the synthesis invocation."""
    lines = [
        "# Synthesis input: labelled leg reports",
        "",
        "Merge the labelled reviews below. Refer to legs only by invocation id.",
        "",
    ]
    for invocation_id, harness, review in legs:
        lines.append(f"### leg {invocation_id} harness {harness}")
        lines.append("```json")
        lines.append(review.model_dump_json(indent=2))
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def validate_synthesis(
    report: SynthesisReportV1, legs: Mapping[str, NormalizedReviewV1]
) -> list[AttributionV1]:
    """Check inputs/sources/agreement/disagreement integrity; return attribution."""
    problems: list[str] = []
    leg_ids = set(legs)
    if set(report.inputs) != leg_ids or len(report.inputs) != len(leg_ids):
        problems.append(
            f"inputs {sorted(report.inputs)} do not match the leg ids {sorted(leg_ids)}"
        )
    valid_pairs = {
        f"{leg_id}:{finding.id}" for leg_id, review in legs.items() for finding in review.findings
    }

    def check_sources(sources: Sequence[str], where: str) -> None:
        for source in sources:
            if source not in valid_pairs:
                problems.append(f"{where} references a non-existent source pair {source!r}")

    for finding in report.merged_findings:
        if not finding.sources:
            problems.append(f"merged finding {finding.id!r} has no sources")
        check_sources(finding.sources, f"merged finding {finding.id!r}")
    for agreement in report.agreements:
        check_sources(agreement.sources, f"agreement {agreement.title!r}")
        distinct_legs = {source.partition(":")[0] for source in agreement.sources}
        if len(distinct_legs) < 2:
            problems.append(
                f"agreement {agreement.title!r} is not an agreement: "
                f"fewer than two distinct legs assert it"
            )
    for disagreement in report.disagreements:
        for leg_id in (*disagreement.asserted_by, *disagreement.not_asserted_by):
            if leg_id not in leg_ids:
                problems.append(f"disagreement {disagreement.title!r} names unknown leg {leg_id!r}")
        overlap = set(disagreement.asserted_by) & set(disagreement.not_asserted_by)
        if overlap:
            problems.append(
                f"disagreement {disagreement.title!r} lists {sorted(overlap)} on both sides"
            )
        if not disagreement.asserted_by:
            problems.append(f"disagreement {disagreement.title!r} has an empty asserted_by")

    if problems:
        raise SynthesisValidationError("; ".join(problems))
    return [
        AttributionV1(merged_finding_id=finding.id, sources=list(finding.sources))
        for finding in report.merged_findings
    ]
