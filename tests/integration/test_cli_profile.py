"""`atm profile init/validate/doctor` (plan sections 8 and 11; no --probe until G5)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentteam.cli import app

runner = CliRunner()
REPO_ROOT = Path(__file__).resolve().parents[2]
CI_FAKE = REPO_ROOT / "examples" / "profiles" / "ci-fake.yaml"


def test_init_writes_profiles_and_config_homes(tmp_path: Path) -> None:
    config = tmp_path / "profiles.yaml"
    result = runner.invoke(app, ["profile", "init", "--config", str(config)])
    assert result.exit_code == 0, result.output
    assert config.is_file()
    for harness in ("claude-code", "codex", "grok"):
        assert (tmp_path / "vendors" / harness).is_dir()
    assert "login" in result.output.lower()
    assert "never" in result.output.lower()  # never automates a browser / copies credentials


def test_init_refuses_an_existing_file(tmp_path: Path) -> None:
    config = tmp_path / "profiles.yaml"
    config.write_text("x: 1\n", encoding="utf-8")
    result = runner.invoke(app, ["profile", "init", "--config", str(config)])
    assert result.exit_code == 2
    assert "exists" in result.output


def test_validate_ok_and_invalid(tmp_path: Path) -> None:
    ok = runner.invoke(app, ["profile", "validate", "--config", str(CI_FAKE)])
    assert ok.exit_code == 0, ok.output
    bad = tmp_path / "bad.yaml"
    bad.write_text("schema_version: 1\nkind: harness-profile-set\nsurprise: 1\n", encoding="utf-8")
    result = runner.invoke(app, ["profile", "validate", "--config", str(bad)])
    assert result.exit_code == 2
    assert "surprise" in result.output


def test_doctor_reports_fake_versions_and_exits_0() -> None:
    result = runner.invoke(app, ["profile", "doctor", "--config", str(CI_FAKE)])
    assert result.exit_code == 0, result.output
    assert "2.1.241" in result.output  # fake claude --version
    assert "codex-cli 0.149.0" in result.output
    assert "grok 1.0.5" in result.output


def test_doctor_json_is_sanitized_names_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FAKE_CONFLICT", "super-secret-value")
    result = runner.invoke(app, ["profile", "doctor", "--config", str(CI_FAKE), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    text = json.dumps(payload)
    assert "FAKE_CONFLICT" in text  # the NAME is reported as set
    assert "super-secret-value" not in text  # the VALUE never appears
    claude = next(p for p in payload["profiles"] if p["harness"] == "claude-code")
    assert claude["executable_resolved"] is True
    assert claude["version"].startswith("2.1.241")
    assert claude["conflicts_set"] == ["FAKE_CONFLICT"]


def test_doctor_missing_executable_exits_1(tmp_path: Path) -> None:
    config = tmp_path / "profiles.yaml"
    config.write_text(
        "schema_version: 1\n"
        "kind: harness-profile-set\n"
        "profiles:\n"
        "  - harness: codex\n"
        "    executable: ./no-such-binary-here\n"
        "    config_home: vendors/codex\n"
        "    environment: {config_home_variable: CODEX_HOME}\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["profile", "doctor", "--config", str(config)])
    assert result.exit_code == 1
    assert "not found" in result.output
