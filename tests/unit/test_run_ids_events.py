"""Run/invocation/ensemble id minting and the archive event log (plan section 13)."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import TypeAdapter

from agentteam.domain.common import EnsembleId, HarnessId, InvocationId, RunId
from agentteam.run.events import EventLog
from agentteam.run.ids import (
    ENSEMBLE_ID,
    SYNTHESIS_INVOCATION_ID,
    leg_invocation_id,
    new_run_id,
)


def test_new_run_id_matches_pattern_and_is_windows_safe() -> None:
    run_id = new_run_id()
    TypeAdapter(RunId).validate_python(run_id)
    assert ":" not in run_id
    assert run_id == run_id.lower()


def test_new_run_id_embeds_utc_stamp_and_varies() -> None:
    fixed = datetime(2026, 8, 23, 12, 0, 0, tzinfo=UTC)
    first = new_run_id(fixed)
    second = new_run_id(fixed)
    assert first.startswith("run-20260823-120000-")
    assert second.startswith("run-20260823-120000-")
    assert first != second


def test_leg_synthesis_and_ensemble_ids_match_domain_patterns() -> None:
    invocation_ids = TypeAdapter(InvocationId)
    for harness in HarnessId:
        leg = leg_invocation_id(harness)
        invocation_ids.validate_python(leg)
        assert leg == f"inv-{harness.value}"
    invocation_ids.validate_python(SYNTHESIS_INVOCATION_ID)
    TypeAdapter(EnsembleId).validate_python(ENSEMBLE_ID)


def test_event_log_appends_one_json_line_per_event(tmp_path: Path) -> None:
    log = EventLog(tmp_path / "events.jsonl", run_id="run-test")
    log.emit("run-created")
    log.emit("leg-started", invocation_id="inv-codex", detail="attempt 1")
    lines = (tmp_path / "events.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    first, second = (json.loads(line) for line in lines)
    assert first["event"] == "run-created"
    assert first["run_id"] == "run-test"
    assert set(first) <= {"ts", "event", "run_id", "invocation_id", "detail"}
    assert second["invocation_id"] == "inv-codex"
    assert second["detail"] == "attempt 1"


def test_event_timestamps_are_aware_utc(tmp_path: Path) -> None:
    log = EventLog(tmp_path / "events.jsonl", run_id="run-test")
    log.emit("run-created")
    payload = json.loads((tmp_path / "events.jsonl").read_text(encoding="utf-8"))
    stamp = datetime.fromisoformat(payload["ts"])
    offset = stamp.utcoffset()
    assert offset is not None
    assert offset.total_seconds() == 0


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permission bits")
def test_event_log_creates_the_file_owner_only(tmp_path: Path) -> None:
    # G6.R3: `events.jsonl` is 0600 from its very first byte, even under the
    # most permissive umask.
    previous = os.umask(0o000)
    try:
        EventLog(tmp_path / "events.jsonl", run_id="run-test").emit("run-created")
    finally:
        os.umask(previous)
    assert (tmp_path / "events.jsonl").stat().st_mode & 0o777 == 0o600


async def test_event_log_is_safe_under_concurrent_emitters(tmp_path: Path) -> None:
    log = EventLog(tmp_path / "events.jsonl", run_id="run-test")

    async def emitter(tag: str) -> None:
        for index in range(25):
            log.emit("tick", detail=f"{tag}-{index}")
            await asyncio.sleep(0)

    await asyncio.gather(*(emitter(tag) for tag in ("a", "b", "c")))
    lines = (tmp_path / "events.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 75
    payloads = [json.loads(line) for line in lines]
    assert all(item["event"] == "tick" for item in payloads)
    assert {item["detail"] for item in payloads} == {
        f"{tag}-{index}" for tag in ("a", "b", "c") for index in range(25)
    }
