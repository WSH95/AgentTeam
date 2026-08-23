"""Profile-set loading, seeding, and profile-relative path resolution."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from agentteam.domain.common import HarnessId
from agentteam.resolution.profiles import (
    ProfileError,
    default_profile_path,
    load_profile_set,
    resolve_profile_path,
    seed_default_profiles,
    write_profile_set,
)


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
        assert profile.auth_mode.value == "native-subscription"
        # capability rows are seeded at observed/unverified only (no probe ran)
        assert all(r.verification.value in {"observed", "unverified"} for r in profile.capabilities)
    assert by_id[HarnessId.CLAUDE_CODE].environment.config_home_variable == "CLAUDE_CONFIG_DIR"
    assert by_id[HarnessId.CODEX].environment.config_home_variable == "CODEX_HOME"
    assert by_id[HarnessId.GROK].environment.config_home_variable == "GROK_HOME"


def test_write_and_load_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "profiles.yaml"
    write_profile_set(path, seed_default_profiles())
    loaded = load_profile_set(path)
    assert [p.harness for p in loaded.profiles] == [
        HarnessId.CLAUDE_CODE,
        HarnessId.CODEX,
        HarnessId.GROK,
    ]


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
    # absolute stays absolute; ~ expands
    assert resolve_profile_path(path, "/abs/x").as_posix() == "/abs/x"
    assert resolve_profile_path(path, "~/x") == Path.home() / "x"


def test_default_profile_path_honours_agentteam_home(tmp_path: Path) -> None:
    assert default_profile_path({"AGENTTEAM_HOME": str(tmp_path)}) == tmp_path / "profiles.yaml"
    assert default_profile_path({}) == Path.home() / ".agentteam" / "profiles.yaml"
