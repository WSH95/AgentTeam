"""`atm profile init/validate/doctor` (plan sections 8 and 11)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentteam.cli import app
from agentteam.domain.common import HarnessId
from agentteam.domain.profile import ProxyPolicy
from agentteam.resolution.profiles import (
    load_profile_set,
    resolve_config_home,
    resolve_profile_executable,
    write_profile_set,
)

runner = CliRunner()
REPO_ROOT = Path(__file__).resolve().parents[2]
CI_FAKE = REPO_ROOT / "examples" / "profiles" / "ci-fake.yaml"


def test_doctor_help_advertises_selectable_authoritative_reprobe() -> None:
    result = runner.invoke(app, ["profile", "doctor", "--help"])
    assert result.exit_code == 0, result.output
    assert "--harness" in result.output
    assert "--reprobe-ready" in result.output
    assert "replace current evidence" in result.output


def test_init_writes_profiles_and_config_homes(tmp_path: Path) -> None:
    config = tmp_path / "profiles.yaml"
    result = runner.invoke(app, ["profile", "init", "--config", str(config)])
    assert result.exit_code == 0, result.output
    assert config.is_file()
    for harness in ("claude-code", "codex", "grok"):
        assert (tmp_path / "vendors" / harness).is_dir()
    codex = (tmp_path / "vendors" / "codex" / "config.toml").read_text()
    assert 'cli_auth_credentials_store = "file"' in codex
    assert 'forced_login_method = "chatgpt"' in codex
    grok = (tmp_path / "vendors" / "grok" / "config.toml").read_text()
    assert "[compat.cursor]" in grok and "[compat.claude]" in grok
    assert grok.count("= false") == 12
    assert (tmp_path / "vendors/claude-code/skills/.agentteam-managed").is_file()
    assert "login" in result.output.lower()
    assert "claude auth login" in result.output
    assert "codex login" in result.output
    assert "grok login --oauth" in result.output
    assert "never" in result.output.lower()  # never automates a browser / copies credentials
    assert "inherit standard proxy variables" in result.output
    assert all(
        profile.proxy_policy is ProxyPolicy.INHERIT for profile in load_profile_set(config).profiles
    )


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
    before = CI_FAKE.read_bytes()
    result = runner.invoke(app, ["profile", "doctor", "--config", str(CI_FAKE)])
    assert result.exit_code == 0, result.output
    assert "2.1.241" in result.output  # fake claude --version
    assert "codex-cli 0.149.0" in result.output
    assert "grok 1.0.5" in result.output
    assert "proxy policy: inherit" in result.output
    assert CI_FAKE.read_bytes() == before


def test_doctor_json_is_sanitized_names_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FAKE_CONFLICT", "super-secret-value")
    result = runner.invoke(app, ["profile", "doctor", "--config", str(CI_FAKE), "--json"])
    assert result.exit_code == 2, result.output
    payload = json.loads(result.output)
    text = json.dumps(payload)
    assert "FAKE_CONFLICT" in text  # the NAME is reported as set
    assert "super-secret-value" not in text  # the VALUE never appears
    claude = next(p for p in payload["profiles"] if p["harness"] == "claude-code")
    assert claude["executable_resolved"] is True
    assert claude["version"].startswith("2.1.241")
    assert claude["conflicts_set"] == ["FAKE_CONFLICT"]
    assert claude["proxy_policy"] == "inherit"
    assert isinstance(claude["proxy_names_inherited"], list)
    assert claude["auth_state"] == "unknown"
    assert claude["readiness"]["ready"] is True
    assert claude["probe"] == {
        "status": "not-requested",
        "calls_used": 0,
        "capture_id": None,
        "profile_updated": False,
    }


def test_doctor_inherits_proxy_names_without_values_or_conflicts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = load_profile_set(CI_FAKE)
    profiles = []
    for profile in source.profiles:
        profiles.append(
            profile.model_copy(
                update={
                    "executable": str(resolve_profile_executable(CI_FAKE, profile.executable)),
                    "config_home": str(resolve_config_home(CI_FAKE, profile.config_home)),
                    "proxy_policy": ProxyPolicy.INHERIT,
                    "environment": profile.environment.model_copy(
                        update={
                            "conflicts": [
                                *profile.environment.conflicts,
                                "HTTP_PROXY",
                                "NO_PROXY",
                            ]
                        }
                    ),
                }
            )
        )
    config = tmp_path / "profiles.yaml"
    write_profile_set(config, source.model_copy(update={"profiles": profiles}))
    monkeypatch.setenv("HTTP_PROXY", "http://sensitive-proxy.invalid")
    monkeypatch.setenv("NO_PROXY", "sensitive-internal.invalid")

    result = runner.invoke(app, ["profile", "doctor", "--config", str(config), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    serialized = json.dumps(payload)
    assert "http://sensitive-proxy.invalid" not in serialized
    assert "sensitive-internal.invalid" not in serialized
    for row in payload["profiles"]:
        assert row["proxy_policy"] == "inherit"
        assert {"HTTP_PROXY", "NO_PROXY"}.issubset(row["proxy_names_inherited"])
        assert row["conflicts_set"] == []


def test_doctor_explicit_proxy_deny_still_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = load_profile_set(CI_FAKE)
    profile = source.profiles[0]
    denied = profile.model_copy(
        update={
            "executable": str(resolve_profile_executable(CI_FAKE, profile.executable)),
            "config_home": str(resolve_config_home(CI_FAKE, profile.config_home)),
            "proxy_policy": ProxyPolicy.DENY,
            "environment": profile.environment.model_copy(
                update={"conflicts": [*profile.environment.conflicts, "HTTP_PROXY"]}
            ),
        }
    )
    config = tmp_path / "profiles.yaml"
    write_profile_set(config, source.model_copy(update={"profiles": [denied]}))
    monkeypatch.setenv("HTTP_PROXY", "http://sensitive-proxy.invalid")

    result = runner.invoke(app, ["profile", "doctor", "--config", str(config), "--json"])

    assert result.exit_code == 2
    payload = json.loads(result.output)
    row = payload["profiles"][0]
    assert row["proxy_policy"] == "deny"
    assert row["proxy_names_inherited"] == []
    assert "HTTP_PROXY" in row["conflicts_set"]
    assert "http://sensitive-proxy.invalid" not in result.output


def test_doctor_missing_executable_exits_1(tmp_path: Path) -> None:
    config = tmp_path / "profiles.yaml"
    config.write_text(
        "schema_version: 1\n"
        "kind: harness-profile-set\n"
        "profiles:\n"
        "  - harness: codex\n"
        "    executable: ./no-such-binary-here\n"
        "    config_home: vendors/codex\n"
        "    proxy_policy: inherit\n"
        "    environment: {config_home_variable: CODEX_HOME}\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["profile", "doctor", "--config", str(config)])
    assert result.exit_code == 1
    assert "not found" in result.output


def test_doctor_reports_expected_version_mismatch_without_mutating_profile(
    tmp_path: Path,
) -> None:
    source = load_profile_set(CI_FAKE)
    profiles = []
    for profile in source.profiles:
        update: dict[str, object] = {
            "executable": str(resolve_profile_executable(CI_FAKE, profile.executable)),
            "config_home": str(resolve_config_home(CI_FAKE, profile.config_home)),
        }
        if profile.harness is HarnessId.CODEX:
            update["expected_version"] = "codex-cli 999.0.0"
        profiles.append(profile.model_copy(update=update))
    config = tmp_path / "profiles.yaml"
    write_profile_set(config, source.model_copy(update={"profiles": profiles}))
    before = config.read_bytes()

    result = runner.invoke(app, ["profile", "doctor", "--config", str(config), "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    codex = next(row for row in payload["profiles"] if row["harness"] == "codex")
    assert codex["expected_version_mismatch"] is True
    assert config.read_bytes() == before
