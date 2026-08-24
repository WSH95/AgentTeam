"""Credential-blind, owner-only profile initialization."""

from __future__ import annotations

import stat
import sys
from pathlib import Path

import pytest

from agentteam.profile.setup import initialize_profiles
from agentteam.resolution.profiles import ProfileError


def test_init_is_owner_only_and_prints_platform_safe_commands(tmp_path: Path) -> None:
    result = initialize_profiles(tmp_path / "profiles.yaml")
    if sys.platform == "win32":
        # PowerShell form: $env:VAR = '<home>'; & '<exe>' '<arg>' ...
        assert result.login_commands[0].endswith("& 'claude' 'auth' 'login'")
        assert result.login_commands[1].endswith("& 'codex' 'login'")
        assert result.login_commands[2].endswith("& 'grok' 'login' '--oauth'")
        assert all(command.startswith("$env:") for command in result.login_commands)
    else:
        assert result.login_commands[0].endswith("claude auth login")
        assert result.login_commands[1].endswith("codex login")
        assert result.login_commands[2].endswith("grok login --oauth")
        assert all(
            "_HOME=" in command or "CLAUDE_CONFIG_DIR=" in command
            for command in result.login_commands
        )
    if sys.platform != "win32":
        assert stat.S_IMODE(result.profile_file.stat().st_mode) == 0o600
        assert stat.S_IMODE((tmp_path / "vendors").stat().st_mode) == 0o700
        for home in result.config_homes:
            assert stat.S_IMODE(home.stat().st_mode) == 0o700
        for path in (
            result.config_homes[1] / "config.toml",
            result.config_homes[2] / "config.toml",
        ):
            assert stat.S_IMODE(path.stat().st_mode) == 0o600

    windows = initialize_profiles(tmp_path / "windows" / "profiles.yaml", platform="win32")
    assert windows.login_commands[0].startswith("$env:CLAUDE_CONFIG_DIR = '")
    assert "; & 'claude' 'auth' 'login'" in windows.login_commands[0]
    assert windows.login_commands[2].endswith("& 'grok' 'login' '--oauth'")


def test_init_refuses_symlinked_home_before_writing_profile(tmp_path: Path) -> None:
    if sys.platform == "win32":
        pytest.skip("symlink setup is privilege-dependent on Windows")
    target = tmp_path / "elsewhere"
    target.mkdir()
    vendors = tmp_path / "vendors"
    vendors.mkdir()
    (vendors / "codex").symlink_to(target, target_is_directory=True)
    path = tmp_path / "profiles.yaml"
    with pytest.raises(ProfileError, match="symlink"):
        initialize_profiles(path)
    assert not path.exists()


def test_init_refuses_unmanaged_claude_skills_and_existing_vendor_config(
    tmp_path: Path,
) -> None:
    skills = tmp_path / "vendors" / "claude-code" / "skills"
    skills.mkdir(parents=True)
    precious = skills / "owner-skill.md"
    precious.write_text("keep\n", encoding="utf-8")
    path = tmp_path / "profiles.yaml"
    with pytest.raises(ProfileError, match="unmarked"):
        initialize_profiles(path)
    assert precious.read_text(encoding="utf-8") == "keep\n"
    assert not path.exists()

    precious.unlink()
    codex_config = tmp_path / "vendors" / "codex" / "config.toml"
    codex_config.parent.mkdir(parents=True)
    codex_config.write_text("owner = true\n", encoding="utf-8")
    with pytest.raises(ProfileError, match="overwrite"):
        initialize_profiles(path)
    assert codex_config.read_text(encoding="utf-8") == "owner = true\n"
    assert not path.exists()
