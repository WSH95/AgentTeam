"""Deterministic attended native-auth doctor probes; no vendor/model calls."""

from __future__ import annotations

import hashlib
import io
import json
import os
import stat
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest
from typer import Abort
from typer.testing import CliRunner

from agentteam.cli import app
from agentteam.domain.common import HarnessId
from agentteam.domain.profile import CapabilityRecordV1, ProxyPolicy, Verification
from agentteam.harness.skills import MARKER
from agentteam.profile.probe import (
    _PROBE_SCHEMA,
    _TASK,
    ProbeCancelled,
    _drain_terminated_probe_process,
    _Recipe,
    _run_probe_process,
    run_attended_probes,
)
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
                    "proxy_policy": ProxyPolicy.INHERIT,
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


def _run(
    path: Path,
    *,
    mode: str = "ok",
    selected_harnesses: frozenset[HarnessId] | None = None,
    reprobe_ready: bool = False,
) -> tuple[Any, list[tuple[str, int]]]:
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
        selected_harnesses=selected_harnesses,
        reprobe_ready=reprobe_ready,
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
        if harness == "claude-code":
            redacted = json.loads(command)
            argv = redacted["argv_redacted"]
            allowed_index = argv.index("--allowedTools")
            assert set(argv[allowed_index + 1].split(",")) == {
                "Read",
                "Grep",
                "Glob",
                "LS",
                "Skill",
            }
            disallowed_index = argv.index("--disallowedTools")
            assert set(argv[disallowed_index + 1].split(",")) == {
                "Write",
                "Edit",
                "NotebookEdit",
                "Bash",
                "WebFetch",
                "WebSearch",
            }
            assert "--safe-mode" not in argv
            assert "--bare" not in argv
        if harness == "grok":
            redacted = json.loads(command)
            assert "-p" not in redacted["argv_redacted"]
            assert "--prompt-file" in redacted["argv_redacted"]
        if sys.platform != "win32":
            assert stat.S_IMODE(call.stat().st_mode) == 0o700
            for file in call.iterdir():
                if file.is_file():
                    assert stat.S_IMODE(file.stat().st_mode) == 0o600


def test_probe_inherits_proxy_but_records_only_its_name(tmp_path: Path) -> None:
    path = _profile_path(tmp_path)
    proxy_value = "http://sensitive-probe-proxy.invalid"
    result = run_attended_probes(
        load_profile_set(path).profiles,
        profile_path=path,
        versions=VERSIONS,
        environ={**_environment(), "HTTP_PROXY": proxy_value, "NO_PROXY": "localhost"},
        confirm=lambda _h, _c, _d: True,
    )
    capture = next((tmp_path / "probes").glob(f"*/{result.capture_id}"))
    for command_path in capture.glob("*/call-1/command.redacted.json"):
        command = json.loads(command_path.read_text())
        assert {"HTTP_PROXY", "NO_PROXY"}.issubset(command["environment_names"])
    for artifact in capture.rglob("*"):
        if artifact.is_file():
            assert proxy_value not in artifact.read_text(encoding="utf-8", errors="replace")


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


def test_fake_claude_withholds_skills_without_explicit_skill_permission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _profile_path(tmp_path)
    monkeypatch.setattr("agentteam.profile.probe.CLAUDE_ALLOWED_TOOLS", "Read,Grep,Glob,LS")
    result = run_attended_probes(
        load_profile_set(path).profiles,
        profile_path=path,
        versions=VERSIONS,
        environ=_environment(),
        confirm=lambda _h, _c, _d: True,
        selected_harnesses=frozenset({HarnessId.CLAUDE_CODE}),
    )

    assert result.all_ready is False
    assert result.by_harness[HarnessId.CLAUDE_CODE].calls_used == 2
    rows = _rows(path, HarnessId.CLAUDE_CODE)
    assert rows["append-system-prompt-file"].verification is Verification.VERIFIED
    for name in ("skills-config-home", "skills-plugin-dir", "skills-workspace"):
        assert rows[name].verification is Verification.UNVERIFIED


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


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX process-group semantics")
def test_probe_timeout_kills_a_sigterm_surviving_descendant(tmp_path: Path) -> None:
    marker = tmp_path / "descendant-alive"
    child = (
        "import pathlib,signal,time\n"
        "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
        f"marker = pathlib.Path({str(marker)!r})\n"
        "while True:\n"
        "    marker.write_text(str(time.time()))\n"
        "    time.sleep(0.1)\n"
    )
    script = tmp_path / "probe-parent.py"
    script.write_text(
        "import signal,subprocess,sys,time\n"
        "def stop(_signum, _frame):\n"
        "    raise SystemExit(0)\n"
        "signal.signal(signal.SIGTERM, stop)\n"
        f"subprocess.Popen([sys.executable, '-c', {child!r}])\n"
        "time.sleep(30)\n",
        encoding="utf-8",
    )
    recipe = _Recipe(
        argv=[sys.executable, str(script)],
        cwd=tmp_path,
        env=dict(os.environ),
        stdin_text=None,
        output_file=None,
        redacted_command={},
        instruction_markers={},
        skill_markers={},
        attempted_base=(),
    )

    started = time.monotonic()
    raw = _run_probe_process(recipe, timeout_seconds=1, platform=sys.platform)
    assert raw.timed_out is True
    assert time.monotonic() - started < 5
    if marker.is_file():
        first = marker.read_text(encoding="utf-8")
        time.sleep(0.4)
        assert marker.read_text(encoding="utf-8") == first


