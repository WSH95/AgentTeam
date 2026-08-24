"""The tested redaction function (plan section 13): a run archive becomes a
reviewable sanitized bundle — records and reviews only, placeholder paths,
no raw streams, no render dumps, nothing value- or path-shaped left inside."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from agentteam.domain.bundle import BundleManifestV1
from agentteam.domain.common import RunStatus
from agentteam.domain.request import RunRequestV1
from agentteam.domain.review import NormalizedReviewV1
from agentteam.domain.run import HarnessInvocationV1, RunRecordV1, TimingV1
from agentteam.harness.types import RawInvocationV1
from agentteam.run.archive import RunArchive
from agentteam.run.events import EventLog
from agentteam.run.sanitize import SanitizeError, sanitize_run_archive, scan_sanitized

Payloads = dict[str, dict[str, Any]]


def _archive(tmp_path: Path, payloads: Payloads) -> RunArchive:
    request = dict(payloads["run-request-v1.schema.json"])
    request["assistant"] = str(tmp_path / "assistants" / "code-reviewer")
    request["workspace"] = str(tmp_path / "workspace")
    request["task_file"] = str(tmp_path / "task.md")
    request["output_dir"] = str(tmp_path / "archive")
    request["acceptance"] = {"oracle": str(tmp_path / "oracle.json")}
    archive, _ = RunArchive.create(
        tmp_path / "archive",
        run_record=RunRecordV1.model_validate(payloads["run-record-v1.schema.json"]),
        resolved_request=RunRequestV1.model_validate(request),
        bundle=BundleManifestV1.model_validate(payloads["bundle-manifest-v1.schema.json"]),
    )
    EventLog(archive.events_path, run_id="run-1").emit("run-created")
    invocation = HarnessInvocationV1.model_validate(payloads["harness-invocation-v1.schema.json"])
    finished = invocation.model_copy(
        update={
            "invocation_id": "inv-codex",
            "status": RunStatus.SUCCEEDED,
            "timing": TimingV1(
                started_at=datetime(2026, 8, 23, 12, 0, tzinfo=UTC),
                finished_at=datetime(2026, 8, 23, 12, 1, tzinfo=UTC),
                duration_ms=60_000,
            ),
        }
    )
    archive.write_invocation(finished)
    archive.write_raw_streams(
        "inv-codex",
        RawInvocationV1(
            exit_code=0,
            signal=None,
            stdout=b"raw stdout that must never publish",
            stderr=b"raw stderr",
            output_file_text='{"vendor": "output"}',
            timed_out=False,
            duration_ms=3,
        ),
    )
    archive.write_review(
        "inv-codex",
        NormalizedReviewV1.model_validate(payloads["normalized-review-v1.schema.json"]),
    )
    # a doctored render dump in the source proves the sanitizer excludes it
    (archive.leg_dir("inv-codex") / "invocation.render.json").write_text(
        '{"env_values": {"SECRET": "hunter2-sentinel"}}', encoding="utf-8"
    )
    workspace, _, _ = archive.working_dirs("inv-codex")
    (workspace / "target.ts").write_text("export const x = 1\n", encoding="utf-8")
    archive.finalize_manifest()
    return archive


def test_sanitized_bundle_has_records_and_none_of_the_raw_material(
    tmp_path: Path, payloads: Payloads
) -> None:
    archive = _archive(tmp_path, payloads)
    dest = tmp_path / "bundle"
    sanitize_run_archive(archive.root, dest)
    assert (dest / "run.json").is_file()
    assert (dest / "request.sanitized.json").is_file()
    assert (dest / "invocations" / "inv-codex.json").is_file()
    assert (dest / "reviews" / "inv-codex.json").is_file()
    assert (dest / "events.jsonl").is_file()
    assert (dest / "summary.md").is_file()
    assert (dest / "manifest.sha256.json").is_file()
    assert not list(dest.rglob("*.raw"))
    assert not list(dest.rglob("invocation.render.json"))
    assert not list(dest.rglob("output-file.json"))
    assert not list(dest.rglob("workspace"))


def test_request_paths_become_placeholders(tmp_path: Path, payloads: Payloads) -> None:
    archive = _archive(tmp_path, payloads)
    dest = tmp_path / "bundle"
    sanitize_run_archive(archive.root, dest)
    sanitized = json.loads((dest / "request.sanitized.json").read_text(encoding="utf-8"))
    assert sanitized["assistant"] == "<ASSISTANT>"
    assert sanitized["workspace"] == "<WORKSPACE>"
    assert sanitized["task_file"] == "<TASK_FILE>"
    assert sanitized["output_dir"] == "<OUTPUT_DIR>"
    assert sanitized["acceptance"]["oracle"] == "<ORACLE>"
    RunRequestV1.model_validate(sanitized)


def test_no_source_path_or_value_survives_in_the_bundle(tmp_path: Path, payloads: Payloads) -> None:
    archive = _archive(tmp_path, payloads)
    dest = tmp_path / "bundle"
    sanitize_run_archive(archive.root, dest)
    everything = "\n".join(
        path.read_text(encoding="utf-8") for path in dest.rglob("*") if path.is_file()
    )
    assert str(tmp_path) not in everything
    assert "hunter2-sentinel" not in everything
    assert "env_values" not in everything
    assert "raw stdout" not in everything
    assert scan_sanitized(dest) == []


def test_every_emitted_record_revalidates(tmp_path: Path, payloads: Payloads) -> None:
    archive = _archive(tmp_path, payloads)
    dest = tmp_path / "bundle"
    sanitize_run_archive(archive.root, dest)
    RunRecordV1.model_validate_json((dest / "run.json").read_text(encoding="utf-8"))
    HarnessInvocationV1.model_validate_json(
        (dest / "invocations" / "inv-codex.json").read_text(encoding="utf-8")
    )
    NormalizedReviewV1.model_validate_json(
        (dest / "reviews" / "inv-codex.json").read_text(encoding="utf-8")
    )


def test_summary_names_the_run_and_leg_statuses(tmp_path: Path, payloads: Payloads) -> None:
    archive = _archive(tmp_path, payloads)
    dest = tmp_path / "bundle"
    sanitize_run_archive(archive.root, dest)
    summary = (dest / "summary.md").read_text(encoding="utf-8")
    assert "run-1" in summary
    assert "inv-codex" in summary
    assert "succeeded" in summary


def test_destination_must_be_empty(tmp_path: Path, payloads: Payloads) -> None:
    archive = _archive(tmp_path, payloads)
    dest = tmp_path / "bundle"
    dest.mkdir()
    (dest / "existing.txt").write_text("here", encoding="utf-8")
    with pytest.raises(SanitizeError, match="not empty"):
        sanitize_run_archive(archive.root, dest)


def test_scan_flags_planted_leaks(tmp_path: Path) -> None:
    dest = tmp_path / "bundle"
    dest.mkdir()
    (dest / "bad.json").write_text('{"path": "/home/owner/secret"}', encoding="utf-8")
    problems = scan_sanitized(dest)
    assert problems
    assert any("bad.json" in problem for problem in problems)
    (dest / "bad.json").write_text('{"env_values": {}}', encoding="utf-8")
    assert scan_sanitized(dest)
