"""Deterministic direct-harness acceptance (plan sections 12, 14, 15).

Every test drives the real CLI with the committed example request, the
committed review target and oracle, and the deterministic fakes — both
acceptance tiers evaluated, exit codes 0/1/3 exercised, the archive
reconstructed, the sanitized bundle produced, and cancellation finalized.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest
import yaml
from typer.testing import CliRunner

from agentteam.cli import app
from agentteam.run.archive import RunArchive
from agentteam.run.sanitize import sanitize_run_archive, scan_sanitized

runner = CliRunner()
REPO_ROOT = Path(__file__).resolve().parents[2]
DIRECT_REQUEST = REPO_ROOT / "examples" / "run-requests" / "direct-review.yaml"
CI_FAKE = REPO_ROOT / "examples" / "profiles" / "ci-fake.yaml"


def _invoke(out: Path, env: dict[str, str] | None = None, request: Path = DIRECT_REQUEST) -> Any:
    return runner.invoke(
        app,
        ["run", str(request), "--config", str(CI_FAKE), "--output-dir", str(out)],
        env={"FAKE_MODE": "ok", **(env or {})},
    )


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _tmp_request(tmp_path: Path, **overrides: Any) -> Path:
    request: dict[str, Any] = {
        "schema_version": 1,
        "kind": "run-request",
        "mode": "direct",
        "assistant": str(REPO_ROOT / "examples" / "assistants" / "code-reviewer"),
        "workspace": str(REPO_ROOT / "fixtures" / "review-target"),
        "task_file": str(REPO_ROOT / "examples" / "run-requests" / "review-task.md"),
    }
    request.update(overrides)
    path = tmp_path / "request.yaml"
    path.write_text(yaml.safe_dump(request), encoding="utf-8")
    return path


def test_deterministic_acceptance_passes_both_tiers(tmp_path: Path) -> None:
    out = tmp_path / "run"
    result = _invoke(out)
    assert result.exit_code == 0, result.output
    ensemble = _load(out / "ensemble.json")
    mechanical = ensemble["acceptance"]["mechanical"]
    semantic = ensemble["acceptance"]["semantic"]
    assert mechanical["passed"] is True
    assert [c["id"] for c in mechanical["conditions"]] == ["cond-1", "cond-6", "cond-7", "cond-8"]
    assert semantic["passed"] is True
    assert [c["id"] for c in semantic["conditions"]] == [
        "cond-2",
        "cond-3",
        "cond-4",
        "cond-5",
        "cond-9",
    ]
    assert ensemble["attribution"]
    for harness in ("claude-code", "codex", "grok"):
        leg = _load(out / "legs" / f"inv-{harness}" / "invocation.json")
        assert leg["selection"]["decided_by"] == "user"
        skill_parts = [
            part["part"] for part in leg["injection"]["render"] if part["part"].startswith("skill:")
        ]
        assert sorted(skill_parts) == [
            "skill:code-review",
            "skill:security-review",
            "skill:test-analysis",
        ]
    assert RunArchive(out).verify_manifest() == []


def test_solo_variant_records_an_invocation_binding(tmp_path: Path) -> None:
    out = tmp_path / "run"
    request = _tmp_request(tmp_path)
    result = _invoke(out, request=request)
    assert result.exit_code == 0, result.output
    run = _load(out / "run.json")
    assert run["member"]["execution"]["kind"] == "invocation"
    assert not (out / "ensemble.json").exists()
    leg = _load(out / "legs" / "inv-claude-code" / "invocation.json")
    assert leg["selection"]["decided_by"] == "assistant"


def test_no_synthesis_leaves_cond_5_unevaluated(tmp_path: Path) -> None:
    out = tmp_path / "run"
    result = runner.invoke(
        app,
        [
            "run",
            str(DIRECT_REQUEST),
            "--config",
            str(CI_FAKE),
            "--output-dir",
            str(out),
            "--no-synthesis",
        ],
        env={"FAKE_MODE": "ok"},
    )
    assert result.exit_code == 0, result.output
    ensemble = _load(out / "ensemble.json")
    assert ensemble["synthesis"]["invocation_id"] is None
    conditions = {c["id"]: c for c in ensemble["acceptance"]["semantic"]["conditions"]}
    assert conditions["cond-5"]["passed"] is None
    assert ensemble["acceptance"]["semantic"]["passed"] is None


def test_semantic_miss_exits_3_with_valid_mechanics(tmp_path: Path) -> None:
    out = tmp_path / "run"
    result = _invoke(out, env={"FAKE_MODE": "semantic-miss"})
    assert result.exit_code == 3, result.output
    ensemble = _load(out / "ensemble.json")
    assert ensemble["acceptance"]["mechanical"]["passed"] is True
    semantic = ensemble["acceptance"]["semantic"]
    assert semantic["passed"] is False
    conditions = {c["id"]: c for c in semantic["conditions"]}
    assert conditions["cond-2"]["passed"] is False
    assert conditions["cond-3"]["passed"] is False


def test_invented_critical_exits_3_via_cond_4(tmp_path: Path) -> None:
    out = tmp_path / "run"
    result = _invoke(out, env={"FAKE_MODE_CODEX": "invent-critical"})
    assert result.exit_code == 3, result.output
    ensemble = _load(out / "ensemble.json")
    conditions = {c["id"]: c for c in ensemble["acceptance"]["semantic"]["conditions"]}
    assert conditions["cond-4"]["passed"] is False
    assert "f9" in (conditions["cond-4"]["detail"] or "")


def test_target_mutation_exits_1_before_any_semantic_verdict(tmp_path: Path) -> None:
    out = tmp_path / "run"
    result = _invoke(out, env={"FAKE_MODE_GROK": "mutate-target"})
    assert result.exit_code == 1
    ensemble = _load(out / "ensemble.json")
    assert ensemble["acceptance"]["mechanical"]["passed"] is False
    run = _load(out / "run.json")
    assert run["status"] == "failed"


def test_the_cycle_stays_inside_the_eight_call_budget(tmp_path: Path) -> None:
    out = tmp_path / "run"
    result = _invoke(out, env={"FAKE_MODE_CLAUDE": "rate-limit-once"})
    assert result.exit_code == 0, result.output
    attempts = 0
    for group in ("legs", "synthesis"):
        for record_path in (out / group).rglob("invocation.json"):
            attempts += int(_load(record_path)["retry"]["attempt"])
    # claude leg 2 (rate-limited once) + codex 1 + grok 1 + synthesis 2 (the
    # synthesis config home is fresh, so its claude fake rate-limits once too)
    assert attempts == 6
    assert attempts <= 8  # the section-12 cycle budget


def test_without_an_oracle_the_semantic_tier_stays_unevaluated(tmp_path: Path) -> None:
    out = tmp_path / "run"
    request = _tmp_request(
        tmp_path,
        harnesses=["claude-code", "codex", "grok"],
        synthesis={"enabled": True, "harness": "claude-code"},
    )
    result = _invoke(out, request=request)
    assert result.exit_code == 0, result.output
    ensemble = _load(out / "ensemble.json")
    assert ensemble["acceptance"]["mechanical"]["passed"] is True
    assert ensemble["acceptance"]["semantic"]["passed"] is None


def test_sanitized_bundle_round_trip_from_a_real_run(tmp_path: Path) -> None:
    out = tmp_path / "run"
    result = _invoke(out)
    assert result.exit_code == 0, result.output
    dest = tmp_path / "bundle"
    sanitize_run_archive(out, dest)
    assert scan_sanitized(dest) == []
    assert (dest / "ensemble.json").is_file()
    assert (dest / "synthesis-report.json").is_file()
    assert len(list((dest / "invocations").glob("*.json"))) == 4
    everything = "\n".join(
        path.read_text(encoding="utf-8") for path in dest.rglob("*") if path.is_file()
    )
    assert str(out) not in everything


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permission bits")
def test_archive_permissions_are_owner_only(tmp_path: Path) -> None:
    out = tmp_path / "run"
    result = _invoke(out)
    assert result.exit_code == 0, result.output
    assert out.stat().st_mode & 0o777 == 0o700
    for path in (out / "legs").rglob("invocation.json"):
        assert path.stat().st_mode & 0o777 == 0o600


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX signal semantics")
def test_sigint_finalizes_cancelled_records_and_exits_130(tmp_path: Path) -> None:
    out = tmp_path / "run"
    request = _tmp_request(tmp_path, harnesses=["claude-code"])
    script = (
        "import sys; from agentteam.cli import main; "
        "sys.argv = ['atm', 'run', *sys.argv[1:]]; main()"
    )
    with subprocess.Popen(
        [
            sys.executable,
            "-c",
            script,
            str(request),
            "--config",
            str(CI_FAKE),
            "--output-dir",
            str(out),
        ],
        env={**os.environ, "FAKE_MODE": "hang"},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as process:
        try:
            leg_record = out / "legs" / "inv-claude-code" / "invocation.json"
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline and not leg_record.is_file():
                time.sleep(0.1)
            assert leg_record.is_file(), "pending record never appeared"
            time.sleep(0.4)
            process.send_signal(signal.SIGINT)
            process.communicate(timeout=25)
        except BaseException:
            process.kill()
            process.communicate(timeout=10)
            raise
        returncode = process.returncode
    assert returncode == 130
    run = _load(out / "run.json")
    assert run["status"] == "cancelled"
    leg = _load(leg_record)
    assert leg["status"] == "cancelled"
    assert (out / "manifest.sha256.json").is_file()
