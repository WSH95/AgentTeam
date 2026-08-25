"""Hostile-hook containment (plan section 10 item 4).

A user-configured shell hook in the (patched) home's config.json would run on
`AfterTaskUpdate` via the global bus's config-hook loader. The seam replaces
the bus and marks the loader spent before any operation — the hook callback
must never execute.
"""

from __future__ import annotations

import json
import sys
import time
from typing import Any

from agentteam.compat.clawteam import ClawTeamCompat


def _plant_hostile_hook(seam_env: Any, sentinel_name: str) -> Any:
    sentinel = seam_env.home / sentinel_name
    config_dir = seam_env.home / ".clawteam"
    config_dir.mkdir(parents=True)
    command = f"{sys.executable} -c \"open({str(sentinel)!r}, 'w').close()\""
    (config_dir / "config.json").write_text(
        json.dumps(
            {
                "hooks": [
                    {
                        "event": "AfterTaskUpdate",
                        "action": "shell",
                        "command": command,
                        "enabled": True,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return sentinel


def test_config_hooks_never_execute_through_the_seam(seam_env: Any) -> None:
    sentinel = _plant_hostile_hook(seam_env, "hook-fired")
    seam = ClawTeamCompat(seam_env.data_root)
    report = seam.hook_containment_report()
    assert report.bus_replaced is True
    assert report.subscriber_count == 0
    assert report.config_hook_loader_disarmed is True

    space = seam.create_space(leader="atm-lead")
    task_id = seam.create_task(space, "exercise the update event path")
    seam.update_task(space, task_id, "in_progress", caller="atm-lead")
    seam.update_task(space, task_id, "completed", caller="atm-lead")
    # events are emitted asynchronously outside the store lock; give the
    # 2-thread pool a moment — nothing can fire on a cleared bus, and the
    # state assertions above are the primary proof
    time.sleep(0.3)
    assert not sentinel.exists(), "a user-configured ClawTeam hook executed"
    after = seam.hook_containment_report()
    assert after.bus_replaced is True
    assert after.subscriber_count == 0


def test_the_loader_stays_spent_for_later_bus_requests(seam_env: Any) -> None:
    _plant_hostile_hook(seam_env, "hook-fired-late")
    seam = ClawTeamCompat(seam_env.data_root)
    from clawteam.events import global_bus

    bus = global_bus.get_event_bus()
    assert bus is ClawTeamCompat._bus
    subscribers = getattr(bus, "_subscribers", None)
    assert subscribers is not None
    assert len(subscribers) == 0
    again = global_bus.get_event_bus()
    assert again is bus
    report = seam.hook_containment_report()
    assert report.config_hook_loader_disarmed is True
