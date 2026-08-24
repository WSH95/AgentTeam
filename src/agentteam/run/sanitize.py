"""The tested redaction function (plan section 13).

`sanitize_run_archive` turns a local run archive into the reviewable bundle
that G8 commits under `docs/evidence/m1a-live-<date>/`: the run and ensemble
records, the redacted invocation records (typed-placeholder argv, environment
names only — redacted by construction), the normalized reviews, the synthesis
report, the event log, a placeholdered request, and a summary. Raw streams,
render dumps, working directories, and anything path- or value-shaped stay
local. The function fails closed: it scans its own output and raises when
anything absolute-path-shaped or value-shaped survives.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from agentteam.domain.review import NormalizedReviewV1, SynthesisReportV1
from agentteam.domain.run import EnsembleRecordV1, HarnessInvocationV1, RunRecordV1

_ABSOLUTE_IN_JSON = re.compile(r'"(?:/[^"\n]+|[A-Za-z]:\\\\[^"\n]+)"')

_PLACEHOLDERS = {
    "assistant": "<ASSISTANT>",
    "workspace": "<WORKSPACE>",
    "task_file": "<TASK_FILE>",
    "output_dir": "<OUTPUT_DIR>",
}


class SanitizeError(ValueError):
    """The sanitized bundle could not be produced safely."""


def _write(dest: Path, relative: str, text: str) -> None:
    path = dest / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _sanitize_request(text: str) -> str:
    payload: dict[str, Any] = json.loads(text)
    for key, placeholder in _PLACEHOLDERS.items():
        if isinstance(payload.get(key), str):
            payload[key] = placeholder
    acceptance = payload.get("acceptance")
    if isinstance(acceptance, dict) and isinstance(acceptance.get("oracle"), str):
        acceptance["oracle"] = "<ORACLE>"
    return json.dumps(payload, indent=2) + "\n"


def _summary(
    run: RunRecordV1,
    invocations: dict[str, HarnessInvocationV1],
    ensemble: EnsembleRecordV1 | None,
) -> str:
    lines = [
        "# Sanitized run summary",
        "",
        f"- run: `{run.run_id}` — {run.status.value}",
        f"- member: `{run.member.name}` (bundle `{run.member.effective_definition_hash[:12]}…`)",
    ]
    if run.failure_reason:
        lines.append(f"- failure reason: {run.failure_reason}")
    lines.append("")
    lines.append("## Invocations")
    lines.append("")
    for invocation_id in sorted(invocations):
        record = invocations[invocation_id]
        lines.append(
            f"- `{invocation_id}` ({record.requested.harness.value}): {record.status.value}, "
            f"attempt {record.retry.attempt}/{record.retry.max_attempts}, "
            f"schema {record.schema_outcome.value}"
        )
    if ensemble is not None:
        lines.append("")
        lines.append("## Acceptance")
        lines.append("")
        for tier_name, tier in (
            ("mechanical", ensemble.acceptance.mechanical),
            ("semantic", ensemble.acceptance.semantic),
        ):
            verdict = {True: "PASS", False: "FAIL", None: "not evaluated"}[tier.passed]
            lines.append(f"- {tier_name}: {verdict}")
            for condition in tier.conditions:
                state = {True: "pass", False: "FAIL", None: "n/a"}[condition.passed]
                lines.append(f"  - {condition.id}: {state}")
    lines.append("")
    return "\n".join(lines)


def scan_sanitized(dest: Path) -> list[str]:
    """Prove the bundle carries nothing value- or absolute-path-shaped."""
    problems: list[str] = []
    for path in sorted(dest.rglob("*")):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        name = path.relative_to(dest).as_posix()
        if "env_values" in text:
            problems.append(f"{name}: contains an env_values key")
        if path.suffix in (".json", ".jsonl") and _ABSOLUTE_IN_JSON.search(text):
            problems.append(f"{name}: contains an absolute-path-shaped string")
    return problems


def sanitize_run_archive(root: Path, dest: Path) -> None:
    if dest.exists() and any(dest.iterdir()):
        raise SanitizeError(f"sanitized bundle destination is not empty: {dest}")
    dest.mkdir(parents=True, exist_ok=True)

    run = RunRecordV1.model_validate_json((root / "run.json").read_text(encoding="utf-8"))
    _write(dest, "run.json", run.model_dump_json(indent=2) + "\n")
    _write(
        dest,
        "request.sanitized.json",
        _sanitize_request((root / "request.resolved.json").read_text(encoding="utf-8")),
    )

    ensemble: EnsembleRecordV1 | None = None
    if (root / "ensemble.json").is_file():
        ensemble = EnsembleRecordV1.model_validate_json(
            (root / "ensemble.json").read_text(encoding="utf-8")
        )
        _write(dest, "ensemble.json", ensemble.model_dump_json(indent=2) + "\n")
    if (root / "synthesis-report.json").is_file():
        report = SynthesisReportV1.model_validate_json(
            (root / "synthesis-report.json").read_text(encoding="utf-8")
        )
        _write(dest, "synthesis-report.json", report.model_dump_json(indent=2) + "\n")

    invocations: dict[str, HarnessInvocationV1] = {}
    for group in ("legs", "synthesis"):
        group_dir = root / group
        if not group_dir.is_dir():
            continue
        for leg_dir in sorted(group_dir.iterdir()):
            record_path = leg_dir / "invocation.json"
            if not record_path.is_file():
                continue
            record = HarnessInvocationV1.model_validate_json(
                record_path.read_text(encoding="utf-8")
            )
            invocations[record.invocation_id] = record
            _write(
                dest,
                f"invocations/{record.invocation_id}.json",
                record.model_dump_json(indent=2) + "\n",
            )
            review_path = leg_dir / "review.normalized.json"
            if review_path.is_file():
                review = NormalizedReviewV1.model_validate_json(
                    review_path.read_text(encoding="utf-8")
                )
                _write(
                    dest,
                    f"reviews/{record.invocation_id}.json",
                    review.model_dump_json(indent=2) + "\n",
                )

    if (root / "events.jsonl").is_file():
        _write(dest, "events.jsonl", (root / "events.jsonl").read_text(encoding="utf-8"))

    _write(dest, "summary.md", _summary(run, invocations, ensemble))

    problems = scan_sanitized(dest)
    if problems:
        raise SanitizeError("sanitized bundle failed its own scan: " + "; ".join(problems))

    manifest = {
        "files": [
            {
                "path": path.relative_to(dest).as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            for path in sorted(dest.rglob("*"))
            if path.is_file() and path.name != "manifest.sha256.json"
        ]
    }
    _write(dest, "manifest.sha256.json", json.dumps(manifest, indent=2) + "\n")
