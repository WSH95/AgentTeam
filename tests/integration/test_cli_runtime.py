"""Runtime CLI never installs implicitly and doctor makes zero calls."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentteam.cli import app
from agentteam.domain.common import HarnessId
from agentteam.domain.interactive import (
    DoctorCheckV1,
    LiveEvidenceRefV1,
    LiveLifecycleProofsV1,
    ProviderDoctorV1,
    ProviderLiveAttestationV1,
)
from agentteam.execution import direct_acp
from agentteam.interactive.live_qualification import DirectAcpLiveQualificationResult

runner = CliRunner()


def test_runtime_doctor_reports_uninstalled_without_installing(tmp_path: Path) -> None:
    env = {"AGENTTEAM_HOME": str(tmp_path)}
    result = runner.invoke(app, ["runtime", "doctor", "direct-acp", "--json"], env=env)
    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert payload["status"] == "unsupported"
    assert payload["model_calls"] == 0


def test_runtime_rejects_unknown_id() -> None:
    result = runner.invoke(app, ["runtime", "doctor", "other"])
    assert result.exit_code == 2
    assert "unknown runtime" in result.output


def _live_target(tmp_path: Path) -> direct_acp.DirectAcpQualificationTarget:
    return direct_acp.DirectAcpQualificationTarget(
        harness=HarnessId.CODEX,
        runtime_path=tmp_path / "runtime",
        command=("node", "agent.mjs"),
        environment={},
        native_version="codex 1.2.3",
        expected_version="codex 1.2.3",
        config_home_variable="CODEX_HOME",
        config_home=tmp_path / "codex-home",
        fingerprint="a" * 64,
    )


def _staged_report() -> ProviderDoctorV1:
    return ProviderDoctorV1(
        schema_version=1,
        kind="provider-doctor",
        provider=direct_acp.RUNTIME_ID,
        checked_at=datetime(2026, 8, 25, tzinfo=UTC),
        status="pass",
        capabilities=direct_acp._direct_capabilities(qualified=True),
        checks=[DoctorCheckV1(name="codex-acp-lifecycle", status="pass")],
        model_calls=0,
    )


def _passing_result(tmp_path: Path) -> DirectAcpLiveQualificationResult:
    proofs = LiveLifecycleProofsV1(
        context_established=True,
        strict_post_turn_resume=True,
        recall=True,
        reset_isolation=True,
        new_run_isolation=True,
        continuity_close=True,
    )
    attestation = ProviderLiveAttestationV1(
        schema_version=1,
        kind="provider-live-attestation",
        provider=direct_acp.RUNTIME_ID,
        harness=HarnessId.CODEX,
        target_fingerprint="a" * 64,
        runtime_lock_hash=direct_acp.runtime_lock_hash(),
        native_version="codex 1.2.3",
        platform=sys.platform,
        status="pass",
        attempted_prompts=5,
        proofs=proofs,
        evidence=[
            LiveEvidenceRefV1(run_id="run-live-1", manifest_sha256="b" * 64),
            LiveEvidenceRefV1(run_id="run-live-2", manifest_sha256="c" * 64),
        ],
        checked_at=datetime(2026, 8, 25, tzinfo=UTC),
    )
    return DirectAcpLiveQualificationResult(
        attestation=attestation,
        path=tmp_path / "attestation.json",
    )


def test_runtime_live_qualification_requires_one_attended_confirmed_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    target = _live_target(tmp_path)
    report = _staged_report()
    monkeypatch.setattr(
        "agentteam.commands.runtime._qualification_targets",
        lambda **_kwargs: ((target,), {}),
    )
    monkeypatch.setattr(
        "agentteam.commands.runtime.load_direct_acp_qualification",
        lambda *_args, **_kwargs: (report, []),
    )

    async def fake_runner(*_args: object, **_kwargs: object) -> object:
        calls.append("run")
        return _passing_result(tmp_path)

    monkeypatch.setattr("agentteam.commands.runtime._run_live_qualification", fake_runner)
    monkeypatch.setattr("agentteam.commands.runtime._is_attended", lambda: True)
    monkeypatch.setattr(
        "agentteam.commands.runtime._confirm_live_qualification",
        lambda _harness: False,
    )

    missing = runner.invoke(app, ["runtime", "qualify-live", "direct-acp"])
    assert missing.exit_code == 2
    multiple = runner.invoke(
        app,
        [
            "runtime",
            "qualify-live",
            "direct-acp",
            "--harness",
            "codex",
            "--harness",
            "grok",
        ],
    )
    assert multiple.exit_code == 2
    declined = runner.invoke(
        app,
        ["runtime", "qualify-live", "direct-acp", "--harness", "codex", "--json"],
    )
    assert declined.exit_code == 130
    assert json.loads(declined.stdout)["attempted_prompts"] == 0
    assert calls == []


def test_runtime_live_qualification_runs_only_after_fresh_confirmation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    target = _live_target(tmp_path)
    report = _staged_report()
    monkeypatch.setattr(
        "agentteam.commands.runtime._qualification_targets",
        lambda **_kwargs: ((target,), {}),
    )
    monkeypatch.setattr(
        "agentteam.commands.runtime.load_direct_acp_qualification",
        lambda *_args, **_kwargs: (report, []),
    )
    monkeypatch.setattr("agentteam.commands.runtime._is_attended", lambda: True)
    monkeypatch.setattr(
        "agentteam.commands.runtime._confirm_live_qualification",
        lambda _harness: True,
    )

    async def fake_runner(*_args: object, **_kwargs: object) -> object:
        calls.append("run")
        return _passing_result(tmp_path)

    monkeypatch.setattr("agentteam.commands.runtime._run_live_qualification", fake_runner)
    result = runner.invoke(
        app,
        ["runtime", "qualify-live", "direct-acp", "--harness", "codex", "--json"],
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["attempted_prompts"] == 5
    assert calls == ["run"]


def test_runtime_live_qualification_rejects_stale_staging_and_non_tty(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = _live_target(tmp_path)
    monkeypatch.setattr(
        "agentteam.commands.runtime._qualification_targets",
        lambda **_kwargs: ((target,), {}),
    )
    monkeypatch.setattr(
        "agentteam.commands.runtime.load_direct_acp_qualification",
        lambda *_args, **_kwargs: (None, ["qualification fingerprint is stale"]),
    )
    stale = runner.invoke(
        app,
        ["runtime", "qualify-live", "direct-acp", "--harness", "codex"],
    )
    assert stale.exit_code == 1
    assert "current no-call qualification is required" in stale.output

    monkeypatch.setattr(
        "agentteam.commands.runtime.load_direct_acp_qualification",
        lambda *_args, **_kwargs: (_staged_report(), []),
    )
    monkeypatch.setattr("agentteam.commands.runtime._is_attended", lambda: False)
    unattended = runner.invoke(
        app,
        ["runtime", "qualify-live", "direct-acp", "--harness", "codex"],
    )
    assert unattended.exit_code == 1
    assert "requires an attended TTY" in unattended.output
