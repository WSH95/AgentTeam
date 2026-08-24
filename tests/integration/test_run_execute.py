"""`atm run` end-to-end over the deterministic fakes (plan section 12).

These tests drive the real CLI: pending-first archives, concurrent legs, the
single transient retry, synthesis over labelled reports, mechanical
acceptance, and the stable exit codes. The oracle-driven semantic tier rides
the example request in `tests/acceptance/`.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml
from typer.testing import CliRunner

from agentteam.cli import app
from agentteam.run.synthesis import instruction_hash

runner = CliRunner()
REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = REPO_ROOT / "examples" / "assistants" / "code-reviewer"
CI_FAKE = REPO_ROOT / "examples" / "profiles" / "ci-fake.yaml"
EMPTY_TREE = hashlib.sha256(b"").hexdigest()
ALL_HARNESSES = ["--harness", "claude-code", "--harness", "codex", "--harness", "grok"]


def _args(tmp_path: Path, out: Path) -> list[str]:
    workspace = tmp_path / "ws"
    workspace.mkdir(exist_ok=True)
    (workspace / "target.ts").write_text("export const x = 1\n", encoding="utf-8")
    task = tmp_path / "task.md"
    task.write_text("Review target.ts.\n", encoding="utf-8")
    return [
        "run",
        "--assistant",
        str(EXAMPLE),
        "--workspace",
        str(workspace),
        "--task-file",
        str(task),
        "--config",
        str(CI_FAKE),
        "--output-dir",
        str(out),
    ]


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_full_ensemble_run_succeeds_with_a_complete_archive(tmp_path: Path) -> None:
    out = tmp_path / "run"
    result = runner.invoke(app, [*_args(tmp_path, out), *ALL_HARNESSES], env={"FAKE_MODE": "ok"})
    assert result.exit_code == 0, result.output
    run = _load(out / "run.json")
    assert run["status"] == "succeeded"
    assert run["member"]["execution"] == {"kind": "ensemble", "ref": "ens-1"}
    for harness in ("claude-code", "codex", "grok"):
        leg = _load(out / "legs" / f"inv-{harness}" / "invocation.json")
        assert leg["status"] == "succeeded"
        assert leg["target"]["after"] == leg["target"]["before"]
        assert (out / "legs" / f"inv-{harness}" / "review.normalized.json").is_file()
    ensemble = _load(out / "ensemble.json")
    assert sorted(ensemble["legs"]) == ["inv-claude-code", "inv-codex", "inv-grok"]
    assert ensemble["synthesis"]["invocation_id"] == "inv-synthesis"
    assert sorted(ensemble["synthesis"]["inputs"]) == sorted(ensemble["legs"])
    assert ensemble["synthesis"]["instruction_hash"] == instruction_hash()
    assert ensemble["acceptance"]["mechanical"]["passed"] is True
    assert ensemble["acceptance"]["semantic"]["passed"] is None  # no oracle here
    assert ensemble["attribution"]
    assert (out / "synthesis-report.json").is_file()
    assert (out / "manifest.sha256.json").is_file()
    events = [
        json.loads(line) for line in (out / "events.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    names = [event["event"] for event in events]
    assert names[0] == "run-created"
    assert "run-finished" in names


def test_solo_run_binds_one_invocation_and_skips_synthesis(tmp_path: Path) -> None:
    out = tmp_path / "run"
    result = runner.invoke(app, _args(tmp_path, out), env={"FAKE_MODE": "ok"})
    assert result.exit_code == 0, result.output
    run = _load(out / "run.json")
    assert run["member"]["execution"] == {"kind": "invocation", "ref": "inv-claude-code"}
    assert not (out / "ensemble.json").exists()
    assert not (out / "synthesis").exists()
    leg = _load(out / "legs" / "inv-claude-code" / "invocation.json")
    assert leg["selection"]["decided_by"] == "assistant"


def test_transient_retry_recovers_and_is_recorded(tmp_path: Path) -> None:
    out = tmp_path / "run"
    result = runner.invoke(
        app,
        [*_args(tmp_path, out), *ALL_HARNESSES],
        env={"FAKE_MODE": "ok", "FAKE_MODE_CLAUDE": "rate-limit-once"},
    )
    assert result.exit_code == 0, result.output
    leg = _load(out / "legs" / "inv-claude-code" / "invocation.json")
    assert leg["retry"]["attempt"] == 2
    assert leg["retry"]["classification"] == "transient"
    assert leg["status"] == "succeeded"


def test_persistent_rate_limit_fails_after_the_single_retry(tmp_path: Path) -> None:
    out = tmp_path / "run"
    result = runner.invoke(
        app,
        [*_args(tmp_path, out), *ALL_HARNESSES],
        env={"FAKE_MODE": "ok", "FAKE_MODE_CODEX": "rate-limit"},
    )
    assert result.exit_code == 1
    leg = _load(out / "legs" / "inv-codex" / "invocation.json")
    assert leg["status"] == "failed"
    assert leg["retry"]["attempt"] == 2
    run = _load(out / "run.json")
    assert run["status"] == "failed"
    assert "codex" in (run["failure_reason"] or "")
    assert not (out / "synthesis-report.json").exists()


def test_schema_failure_is_never_retried(tmp_path: Path) -> None:
    out = tmp_path / "run"
    result = runner.invoke(
        app,
        [*_args(tmp_path, out), *ALL_HARNESSES],
        env={"FAKE_MODE": "ok", "FAKE_MODE_CODEX": "malformed"},
    )
    assert result.exit_code == 1
    leg = _load(out / "legs" / "inv-codex" / "invocation.json")
    assert leg["status"] == "failed"
    assert leg["retry"]["attempt"] == 1
    assert leg["schema_outcome"] == "missing"
    assert not (out / "synthesis").exists()


def test_target_mutation_is_a_mechanical_failure(tmp_path: Path) -> None:
    out = tmp_path / "run"
    result = runner.invoke(
        app,
        [*_args(tmp_path, out), *ALL_HARNESSES],
        env={"FAKE_MODE": "ok", "FAKE_MODE_GROK": "mutate-target"},
    )
    assert result.exit_code == 1
    leg = _load(out / "legs" / "inv-grok" / "invocation.json")
    assert leg["target"]["after"] != leg["target"]["before"]
    run = _load(out / "run.json")
    assert run["status"] == "failed"
    assert "grok" in (run["failure_reason"] or "")
    ensemble = _load(out / "ensemble.json")
    assert ensemble["acceptance"]["mechanical"]["passed"] is False


def test_occupied_output_dir_exits_2_and_is_untouched(tmp_path: Path) -> None:
    out = tmp_path / "run"
    out.mkdir()
    stray = out / "precious.txt"
    stray.write_text("do not clobber", encoding="utf-8")
    result = runner.invoke(app, _args(tmp_path, out), env={"FAKE_MODE": "ok"})
    assert result.exit_code == 2
    assert stray.read_text(encoding="utf-8") == "do not clobber"
    assert not (out / "run.json").exists()


def test_hang_times_out_with_the_pending_archive_on_disk(tmp_path: Path) -> None:
    out = tmp_path / "run"
    workspace = tmp_path / "ws"
    workspace.mkdir()
    (workspace / "target.ts").write_text("export const x = 1\n", encoding="utf-8")
    task = tmp_path / "task.md"
    task.write_text("Review.\n", encoding="utf-8")
    request = {
        "schema_version": 1,
        "kind": "run-request",
        "mode": "direct",
        "assistant": str(EXAMPLE),
        "workspace": str(workspace),
        "task_file": str(task),
        "output_dir": str(out),
        "limits": {"attempt_seconds": 1, "transient_retries": 0},
    }
    request_file = tmp_path / "request.yaml"
    request_file.write_text(yaml.safe_dump(request), encoding="utf-8")
    result = runner.invoke(
        app, ["run", str(request_file), "--config", str(CI_FAKE)], env={"FAKE_MODE": "hang"}
    )
    assert result.exit_code == 1
    leg = _load(out / "legs" / "inv-claude-code" / "invocation.json")
    assert leg["status"] == "timed-out"
    events = [
        json.loads(line) for line in (out / "events.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    names = [event["event"] for event in events]
    assert names.index("run-created") < names.index("leg-started")


def test_synthesis_leg_runs_over_an_empty_workspace(tmp_path: Path) -> None:
    out = tmp_path / "run"
    result = runner.invoke(app, [*_args(tmp_path, out), *ALL_HARNESSES], env={"FAKE_MODE": "ok"})
    assert result.exit_code == 0, result.output
    synthesis = _load(out / "synthesis" / "inv-synthesis" / "invocation.json")
    assert synthesis["target"]["before"] == EMPTY_TREE
    assert synthesis["target"]["after"] == EMPTY_TREE
    assert (
        (out / "synthesis" / "inv-synthesis" / "task.md")
        .read_text(encoding="utf-8")
        .startswith("# Synthesis input")
    )


def test_no_env_values_key_in_any_archived_record(tmp_path: Path) -> None:
    out = tmp_path / "run"
    result = runner.invoke(app, [*_args(tmp_path, out), *ALL_HARNESSES], env={"FAKE_MODE": "ok"})
    assert result.exit_code == 0, result.output
    for path in out.rglob("*.json"):
        assert '"env_values"' not in path.read_text(encoding="utf-8"), path


def test_events_carry_no_absolute_paths(tmp_path: Path) -> None:
    out = tmp_path / "run"
    result = runner.invoke(app, [*_args(tmp_path, out), *ALL_HARNESSES], env={"FAKE_MODE": "ok"})
    assert result.exit_code == 0, result.output
    for line in (out / "events.jsonl").read_text(encoding="utf-8").splitlines():
        payload = json.loads(line)
        for value in payload.values():
            if isinstance(value, str):
                assert not value.startswith("/")
                assert ":\\" not in value


def test_cancel_finalizer_marks_records_cancelled(tmp_path: Path, payloads: Any) -> None:
    from datetime import UTC, datetime

    from agentteam.domain.bundle import BundleManifestV1
    from agentteam.domain.request import RunRequestV1
    from agentteam.domain.run import HarnessInvocationV1, RunRecordV1
    from agentteam.run.archive import RunArchive
    from agentteam.run.events import EventLog
    from agentteam.run.runner import finalize_cancelled

    archive, _ = RunArchive.create(
        tmp_path / "archive",
        run_record=RunRecordV1.model_validate(payloads["run-record-v1.schema.json"]),
        resolved_request=RunRequestV1.model_validate(payloads["run-request-v1.schema.json"]),
        bundle=BundleManifestV1.model_validate(payloads["bundle-manifest-v1.schema.json"]),
    )
    pending_leg = HarnessInvocationV1.model_validate(
        payloads["harness-invocation-v1.schema.json"]
    ).model_copy(update={"invocation_id": "inv-codex"})
    archive.write_invocation(pending_leg)
    events = EventLog(archive.events_path, run_id="run-1")
    finalize_cancelled(
        archive,
        run_record=RunRecordV1.model_validate(payloads["run-record-v1.schema.json"]),
        invocations=[pending_leg],
        events=events,
    )
    run = _load(archive.root / "run.json")
    assert run["status"] == "cancelled"
    assert run["timing"]["finished_at"] is not None
    leg = _load(archive.root / "legs" / "inv-codex" / "invocation.json")
    assert leg["status"] == "cancelled"
    assert (archive.root / "manifest.sha256.json").is_file()
    started = datetime.fromisoformat(run["timing"]["finished_at"])
    assert started.tzinfo is not None and datetime.now(tz=UTC) >= started
