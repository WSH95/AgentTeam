"""Child-environment construction (plan sections 9 and 11).

Each native run starts from a minimal cross-platform allowlist, sets the
selected config-home variable, records names only, and fails closed when a
conflict variable (API key, base URL, alternate provider, unapproved proxy) is
set in the parent environment. Standard proxy names are policy data: an
``inherit`` profile passes their values through unchanged, while ``deny``
keeps them fail-closed. Other conflict names remain profile data.
"""

from __future__ import annotations

from collections.abc import Mapping

from agentteam.domain.profile import HarnessProfileV1, ProxyPolicy
from agentteam.domain.run import EnvironmentV1

POSIX_BASELINE = ("HOME", "PATH", "TMPDIR", "LANG")
WINDOWS_BASELINE = (
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
)

# Generic proxy names; under proxy_policy=inherit these conflict names become
# passthrough instead of failing closed.
PROXY_NAMES = frozenset(
    name
    for base in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY")
    for name in (base, base.lower())
)


def baseline_environment(parent: Mapping[str, str], *, platform: str) -> dict[str, str]:
    """The platform baseline subset of ``parent``, canonically spelled.

    Windows environment names are case-insensitive at the OS level, and a
    plain ``dict(os.environ)`` carries them upper-cased — the mixed-case
    baseline names (``SystemRoot``, ``SystemDrive``) must therefore match
    case-insensitively on win32: a child without ``SystemRoot`` cannot even
    start node.exe (G7 vendor smoke, run 32764994137).
    """
    baseline = WINDOWS_BASELINE if platform == "win32" else POSIX_BASELINE
    if platform != "win32":
        return {name: parent[name] for name in baseline if name in parent}
    by_upper = {key.upper(): key for key in parent}
    child: dict[str, str] = {}
    for name in baseline:
        actual = by_upper.get(name.upper())
        if actual is not None:
            child[name] = parent[actual]
    return child


class EnvironmentConflictError(ValueError):
    """A conflict variable is set; native runs fail closed (exit 2)."""

    def __init__(self, names: list[str]) -> None:
        super().__init__(
            "environment variables that could redirect native authentication are set: "
            + ", ".join(names)
            + " (unset them, or change the profile's conflict/proxy policy)"
        )
        self.names = names


def inherited_proxy_names(
    profile: HarnessProfileV1,
    parent: Mapping[str, str],
) -> list[str]:
    """Return present standard proxy names approved for inheritance.

    Values deliberately stay in ``parent`` and are never returned or recorded.
    """
    if profile.proxy_policy is not ProxyPolicy.INHERIT:
        return []
    return sorted(name for name in PROXY_NAMES if name in parent)


def conflicting_environment_names(
    profile: HarnessProfileV1,
    parent: Mapping[str, str],
) -> list[str]:
    """Return set conflict names after applying the profile's proxy policy."""
    conflicts = set(profile.environment.conflicts)
    if profile.proxy_policy is ProxyPolicy.INHERIT:
        conflicts.difference_update(PROXY_NAMES)
    else:
        conflicts.update(PROXY_NAMES)
    return sorted(name for name in conflicts if name in parent)


def build_environment(
    profile: HarnessProfileV1,
    parent: Mapping[str, str],
    *,
    platform: str,
) -> tuple[dict[str, str], EnvironmentV1]:
    """Build the child env from scratch; return it with its names-only record."""
    offending = conflicting_environment_names(profile, parent)
    if offending:
        raise EnvironmentConflictError(offending)

    child = baseline_environment(parent, platform=platform)
    for name in profile.environment.passthrough:
        if name in parent:
            child[name] = parent[name]
    for name in inherited_proxy_names(profile, parent):
        child[name] = parent[name]
    child[profile.environment.config_home_variable] = profile.config_home

    record = EnvironmentV1(
        names=sorted(child),
        config_home_variable=profile.environment.config_home_variable,
        conflicts_detected=[],
    )
    return child, record
