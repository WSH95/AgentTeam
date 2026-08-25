"""The complete section-13 lifecycle through the optional provider and public CLI."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml
from tests.acceptance.test_team_lifecycle import (
    CI_FAKE,
    REVIEW_TARGET,
    TEAM_REQUEST,
    TEAM_TEMPLATE,
    ProviderSnapshotProjection,
    assert_three_member_lifecycle,
)
from typer.testing import CliRunner

from agentteam.cli import app

runner = CliRunner()


def _project_snapshot(snapshot: dict[str, Any]) -> ProviderSnapshotProjection:
    status_map = {
        "blocked": "blocked",
        "pending": "pending",
        "in_progress": "running",
        "completed": "completed",
    }
    config = snapshot["config"]
    tasks = [
        {
            "id": row["id"],
            "subject": row["subject"],
            "status": status_map[row["status"]],
            "blocked_by": list(row["blockedBy"]),
        }
        for row in snapshot["tasks"]
    ]
    messages = [
        {"sender": row["from"], "recipient": row["to"], "body": row["content"]}
        for row in snapshot["events"]
        if row.get("type") == "message"
    ]
    return ProviderSnapshotProjection(
        namespace=str(config["name"]),
        members=[str(row["name"]) for row in config["members"]],
        tasks=tasks,
        messages=messages,
    )


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_three_member_clawteam_cli_lifecycle_satisfies_all_conditions(
    seam_env: Any,
    tmp_path: Path,
) -> None:
    request = yaml.safe_load(TEAM_REQUEST.read_text(encoding="utf-8"))
    request.update(
        {
            "template": str(TEAM_TEMPLATE),
            "workspace": str(REVIEW_TARGET),
            "task_file": str(TEAM_REQUEST.parent / "review-task.md"),
            "substrate": "clawteam",
        }
    )
    request_path = tmp_path / "clawteam-team-run.yaml"
    request_path.write_text(yaml.safe_dump(request, sort_keys=False), encoding="utf-8")
    out = tmp_path / "clawteam-team-acceptance"
    agentteam_home = seam_env.home / "agentteam-home"
    result = runner.invoke(
        app,
        [
            "run",
            str(request_path),
            "--config",
            str(CI_FAKE),
            "--output-dir",
            str(out),
            "--json",
        ],
        env={"AGENTTEAM_HOME": str(agentteam_home), "FAKE_MODE": "ok"},
    )
    assert result.exit_code == 0, result.output

    assert_three_member_lifecycle(
        out,
        project_snapshot=_project_snapshot,
        expected_substrate="clawteam",
        expected_achieved="namespace",
    )

    run = _load(out / "run.json")
    namespace = run["substrate"]["namespace"]
    provider_root = agentteam_home / "clawteam"
    assert not (provider_root / "snapshots" / namespace).exists()
    events = [
        json.loads(line) for line in (out / "events.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    stopped = next(index for index, row in enumerate(events) if row["event"] == "processes-stopped")
    cleaned = next(index for index, row in enumerate(events) if row["event"] == "provider-cleanup")
    assert stopped < cleaned

    forbidden_modules = {
        "clawteam.cli.commands",
        "clawteam.harness.spawner",
        "clawteam.spawn.keepalive",
        "clawteam.spawn.subprocess_backend",
        "clawteam.spawn.tmux_backend",
        "clawteam.spawn.wsh_backend",
    }
    assert forbidden_modules.isdisjoint(sys.modules)