def test_probe_final_pipe_drain_is_bounded() -> None:
    class StuckProcess:
        pid = 424242

        def __init__(self) -> None:
            self.returncode: int | None = None
            self.stdin = io.BytesIO()
            self.stdout = io.BytesIO()
            self.stderr = io.BytesIO()
            self.communicate_timeouts: list[float | int | None] = []
            self.kill_calls = 0

        def communicate(
            self, _input: bytes | None = None, *, timeout: float | None = None
        ) -> tuple[bytes, bytes]:
            self.communicate_timeouts.append(timeout)
            if timeout is None:
                raise AssertionError("probe communicates must always be bounded")
            raise subprocess.TimeoutExpired(["fake-probe"], timeout)

        def poll(self) -> int | None:
            return self.returncode

        def wait(self, *, timeout: float | None = None) -> int:
            self.returncode = 0
            return 0

        def kill(self) -> None:
            self.kill_calls += 1

    process: Any = StuckProcess()
    stdout, stderr = _drain_terminated_probe_process(process)
    assert stdout == b""
    assert stderr == b"process pipes did not close after termination"
    assert process.communicate_timeouts == [10, 5]
    assert process.kill_calls == 1
    assert process.stdin.closed
    assert process.stdout.closed
    assert process.stderr.closed


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


def test_ready_profiles_skip_by_default_and_selected_forced_probes_follow_profile_order(
    tmp_path: Path,
) -> None:
    path = _profile_path(tmp_path)
    first, _confirmations = _run(path)
    captures_before = set((tmp_path / "probes").glob("*/*"))

    skipped, skipped_confirmations = _run(path)
    assert skipped.all_ready is True
    assert skipped.capture_id is None
    assert skipped_confirmations == []
    assert all(row.status == "already-ready" for row in skipped.by_harness.values())
    assert set((tmp_path / "probes").glob("*/*")) == captures_before

    selected = frozenset({HarnessId.CODEX, HarnessId.CLAUDE_CODE})
    selected_skipped, selected_skip_confirmations = _run(
        path,
        selected_harnesses=selected,
    )
    assert selected_skip_confirmations == []
    assert selected_skipped.by_harness[HarnessId.CLAUDE_CODE].status == "already-ready"
    assert selected_skipped.by_harness[HarnessId.CODEX].status == "already-ready"
    assert selected_skipped.by_harness[HarnessId.GROK].status == "not-selected"
    codex_before = _rows(path, HarnessId.CODEX)["native-auth"].verified_at
    assert codex_before is not None

    forced, forced_confirmations = _run(
        path,
        selected_harnesses=selected,
        reprobe_ready=True,
    )
    assert forced.all_ready is True
    assert forced.capture_id is not None and forced.capture_id != first.capture_id
    assert forced_confirmations == [("claude-code", 1), ("codex", 1)]
    claude = forced.by_harness[HarnessId.CLAUDE_CODE]
    assert claude.status == "passed"
    assert claude.calls_used == 1
    assert claude.capture_id == forced.capture_id
    assert claude.profile_updated is True
    assert forced.by_harness[HarnessId.CODEX].capture_id == forced.capture_id
    codex_after = _rows(path, HarnessId.CODEX)["native-auth"].verified_at
    assert codex_after is not None and codex_after > codex_before
    assert forced.by_harness[HarnessId.GROK].status == "not-selected"
    assert forced.by_harness[HarnessId.GROK].calls_used == 0
    assert forced.by_harness[HarnessId.GROK].capture_id is None


