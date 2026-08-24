"""Pending-first probe capture persistence."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from agentteam.harness.types import RawInvocationV1
from agentteam.profile.capture import ProbeCapture


def test_probe_capture_is_pending_before_raw_evidence_and_terminal_after(tmp_path: Path) -> None:
    now = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)
    capture = ProbeCapture.create(tmp_path / "profiles.yaml", now=now)
    call = capture.begin_call(
        "codex",
        1,
        command={"argv_redacted": ["<LAUNCHER>", "exec"]},
        started_at=now,
    )
    pending = json.loads((call / "manifest.json").read_text())
    assert pending["status"] == "pending"
    assert not (call / "stdout.raw").exists()

    raw = RawInvocationV1(
        exit_code=0,
        signal=None,
        stdout=b"{}\n",
        stderr=b"",
        output_file_text="{}",
        timed_out=False,
        duration_ms=2,
        started_at=now,
        finished_at=now,
    )
    capture.finish_call(
        call,
        raw=raw,
        status="succeeded",
        sanitized_result={"status": "passed"},
    )
    terminal = json.loads((call / "manifest.json").read_text())
    assert terminal["status"] == "succeeded"
    assert {item["path"] for item in terminal["artifacts"]} == {
        "stdout.raw",
        "stderr.raw",
        "output-file.raw",
        "result.sanitized.json",
        "command.redacted.json",
    }
