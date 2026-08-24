"""Child-environment construction (plan section 9): baseline allowlist, conflicts fail closed."""

from __future__ import annotations

import json

import pytest

from agentteam.domain.profile import HarnessProfileV1, ProxyPolicy
from agentteam.harness.diagnostics import diagnostic_environment
from agentteam.harness.environment import (
    PROXY_NAMES,
    EnvironmentConflictError,
    build_environment,
)


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


def test_proxy_deny_fails_closed_even_when_conflict_list_omits_proxy_names() -> None:
    profile = _profile(conflicts=["CODEX_API_KEY"])
    with pytest.raises(EnvironmentConflictError, match="NO_PROXY"):
        build_environment(profile, {**PARENT, "NO_PROXY": "localhost"}, platform="linux")


def test_proxy_policy_inherit_passes_all_present_proxies_unchanged() -> None:
    proxy_values = {name: f"sensitive-{index}" for index, name in enumerate(PROXY_NAMES)}
    profile = _profile(conflicts=["CODEX_API_KEY"]).model_copy(
        update={"proxy_policy": ProxyPolicy.INHERIT}
    )
    env, record = build_environment(profile, {**PARENT, **proxy_values}, platform="linux")
    assert {name: env[name] for name in PROXY_NAMES} == proxy_values
    assert record.conflicts_detected == []
    record_json = json.dumps(record.model_dump(mode="json"))
    assert all(value not in record_json for value in proxy_values.values())


def test_diagnostic_environment_obeys_proxy_policy() -> None:
    parent = {**PARENT, "HTTP_PROXY": "http://proxy", "NO_PROXY": "localhost"}
    inherited = _profile().model_copy(update={"proxy_policy": ProxyPolicy.INHERIT})
    inherited_env = diagnostic_environment(inherited, parent, platform="linux")
    assert inherited_env["HTTP_PROXY"] == "http://proxy"
    assert inherited_env["NO_PROXY"] == "localhost"

    denied_env = diagnostic_environment(_profile(), parent, platform="linux")
    assert "HTTP_PROXY" not in denied_env
    assert "NO_PROXY" not in denied_env


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