def test_forced_probe_failure_downgrades_current_evidence_and_uses_two_calls(
    tmp_path: Path,
) -> None:
    path = _profile_path(tmp_path)
    _run(path)
    before = _rows(path, HarnessId.CLAUDE_CODE)["skills-config-home"]
    descriptions: list[str] = []

    def confirm(_harness: HarnessId, _call: int, description: str) -> bool:
        descriptions.append(description)
        return True

    result = run_attended_probes(
        load_profile_set(path).profiles,
        profile_path=path,
        versions=VERSIONS,
        environ=_environment("missing-skill"),
        confirm=confirm,
        selected_harnesses=frozenset({HarnessId.CLAUDE_CODE}),
        reprobe_ready=True,
    )

    claude = result.by_harness[HarnessId.CLAUDE_CODE]
    assert result.all_ready is False
    assert claude.status == "failed" and claude.calls_used == 2
    assert result.by_harness[HarnessId.CODEX].status == "not-selected"
    assert result.by_harness[HarnessId.GROK].status == "not-selected"
    assert len(descriptions) == 2
    assert all(
        "forced reassessment; failure replaces current capability evidence" in description
        for description in descriptions
    )
    after = _rows(path, HarnessId.CLAUDE_CODE)["skills-config-home"]
    assert before.verification is Verification.VERIFIED
    assert before.verified_at is not None
    assert after.verification is Verification.UNVERIFIED
    assert after.cli_version == VERSIONS[HarnessId.CLAUDE_CODE]
    assert after.verified_at is not None and after.verified_at > before.verified_at


def test_forced_claude_reprobe_refuses_unmanaged_home_then_verifies_fallbacks(
    tmp_path: Path,
) -> None:
    path = _profile_path(tmp_path)
    _run(path)
    skills = tmp_path / "vendors" / "claude-code" / "skills"
    (skills / MARKER).unlink()
    owner_file = skills / "owner-skill.md"
    owner_file.write_text("keep\n", encoding="utf-8")

    result, confirmations = _run(
        path,
        selected_harnesses=frozenset({HarnessId.CLAUDE_CODE}),
        reprobe_ready=True,
    )

    assert result.all_ready is True
    assert confirmations == [("claude-code", 1), ("claude-code", 2)]
    assert owner_file.read_text(encoding="utf-8") == "keep\n"
    rows = _rows(path, HarnessId.CLAUDE_CODE)
    assert rows["append-system-prompt-file"].verification is Verification.UNVERIFIED
    assert rows["skills-config-home"].verification is Verification.UNVERIFIED
    assert rows["append-system-prompt"].verification is Verification.VERIFIED
    assert rows["skills-plugin-dir"].verification is Verification.VERIFIED
    assert rows["skills-workspace"].verification is Verification.VERIFIED


def test_forced_probe_decline_retains_completed_results_and_nonselected_status(
    tmp_path: Path,
) -> None:
    path = _profile_path(tmp_path)
    _run(path)
    decisions = iter([True, False])

    with pytest.raises(ProbeCancelled) as cancelled:
        run_attended_probes(
            load_profile_set(path).profiles,
            profile_path=path,
            versions=VERSIONS,
            environ=_environment(),
            confirm=lambda _h, _c, _d: next(decisions),
            selected_harnesses=frozenset({HarnessId.CLAUDE_CODE, HarnessId.CODEX}),
            reprobe_ready=True,
        )

    results = cancelled.value.results
    assert results[HarnessId.CLAUDE_CODE].status == "passed"
    assert results[HarnessId.CLAUDE_CODE].profile_updated is True
    assert results[HarnessId.CODEX].status == "cancelled"
    assert results[HarnessId.CODEX].calls_used == 0
    assert results[HarnessId.GROK].status == "not-selected"


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


