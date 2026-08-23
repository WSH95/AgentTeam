"""Child-environment construction (plan sections 9 and 11).

Each native run starts from a minimal cross-platform allowlist, sets the
selected config-home variable, records names only, and fails closed when a
conflict variable (API key, base URL, alternate provider, unapproved proxy) is
set in the parent environment. Conflict names are profile data, never
hardcoded vendor knowledge.
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


class EnvironmentConflictError(ValueError):
    """A conflict variable is set; native runs fail closed (exit 2)."""

    def __init__(self, names: list[str]) -> None:
        super().__init__(
            "environment variables that could redirect native authentication are set: "
            + ", ".join(names)
            + " (unset them, or change the profile's conflict/proxy policy)"
        )
        self.names = names


def build_environment(
    profile: HarnessProfileV1,
    parent: Mapping[str, str],
    *,
    platform: str,
) -> tuple[dict[str, str], EnvironmentV1]:
    """Build the child env from scratch; return it with its names-only record."""
    conflicts = list(profile.environment.conflicts)
    inherit_proxies = profile.proxy_policy is ProxyPolicy.INHERIT
    effective_conflicts = [
        name for name in conflicts if not (inherit_proxies and name in PROXY_NAMES)
    ]
    offending = sorted(name for name in effective_conflicts if name in parent)
    if offending:
        raise EnvironmentConflictError(offending)

    baseline = WINDOWS_BASELINE if platform == "win32" else POSIX_BASELINE
    child: dict[str, str] = {}
    for name in baseline:
        if name in parent:
            child[name] = parent[name]
    for name in profile.environment.passthrough:
        if name in parent:
            child[name] = parent[name]
    if inherit_proxies:
        for name in sorted(PROXY_NAMES):
            if name in conflicts and name in parent:
                child[name] = parent[name]
    child[profile.environment.config_home_variable] = profile.config_home

    record = EnvironmentV1(
        names=sorted(child),
        config_home_variable=profile.environment.config_home_variable,
        conflicts_detected=[],
    )
    return child, record
