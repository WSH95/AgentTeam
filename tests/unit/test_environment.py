"""Child-environment construction (plan section 9): baseline allowlist, conflicts fail closed."""

from __future__ import annotations

import pytest

from agentteam.domain.profile import HarnessProfileV1, ProxyPolicy
from agentteam.harness.environment import EnvironmentConflictError, build_environment


def _profile(**env_overrides: object) -> HarnessProfileV1:
    env: dict[str, object] = {
        "config_home_variable": "CODEX_HOME",
        "passthrough": ["FAKE_OBSERVE"],
        "conflicts": ["CODEX_API_KEY", "HTTP_PROXY", "http_proxy"],
    }
    env.update(env_overrides)
    return HarnessProfileV1.model_validate(
        {
            "harness": "codex",
            "executable": "codex",
            "config_home": "/vendors/codex",
            "environment": env,
        }
    )


PARENT = {
    "HOME": "/home/u",
    "PATH": "/usr/bin",
    "TMPDIR": "/tmp",
    "LANG": "C.UTF-8",
    "SHELL": "/bin/bash",  # not in the baseline; must not leak
    "FAKE_OBSERVE": "/tmp/obs.json",
    "SECRET_THING": "x",  # must not leak
}


def test_posix_baseline_plus_config_home_and_passthrough_only() -> None:
    env, record = build_environment(_profile(), PARENT, platform="linux")
    assert env == {
        "HOME": "/home/u",
        "PATH": "/usr/bin",
        "TMPDIR": "/tmp",
        "LANG": "C.UTF-8",
        "FAKE_OBSERVE": "/tmp/obs.json",
        "CODEX_HOME": "/vendors/codex",
    }
    assert record.config_home_variable == "CODEX_HOME"
    assert sorted(env) == record.names  # names only, never values
    assert record.conflicts_detected == []


def test_windows_baseline_names() -> None:
    parent = {
        name: "v"
        for name in [
            "PATH",
            "SystemRoot",
            "SystemDrive",
            "COMSPEC",
            "PATHEXT",
            "USERPROFILE",
            "APPDATA",
            "LOCALAPPDATA",
            "TEMP",
            "TMP",
            "HOME",
        ]
    }
    env, _ = build_environment(_profile(), parent, platform="win32")
    assert "USERPROFILE" in env and "COMSPEC" in env
    assert "HOME" not in env  # POSIX-only name


def test_missing_baseline_names_are_simply_absent() -> None:
    env, _ = build_environment(_profile(), {"PATH": "/usr/bin"}, platform="linux")
    assert env == {"PATH": "/usr/bin", "CODEX_HOME": "/vendors/codex"}


def test_conflict_variable_fails_closed() -> None:
    with pytest.raises(EnvironmentConflictError, match="CODEX_API_KEY"):
        build_environment(_profile(), {**PARENT, "CODEX_API_KEY": "k"}, platform="linux")


def test_proxy_conflict_fails_closed_under_deny() -> None:
    with pytest.raises(EnvironmentConflictError, match="http_proxy"):
        build_environment(_profile(), {**PARENT, "http_proxy": "http://p"}, platform="linux")


def test_proxy_policy_inherit_passes_proxies_through() -> None:
    profile = _profile()
    profile = profile.model_copy(update={"proxy_policy": ProxyPolicy.INHERIT})
    env, record = build_environment(profile, {**PARENT, "HTTP_PROXY": "http://p"}, platform="linux")
    assert env["HTTP_PROXY"] == "http://p"
    assert record.conflicts_detected == []


def test_non_proxy_conflicts_still_fail_under_inherit() -> None:
    profile = _profile().model_copy(update={"proxy_policy": ProxyPolicy.INHERIT})
    with pytest.raises(EnvironmentConflictError, match="CODEX_API_KEY"):
        build_environment(profile, {**PARENT, "CODEX_API_KEY": "k"}, platform="linux")


def test_error_carries_every_offending_name() -> None:
    with pytest.raises(EnvironmentConflictError) as excinfo:
        build_environment(
            _profile(), {**PARENT, "CODEX_API_KEY": "k", "HTTP_PROXY": "p"}, platform="linux"
        )
    assert excinfo.value.names == ["CODEX_API_KEY", "HTTP_PROXY"]
