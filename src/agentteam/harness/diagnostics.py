"""Shell-free, no-model-call CLI diagnostics shared by doctor and preflight."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from agentteam.domain.profile import HarnessProfileV1
from agentteam.harness.environment import (
    baseline_environment,
    inherited_proxy_names,
)
from agentteam.harness.launcher import resolve_launcher


def diagnostic_environment(
    profile: HarnessProfileV1,
    parent: Mapping[str, str],
    *,
    platform: str,
) -> dict[str, str]:
    """Minimal child environment plus the already-resolved config home."""
    child = baseline_environment(parent, platform=platform)
    for name in profile.environment.passthrough:
        if name in parent:
            child[name] = parent[name]
    for name in inherited_proxy_names(profile, parent):
        child[name] = parent[name]
    child[profile.environment.config_home_variable] = profile.config_home
    return child


def capture_cli(
    profile: HarnessProfileV1,
    args: Sequence[str],
    *,
    parent: Mapping[str, str],
    platform: str = sys.platform,
    timeout_seconds: int = 20,
    cwd: Path | None = None,
) -> tuple[int | None, bytes, bytes]:
    """Capture one diagnostic command; timeout/launch failures become no result."""
    resolved = resolve_launcher(Path(profile.executable), list(args), platform=platform)
    if resolved.reason is not None:
        return None, b"", resolved.reason.encode("utf-8")
    try:
        completed = subprocess.run(
            resolved.argv,
            cwd=str(cwd or Path.cwd()),
            env=diagnostic_environment(profile, parent, platform=platform),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return None, b"", str(error).encode("utf-8", errors="replace")
    return completed.returncode, completed.stdout, completed.stderr


def capture_version(
    profile: HarnessProfileV1,
    *,
    parent: Mapping[str, str],
    platform: str = sys.platform,
) -> str | None:
    code, stdout, _stderr = capture_cli(profile, ["--version"], parent=parent, platform=platform)
    if code != 0:
        return None
    return stdout.decode("utf-8", errors="replace").strip() or None
