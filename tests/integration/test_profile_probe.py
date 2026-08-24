"""Deterministic attended native-auth doctor probes; no vendor/model calls."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any

import pytest
from click import Abort
from typer.testing import CliRunner

from agentteam.cli import app
from agentteam.domain.common import HarnessId
from agentteam.domain.profile import CapabilityRecordV1, Verification
from agentteam.profile.probe import _PROBE_SCHEMA, _TASK, ProbeCancelled, run_attended_probes
from agentteam.resolution.profiles import (
    load_profile_set,
    resolve_profile_executable,
    write_profile_set,
)

runner = CliRunner()
REPO_ROOT = Path(__file__).resolve().parents[2]
CI_FAKE = REPO_ROOT / "examples" / "profiles" / "ci-fake.yaml"
VERSIONS = {
    HarnessId.CLAUDE_CODE: "2.1.241 (Claude Code)",
    HarnessId.CODEX: "codex-cli 0.149.0",
    HarnessId.GROK: "grok 1.0.5 (fake)",
}


def _profile_path(tmp_path: Path, *, timeout: int = 10) -> Path:
    source = load_profile_set(CI_FAKE)
    profiles = []
    for profile in source.profiles:
        executable = resolve_profile_executable(CI_FAKE, profile.executable)
        capabilities = [
            row.model_copy(
                update={
                    "verification": Verification.UNVERIFIED,
                    "cli_version": None,
                    "verified_at": None,
                }
            )
            for row in profile.capabilities
        ]
        capabilities.append(
            CapabilityRecordV1(name="custom-capability", verification=Verification.OBSERVED)
        )
        profiles.append(
            profile.model_copy(
                update={
                    "executable": str(executable),
                    "config_home": f"vendors/{profile.harness.value}",
                    "capabilities": capabilities,
                    "model_defaults": profile.model_defaults.model_copy(
                        update={"model": "owner-model", "effort": "owner-effort"}
                    ),
                    "timeouts": profile.timeouts.model_copy(update={"attempt_seconds": timeout}),
                }
            )
        )
    path = tmp_path / "profiles.yaml"
    write_profile_set(path, source.model_copy(update={"profiles": profiles}))
    for profile in profiles:
        (tmp_path / profile.config_home).mkdir(parents=True)
    return path


def _environment(mode: str = "ok") -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", ""),
        "HOME": "/tmp/agentteam-probe-sensitive-home",
        "FAKE_PROBE_MODE": mode,
    }


def _run(path: Path, *, mode: str = "ok") -> tuple[Any, list[tuple[str, int]]]:
    profiles = load_profile_set(path).profiles
    confirmations: list[tuple[str, int]] = []

    def confirm(harness: HarnessId, call: int, _description: str) -> bool:
        confirmations.append((harness.value, call))
        return True

    result = run_attended_probes(
        profiles,
        profile_path=path,
        versions=VERSIONS,
        environ=_environment(mode),
        confirm=confirm,
    )
    return result, confirmations


def _rows(path: Path, harness: HarnessId) -> dict[str, CapabilityRecordV1]:
    profile = next(p for p in load_profile_set(path).profiles if p.harness is harness)
    return {row.name: row for row in profile.capabilities}


def test_primary_probes_pass_in_three_calls_and_write_terminal_captures(
    tmp_path: Path,
) -> None:
    path = _profile_path(tmp_path)
    before_settings = [
        profile.model_dump(exclude={"capabilities"}) for profile in load_profile_set(path).profiles
    ]
    result, confirmations = _run(path)
    assert result.all_ready is True
    assert confirmations == [("claude-code", 1), ("codex", 1), ("grok", 1)]
    assert all(item.calls_used == 1 for item in result.by_harness.values())
    after = load_profile_set(path)
    assert [
        profile.model_dump(exclude={"capabilities"}) for profile in after.profiles
    ] == before_settings
    for profile in after.profiles:
        custom = next(row for row in profile.capabilities if row.name == "custom-capability")
        assert custom.verification is Verification.OBSERVED
        assert custom.cli_version is None and custom.verified_at is None

    assert (
        _rows(path, HarnessId.CODEX)["jsonl-final-agent-message"].verification
        is Verification.VERIFIED
    )
    grok = _rows(path, HarnessId.GROK)
    assert grok["structured-output-field"].verification is Verification.VERIFIED
    assert grok["structured-output-text"].verification is Verification.UNVERIFIED

    assert result.capture_id is not None
    assert "ATM_INSTRUCTION_" not in _TASK + _PROBE_SCHEMA
    assert "ATM_SKILL_" not in _TASK + _PROBE_SCHEMA
    capture = next((tmp_path / "probes").glob(f"*/{result.capture_id}"))
    for harness in ("claude-code", "codex", "grok"):
        call = capture / harness / "call-1"
        manifest = json.loads((call / "manifest.json").read_text())
        assert manifest["status"] == "succeeded"
        for artifact in manifest["artifacts"]:
            data = (call / artifact["path"]).read_bytes()
            assert hashlib.sha256(data).hexdigest() == artifact["sha256"]
        command = (call / "command.redacted.json").read_text()
        assert "ATM_INSTRUCTION_" not in command
        assert "ATM_SKILL_" not in command
        assert "agentteam-probe-sensitive-home" not in command
        if sys.platform != "win32":
            assert stat.S_IMODE(call.stat().st_mode) == 0o700
            for file in call.iterdir():
                if file.is_file():
                    assert stat.S_IMODE(file.stat().st_mode) == 0o600


def test_fallback_mode_uses_exactly_two_calls_and_verifies_fallback_ladders(
    tmp_path: Path,
) -> None:
    path = _profile_path(tmp_path)
    result, confirmations = _run(path, mode="fallback")
    assert result.all_ready is True
    assert len(confirmations) == 6
    assert all(item.calls_used == 2 for item in result.by_harness.values())
    claude = _rows(path, HarnessId.CLAUDE_CODE)
    assert claude["append-system-prompt-file"].verification is Verification.UNVERIFIED
    assert claude["append-system-prompt"].verification is Verification.VERIFIED
    assert claude["skills-plugin-dir"].verification is Verification.VERIFIED
    assert claude["skills-workspace"].verification is Verification.VERIFIED
    codex = _rows(path, HarnessId.CODEX)
    assert codex["instructions-model-instructions-file"].verification is Verification.UNVERIFIED
    assert codex["instructions-developer-instructions"].verification is Verification.VERIFIED
    assert codex["instructions-workspace-agents-md"].verification is Verification.VERIFIED
    grok = _rows(path, HarnessId.GROK)
    assert grok["instructions-rules"].verification is Verification.UNVERIFIED
    assert grok["instructions-system-prompt-override"].verification is Verification.VERIFIED


def test_two_call_ceiling_leaves_missing_skill_matrix_unready(tmp_path: Path) -> None:
    path = _profile_path(tmp_path)
    result, confirmations = _run(path, mode="missing-skill")
    assert result.all_ready is False
    assert len(confirmations) == 6
    assert all(
        item.calls_used == 2 and item.status == "failed" for item in result.by_harness.values()
    )


def test_failed_fallback_preserves_capabilities_proven_by_the_first_call(
    tmp_path: Path,
) -> None:
    path = _profile_path(tmp_path)
    profile = load_profile_set(path).profiles[0]
    result = run_attended_probes(
        [profile],
        profile_path=path,
        versions={HarnessId.CLAUDE_CODE: VERSIONS[HarnessId.CLAUDE_CODE]},
        environ=_environment("fallback-error"),
        confirm=lambda _h, _c, _d: True,
    )
    assert result.all_ready is False
    assert result.by_harness[HarnessId.CLAUDE_CODE].calls_used == 2
    rows = _rows(path, HarnessId.CLAUDE_CODE)
    for name in ("headless-json", "structured-output", "native-auth"):
        assert rows[name].verification is Verification.VERIFIED
    assert rows["append-system-prompt-file"].verification is Verification.VERIFIED
    assert rows["skills-config-home"].verification is Verification.UNVERIFIED


@pytest.mark.parametrize("mode", ["malformed", "timeout"])
def test_malformed_and_timeout_calls_are_terminal_and_bounded(tmp_path: Path, mode: str) -> None:
    path = _profile_path(tmp_path, timeout=1)
    profile = load_profile_set(path).profiles[0]
    confirmations: list[int] = []

    def confirm(_harness: HarnessId, call: int, _description: str) -> bool:
        confirmations.append(call)
        return True

    result = run_attended_probes(
        [profile],
        profile_path=path,
        versions={HarnessId.CLAUDE_CODE: VERSIONS[HarnessId.CLAUDE_CODE]},
        environ=_environment(mode),
        confirm=confirm,
    )
    assert result.all_ready is False
    assert confirmations == [1, 2]
    assert result.by_harness[HarnessId.CLAUDE_CODE].calls_used == 2
    capture = next((tmp_path / "probes").glob(f"*/{result.capture_id}"))
    statuses = [
        json.loads((capture / "claude-code" / f"call-{call}" / "manifest.json").read_text())[
            "status"
        ]
        for call in (1, 2)
    ]
    assert statuses == (["timed-out", "timed-out"] if mode == "timeout" else ["failed", "failed"])


def test_codex_event_disagreement_is_telemetry_only_and_grok_text_is_selected(
    tmp_path: Path,
) -> None:
    path = _profile_path(tmp_path)
    profiles = load_profile_set(path).profiles
    codex = next(profile for profile in profiles if profile.harness is HarnessId.CODEX)
    codex_result = run_attended_probes(
        [codex],
        profile_path=path,
        versions={HarnessId.CODEX: VERSIONS[HarnessId.CODEX]},
        environ=_environment("event-mismatch"),
        confirm=lambda _h, _c, _d: True,
    )
    assert codex_result.all_ready is True
    codex_rows = _rows(path, HarnessId.CODEX)
    assert codex_rows["output-last-message"].verification is Verification.VERIFIED
    assert codex_rows["jsonl-final-agent-message"].verification is Verification.UNVERIFIED

    grok = next(
        profile for profile in load_profile_set(path).profiles if profile.harness is HarnessId.GROK
    )
    grok_result = run_attended_probes(
        [grok],
        profile_path=path,
        versions={HarnessId.GROK: VERSIONS[HarnessId.GROK]},
        environ=_environment("text"),
        confirm=lambda _h, _c, _d: True,
    )
    assert grok_result.all_ready is True
    grok_rows = _rows(path, HarnessId.GROK)
    assert grok_rows["structured-output-field"].verification is Verification.UNVERIFIED
    assert grok_rows["structured-output-text"].verification is Verification.VERIFIED


def test_decline_makes_zero_calls_and_partial_cancellation_preserves_prior_rows(
    tmp_path: Path,
) -> None:
    path = _profile_path(tmp_path)
    before = path.read_bytes()
    with pytest.raises(ProbeCancelled) as first:
        run_attended_probes(
            load_profile_set(path).profiles,
            profile_path=path,
            versions=VERSIONS,
            environ=_environment(),
            confirm=lambda _h, _c, _d: False,
        )
    assert first.value.results[HarnessId.CLAUDE_CODE].calls_used == 0
    assert path.read_bytes() == before
    assert not list((tmp_path / "probes").glob("*/*/*/call-*"))

    decisions = iter([True, False])
    with pytest.raises(ProbeCancelled) as partial:
        run_attended_probes(
            load_profile_set(path).profiles,
            profile_path=path,
            versions=VERSIONS,
            environ=_environment(),
            confirm=lambda _h, _c, _d: next(decisions),
        )
    assert partial.value.results[HarnessId.CLAUDE_CODE].status == "passed"
    assert partial.value.results[HarnessId.CODEX].status == "cancelled"
    assert _rows(path, HarnessId.CLAUDE_CODE)["native-auth"].verification is Verification.VERIFIED
    assert _rows(path, HarnessId.CODEX)["native-auth"].verified_at is None


def test_cli_probe_requires_tty_and_keeps_json_stdout_parseable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _profile_path(tmp_path)
    before = path.read_bytes()
    non_attended = runner.invoke(app, ["profile", "doctor", "--probe", "--config", str(path)])
    assert non_attended.exit_code == 2
    assert path.read_bytes() == before

    monkeypatch.setattr("agentteam.commands.profile._is_attended", lambda: True)

    def confirm(harness: HarnessId, call: int, _description: str) -> bool:
        import typer

        typer.echo(f"confirm {harness.value} call {call}", err=True)
        return True

    monkeypatch.setattr("agentteam.commands.profile._confirm_call", confirm)
    completed = runner.invoke(
        app,
        ["profile", "doctor", "--probe", "--json", "--config", str(path)],
        env={"FAKE_PROBE_MODE": "ok"},
    )
    assert completed.exit_code == 0, completed.output
    payload = json.loads(completed.stdout)
    assert all(row["probe"]["status"] == "passed" for row in payload["profiles"])
    assert "confirm claude-code call 1" in completed.stderr


def test_cli_probe_exit_codes_for_signed_out_decline_and_completed_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("agentteam.commands.profile._is_attended", lambda: True)

    signed_out_path = _profile_path(tmp_path / "signed-out")
    called = False

    def should_not_confirm(_harness: HarnessId, _call: int, _description: str) -> bool:
        nonlocal called
        called = True
        return True

    monkeypatch.setattr("agentteam.commands.profile._confirm_call", should_not_confirm)
    signed_out = runner.invoke(
        app,
        ["profile", "doctor", "--probe", "--config", str(signed_out_path)],
        env={"FAKE_PROBE_MODE": "signed-out"},
    )
    assert signed_out.exit_code == 1
    assert called is False
    assert not (signed_out_path.parent / "probes").exists()

    decline_path = _profile_path(tmp_path / "decline")
    monkeypatch.setattr("agentteam.commands.profile._confirm_call", lambda _h, _c, _d: False)
    declined = runner.invoke(
        app,
        ["profile", "doctor", "--probe", "--json", "--config", str(decline_path)],
        env={"FAKE_PROBE_MODE": "ok"},
    )
    assert declined.exit_code == 130
    declined_payload = json.loads(declined.stdout)
    assert declined_payload["profiles"][0]["probe"]["status"] == "cancelled"
    assert declined_payload["profiles"][0]["probe"]["calls_used"] == 0

    failed_path = _profile_path(tmp_path / "failed")
    monkeypatch.setattr("agentteam.commands.profile._confirm_call", lambda _h, _c, _d: True)
    failed = runner.invoke(
        app,
        ["profile", "doctor", "--probe", "--json", "--config", str(failed_path)],
        env={"FAKE_PROBE_MODE": "missing-skill"},
    )
    assert failed.exit_code == 1
    failed_payload = json.loads(failed.stdout)
    assert all(row["probe"]["calls_used"] == 2 for row in failed_payload["profiles"])
    assert all(row["probe"]["status"] == "failed" for row in failed_payload["profiles"])


def test_cli_prompt_interrupt_exits_130_before_a_vendor_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _profile_path(tmp_path)
    before = path.read_bytes()
    monkeypatch.setattr("agentteam.commands.profile._is_attended", lambda: True)

    def abort_prompt(*_args: object, **_kwargs: object) -> bool:
        raise Abort

    monkeypatch.setattr("agentteam.commands.profile.typer.confirm", abort_prompt)
    interrupted = runner.invoke(
        app,
        ["profile", "doctor", "--probe", "--json", "--config", str(path)],
        env={"FAKE_PROBE_MODE": "ok"},
    )
    assert interrupted.exit_code == 130
    payload = json.loads(interrupted.stdout)
    assert payload["profiles"][0]["probe"]["status"] == "cancelled"
    assert payload["profiles"][0]["probe"]["calls_used"] == 0
    assert path.read_bytes() == before
    assert not list((tmp_path / "probes").glob("*/*/*/call-*"))


@pytest.mark.parametrize(
    "probe_env",
    [
        {"FAKE_PROBE_MODE_GROK": "missing-flags"},
        {"FAKE_PROBE_MODE_CODEX": "signed-out"},
    ],
)
def test_probe_preflights_every_harness_before_any_model_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, probe_env: dict[str, str]
) -> None:
    path = _profile_path(tmp_path)
    monkeypatch.setattr("agentteam.commands.profile._is_attended", lambda: True)
    confirmations: list[str] = []

    def confirm(harness: HarnessId, _call: int, _description: str) -> bool:
        confirmations.append(harness.value)
        return True

    monkeypatch.setattr("agentteam.commands.profile._confirm_call", confirm)
    result = runner.invoke(
        app,
        ["profile", "doctor", "--probe", "--config", str(path)],
        env=probe_env,
    )
    assert result.exit_code == 1
    assert confirmations == []
    assert not (tmp_path / "probes").exists()
