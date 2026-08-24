"""Persistent Claude Skill channel ownership and cross-process lease tests."""

from __future__ import annotations

import multiprocessing
import sys
import time
from pathlib import Path
from typing import Any

import pytest

from agentteam.harness.rendering import RenderError
from agentteam.harness.skills import MARKER, ManagedSkillsLease


def _hold_lease(home: str, ready: Any, release: Any) -> None:
    with ManagedSkillsLease(Path(home)):
        ready.set()
        release.wait(5)


def _measure_wait(home: str, result: Any) -> None:
    started = time.monotonic()
    with ManagedSkillsLease(Path(home)):
        result.put(time.monotonic() - started)


def test_managed_lease_cleans_only_the_marked_skill_root(tmp_path: Path) -> None:
    home = tmp_path / "claude"
    skills = home / "skills"
    skills.mkdir(parents=True)
    precious = skills / "owner-skill.md"
    precious.write_text("keep\n", encoding="utf-8")
    with pytest.raises(RenderError, match="unmanaged"):
        ManagedSkillsLease(home).acquire()
    assert precious.read_text(encoding="utf-8") == "keep\n"

    precious.unlink()
    with ManagedSkillsLease(home):
        (skills / MARKER).write_text("managed\n", encoding="utf-8")
        generated = skills / "generated"
        generated.mkdir()
        (generated / "SKILL.md").write_text("generated\n", encoding="utf-8")
    assert sorted(path.name for path in skills.iterdir()) == [MARKER]


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX flock timing assertion")
def test_managed_lease_serializes_processes(tmp_path: Path) -> None:
    context = multiprocessing.get_context("fork")
    ready = context.Event()
    release = context.Event()
    result = context.Queue()
    first = context.Process(target=_hold_lease, args=(str(tmp_path), ready, release))
    first.start()
    assert ready.wait(3)
    second = context.Process(target=_measure_wait, args=(str(tmp_path), result))
    second.start()
    time.sleep(0.2)
    assert second.is_alive()
    release.set()
    first.join(3)
    second.join(3)
    assert first.exitcode == 0
    assert second.exitcode == 0
    assert result.get(timeout=1) >= 0.15