def test_cli_ready_probe_skips_until_explicit_reprobe_and_reports_selection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _profile_path(tmp_path)
    _run(path)
    monkeypatch.setattr("agentteam.commands.profile._is_attended", lambda: True)
    confirmations: list[tuple[str, int, str]] = []

    def confirm(harness: HarnessId, call: int, description: str) -> bool:
        confirmations.append((harness.value, call, description))
        return True

    monkeypatch.setattr("agentteam.commands.profile._confirm_call", confirm)
    skipped = runner.invoke(
        app,
        ["profile", "doctor", "--probe", "--json", "--config", str(path)],
        env={"FAKE_PROBE_MODE": "ok"},
    )
    assert skipped.exit_code == 0, skipped.output
    assert confirmations == []
    assert all(
        row["probe"]["status"] == "already-ready" for row in json.loads(skipped.stdout)["profiles"]
    )

    forced = runner.invoke(
        app,
        [
            "profile",
            "doctor",
            "--probe",
            "--reprobe-ready",
            "--harness",
            "codex",
            "--harness",
            "claude-code",
            "--json",
            "--config",
            str(path),
        ],
        env={"FAKE_PROBE_MODE": "ok"},
    )
    assert forced.exit_code == 0, forced.output
    assert [(harness, call) for harness, call, _description in confirmations] == [
        ("claude-code", 1),
        ("codex", 1),
    ]
    assert all("forced reassessment" in item[2] for item in confirmations)
    payload = json.loads(forced.stdout)
    rows = {row["harness"]: row["probe"] for row in payload["profiles"]}
    capture_id = rows["claude-code"]["capture_id"]
    assert capture_id is not None and rows["codex"]["capture_id"] == capture_id
    assert rows["claude-code"] == {
        "status": "passed",
        "calls_used": 1,
        "capture_id": capture_id,
        "profile_updated": True,
    }
    assert rows["grok"] == {
        "status": "not-selected",
        "calls_used": 0,
        "capture_id": None,
        "profile_updated": False,
    }


def test_cli_reprobe_ready_without_selection_retests_all_profiles_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _profile_path(tmp_path)
    _run(path)
    monkeypatch.setattr("agentteam.commands.profile._is_attended", lambda: True)
    confirmations: list[tuple[str, int]] = []

    def confirm(harness: HarnessId, call: int, _description: str) -> bool:
        confirmations.append((harness.value, call))
        return True

    monkeypatch.setattr(
        "agentteam.commands.profile._confirm_call",
        confirm,
    )

    completed = runner.invoke(
        app,
        [
            "profile",
            "doctor",
            "--probe",
            "--reprobe-ready",
            "--json",
            "--config",
            str(path),
        ],
        env={"FAKE_PROBE_MODE": "ok"},
    )
    assert completed.exit_code == 0, completed.output
    assert confirmations == [("claude-code", 1), ("codex", 1), ("grok", 1)]
    rows = json.loads(completed.stdout)["profiles"]
    assert all(row["probe"]["status"] == "passed" for row in rows)
    assert len({row["probe"]["capture_id"] for row in rows}) == 1


@pytest.mark.parametrize(
    "arguments",
    [
        ["--reprobe-ready"],
        ["--harness", "codex"],
        ["--probe", "--harness", "unknown"],
        ["--probe", "--harness", "claude", "--harness", "claude-code"],
        ["--probe", "--harness", "grok", "--harness", "grok"],
    ],
)
def test_cli_reprobe_rejects_invalid_option_combinations_before_calls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    arguments: list[str],
) -> None:
    path = _profile_path(tmp_path)
    before = path.read_bytes()
    confirmations: list[str] = []
    monkeypatch.setattr("agentteam.commands.profile._is_attended", lambda: True)

    def confirm(harness: HarnessId, _call: int, _description: str) -> bool:
        confirmations.append(harness.value)
        return True

    monkeypatch.setattr(
        "agentteam.commands.profile._confirm_call",
        confirm,
    )

    result = runner.invoke(
        app,
        ["profile", "doctor", *arguments, "--config", str(path)],
        env={"FAKE_PROBE_MODE": "ok"},
    )
    assert result.exit_code == 2
    assert confirmations == []
    assert path.read_bytes() == before
    assert not (tmp_path / "probes").exists()


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


def test_real_typer_confirm_eof_exits_130_before_a_vendor_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _profile_path(tmp_path)
    before = path.read_bytes()
    monkeypatch.setattr("agentteam.commands.profile._is_attended", lambda: True)

    interrupted = runner.invoke(
        app,
        ["profile", "doctor", "--probe", "--config", str(path)],
        input="",
        env={"FAKE_PROBE_MODE": "ok"},
    )
    assert interrupted.exit_code == 130
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
        [
            "profile",
            "doctor",
            "--probe",
            "--harness",
            "claude-code",
            "--config",
            str(path),
        ],
        env=probe_env,
    )
    assert result.exit_code == 1
    assert confirmations == []
    assert not (tmp_path / "probes").exists()
