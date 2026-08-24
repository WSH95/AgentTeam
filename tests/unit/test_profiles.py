"""Profile-set loading, seeding, and profile-relative path resolution."""

from __future__ import annotations

import stat
import sys
from pathlib import Path

import pytest
import yaml

from agentteam.domain.common import HarnessId
from agentteam.domain.profile import HarnessProfileV1, ProxyPolicy
from agentteam.resolution.profiles import (
    ProfileError,
    default_profile_path,
    load_profile_set,
    resolve_profile_path,
    seed_default_profiles,
    write_profile_set,
)


def test_ci_vendor_profile_set_is_native_shaped_and_credential_free() -> None:
    # G7 vendor-smoke config (plan section 16): the real npm-installed CLIs by
    # bare PATH name (the Windows `.cmd` shim path — RISKS R30), no capability
    # rows (doctor exit 1 signed-out/unverified is the designed CI green), and
    # seeded conflict names so a leaked key on a runner fails the job closed.
    repo_root = Path(__file__).resolve().parents[2]
    loaded = load_profile_set(repo_root / "examples" / "profiles" / "ci-vendor.yaml")
    assert [p.harness for p in loaded.profiles] == [HarnessId.CLAUDE_CODE, HarnessId.CODEX]
    by_id = {p.harness: p for p in loaded.profiles}
    assert by_id[HarnessId.CLAUDE_CODE].executable == "claude"
    assert by_id[HarnessId.CODEX].executable == "codex"
    assert "ANTHROPIC_API_KEY" in by_id[HarnessId.CLAUDE_CODE].environment.conflicts
    assert "OPENAI_API_KEY" in by_id[HarnessId.CODEX].environment.conflicts
    for profile in loaded.profiles:
        assert profile.proxy_policy is ProxyPolicy.INHERIT
        assert profile.capabilities == []


def test_seed_covers_the_three_harnesses_with_conflict_data() -> None:
    seeded = seed_default_profiles()
    ids = [p.harness for p in seeded.profiles]
    assert ids == [HarnessId.CLAUDE_CODE, HarnessId.CODEX, HarnessId.GROK]
    by_id = {p.harness: p for p in seeded.profiles}
    assert "ANTHROPIC_API_KEY" in by_id[HarnessId.CLAUDE_CODE].environment.conflicts
    assert "CODEX_API_KEY" in by_id[HarnessId.CODEX].environment.conflicts
    assert "XAI_API_KEY" in by_id[HarnessId.GROK].environment.conflicts
    for profile in seeded.profiles:
        assert "HTTP_PROXY" in profile.environment.conflicts
        assert "http_proxy" in profile.environment.conflicts
        assert profile.proxy_policy is ProxyPolicy.INHERIT
        assert profile.auth_mode.value == "native-subscription"
        # capability rows are seeded at observed/unverified only (no probe ran)
        assert all(r.verification.value in {"observed", "unverified"} for r in profile.capabilities)
    assert by_id[HarnessId.CLAUDE_CODE].environment.config_home_variable == "CLAUDE_CONFIG_DIR"
    assert by_id[HarnessId.CODEX].environment.config_home_variable == "CODEX_HOME"
    assert by_id[HarnessId.GROK].environment.config_home_variable == "GROK_HOME"


def test_omitted_proxy_policy_keeps_safe_legacy_default() -> None:
    profile = HarnessProfileV1.model_validate(
        {
            "harness": "codex",
            "executable": "codex",
            "config_home": "/vendors/codex",
            "environment": {"config_home_variable": "CODEX_HOME"},
        }
    )
    assert profile.proxy_policy is ProxyPolicy.DENY


def test_write_and_load_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "profiles.yaml"
    write_profile_set(path, seed_default_profiles())
    loaded = load_profile_set(path)
    assert [p.harness for p in loaded.profiles] == [
        HarnessId.CLAUDE_CODE,
        HarnessId.CODEX,
        HarnessId.GROK,
    ]
    if sys.platform != "win32":
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    assert not list(tmp_path.glob(".profiles.yaml.*.tmp"))


def test_load_rejects_unknown_fields(tmp_path: Path) -> None:
    path = tmp_path / "profiles.yaml"
    data = {"schema_version": 1, "kind": "harness-profile-set", "profiles": [], "surprise": 1}
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(ProfileError, match="surprise"):
        load_profile_set(path)


def test_relative_paths_resolve_against_the_profile_file(tmp_path: Path) -> None:
    profile_dir = tmp_path / "examples" / "profiles"
    profile_dir.mkdir(parents=True)
    data = {
        "schema_version": 1,
        "kind": "harness-profile-set",
        "profiles": [
            {
                "harness": "codex",
                "executable": "../../fakes/fake_codex.py",
                "config_home": ".local/vendors/codex",
                "environment": {"config_home_variable": "CODEX_HOME"},
            }
        ],
    }
    path = profile_dir / "ci-fake.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    loaded = load_profile_set(path)
    profile = loaded.profiles[0]
    assert resolve_profile_path(path, profile.executable) == (tmp_path / "fakes" / "fake_codex.py")
    assert resolve_profile_path(path, profile.config_home) == (
        profile_dir / ".local" / "vendors" / "codex"
    )
    # absolute stays absolute (use a real absolute path: "/abs/x" has no
    # drive on Windows and is only drive-relative there); ~ expands
    absolute = tmp_path / "somewhere" / "else"
    assert resolve_profile_path(path, str(absolute)) == absolute
    assert resolve_profile_path(path, "~/x") == Path.home() / "x"


def test_default_profile_path_honours_agentteam_home(tmp_path: Path) -> None:
    assert default_profile_path({"AGENTTEAM_HOME": str(tmp_path)}) == tmp_path / "profiles.yaml"
    assert default_profile_path({}) == Path.home() / ".agentteam" / "profiles.yaml"
