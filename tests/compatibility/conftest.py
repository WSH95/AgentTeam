"""Compatibility-suite fixtures (plan section 10).

The whole directory skips cleanly when the `clawteam` extra is absent. Every
test runs against a temporary HOME and a temporary data root — the owner's
real `~/.clawteam` is captured before any patching and asserted untouched
when the suite ends.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

clawteam = pytest.importorskip("clawteam")

# Captured at collection time, before any test patches HOME.
_REAL_CLAWTEAM = Path.home() / ".clawteam"
_REAL_EXISTED = _REAL_CLAWTEAM.exists()
_REAL_MTIME = _REAL_CLAWTEAM.stat().st_mtime_ns if _REAL_EXISTED else None


@pytest.fixture(scope="session", autouse=True)
def owner_state_stays_untouched() -> Iterator[None]:
    yield
    exists_now = _REAL_CLAWTEAM.exists()
    assert exists_now == _REAL_EXISTED, "the suite created or removed ~/.clawteam"
    if _REAL_EXISTED:
        assert _REAL_CLAWTEAM.stat().st_mtime_ns == _REAL_MTIME, "the suite modified ~/.clawteam"


@dataclass(frozen=True)
class SeamEnv:
    home: Path
    data_root: Path


@pytest.fixture()
def seam_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[SeamEnv]:
    from agentteam.compat.clawteam import ClawTeamCompat

    home = tmp_path / "home"
    home.mkdir()
    data_root = tmp_path / "data"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    for name in ("CLAWTEAM_DATA_DIR", "CLAWTEAM_TRANSPORT", "CLAWTEAM_USER"):
        monkeypatch.delenv(name, raising=False)
    ClawTeamCompat._reset_for_tests()
    yield SeamEnv(home=home, data_root=data_root)
    ClawTeamCompat._reset_for_tests()
    assert "CLAWTEAM_DATA_DIR" not in os.environ
