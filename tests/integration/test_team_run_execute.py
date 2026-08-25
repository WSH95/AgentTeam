"""M1b TeamRun lifecycle over local coordination and deterministic fakes."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml
from typer.testing import CliRunner

from agentteam.cli import app
from agentteam.run.archive import RunArchive

runner = CliRunner()
REPO_ROOT = Path(__file__).resolve().parents[2]
REQUEST = REPO_ROOT / "examples" / "run-requests" / "team-review.yaml"
CI_FAKE = REPO_ROOT / "examples" / "profiles" / "ci-fake.yaml"


def _invoke(out: Path, *, render_only: bool = False, env: dict[str, str] | None = None) -> Any:
    args = [
        "run",
        str(REQUEST),
        "--config",
        str(CI_FAKE),
        "--output-dir",
        str(out),
        "--json",
    ]
    if render_only:
        args.append("--render-only")
    return runner.invoke(app, args, env={"FAKE_MODE": "ok", **(env or {})})


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _events(out: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line) for line in (out / "events.jsonl").read_text(encoding="utf-8").splitlines()
    ]


def test_three_member_team_run_closes_the_full_publication_pipeline(tmp_path: Path) -> None:
    out = tmp_path / "team-run"
    result = _invoke(out)
    assert result.exit_code == 0, result.output

    run = _json(out / "run.json")
    assert run["mode"] == "team"
    assert run["status"] == "succeeded"
    assert [row["name"] for row in run["members"]] == [
        "lead",
        "implementer",
        "reviewer",
    ]
    assert {row["name"]: row["selection"]["decided_by"] for row in run["members"]} == {
        "lead": "assistant",
        "implementer": "team",
        "reviewer": "assistant",
    }
    assert [row["status"] for row in run["tasks"]] == [
        "completed",
        "completed",
        "completed",
    ]
    assert [row["substrate_id"] for row in run["tasks"]] == ["t-1", "t-2", "t-3"]
    assert [row["workspace_access"] for row in run["tasks"]] == [
        "read-only",
        "workspace-write",
        "read-only",
    ]
    assert run["substrate"]["namespace"] == "space"
    snapshot = out / run["substrate"]["snapshot"]["path"]
    assert (
        hashlib.sha256(snapshot.read_bytes()).hexdigest() == run["substrate"]["snapshot"]["sha256"]
    )

    for member in ("lead", "implementer", "reviewer"):
        leg = out / "legs" / f"inv-{member}"
        invocation = _json(leg / "invocation.json")
        assert invocation["status"] == "succeeded"
        assert invocation["schema_outcome"] == "valid"
        assert invocation["target"]["before"]
        assert invocation["target"]["after"]
        assert _json(leg / "member-result.json")["kind"] == "member-result"
        assert any(item["role"] == "member-result" for item in invocation["artifacts"])

    lead_invocation = _json(out / "legs/inv-lead/invocation.json")
    implement_invocation = _json(out / "legs/inv-implementer/invocation.json")
    review_invocation = _json(out / "legs/inv-reviewer/invocation.json")
    assert lead_invocation["target"]["before"] == lead_invocation["target"]["after"]
    assert implement_invocation["target"]["before"] != implement_invocation["target"]["after"]
    assert review_invocation["target"]["before"] == review_invocation["target"]["after"]

    deliverable = out / "legs/inv-implementer/deliverables/implementation.txt"
    materialized = out / "legs/inv-reviewer/workspace/handoff/implement/implementation.txt"
    assert deliverable.read_bytes() == materialized.read_bytes()
    assert _json(out / "legs/inv-implementer/invocation.render.json")["command"][
        "argv_redacted"
    ] >= ["-s", "workspace-write"]

    ledger = [
        json.loads(line)
        for line in (out / "coordination/messages.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert len(ledger) == 1
    assert ledger[0]["sender"] == "lead" and ledger[0]["recipient"] == "implementer"
    implement_task = (out / "legs/inv-implementer/task.md").read_text(encoding="utf-8")
    review_task = (out / "legs/inv-reviewer/task.md").read_text(encoding="utf-8")
    assert ledger[0]["body"] in implement_task
    assert "handoff blinded by declared independence: artifact only" in review_task
    assert "Completed the assigned team task." not in review_task

    events = _events(out)
    names = [event["event"] for event in events]
    assert names.count("processes-stopped") == 1
    assert names.count("provider-cleanup") == 1
    starts = [event["member"] for event in events if event["event"] == "leg-started"]
    assert starts == ["lead", "implementer", "reviewer"]
    for predecessor, successor in (("plan", "implement"), ("implement", "review")):
        completed = next(
            index
            for index, event in enumerate(events)
            if event["event"] == "task-completed" and event["task_id"] == predecessor
        )
        successor_start = next(
            index
            for index, event in enumerate(events)
            if event["event"] == "leg-started" and event["task_id"] == successor
        )
        assert completed < successor_start
    assert RunArchive(out).verify_manifest() == []


def test_team_render_only_is_state_free(tmp_path: Path) -> None:
    out = tmp_path / "render"
    result = _invoke(out, render_only=True)
    assert result.exit_code == 0, result.output
    assert not (out / "run.json").exists()
    assert not (out / "coordination").exists()
    for member in ("lead", "implementer", "reviewer"):
        assert (out / member / "invocation.render.json").is_file()
        assert not (out / member / "invocation.json").exists()


def test_team_mode_rejects_direct_run_shaping_flags(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "run",
            str(REQUEST),
            "--config",
            str(CI_FAKE),
            "--output-dir",
            str(tmp_path / "out"),
            "--harness",
            "codex",
        ],
    )
    assert result.exit_code == 2
    assert "members map" in result.output
    assert not (tmp_path / "out").exists()


def test_invalid_member_result_cascades_without_launching_successors(tmp_path: Path) -> None:
    out = tmp_path / "failed"
    result = _invoke(out, env={"FAKE_MODE_CLAUDE": "schema-invalid"})
    assert result.exit_code == 1, result.output
    run = _json(out / "run.json")
    assert [row["status"] for row in run["tasks"]] == [
        "failed",
        "abandoned",
        "abandoned",
    ]
    assert (out / "legs/inv-lead/invocation.json").is_file()
    assert _json(out / "legs/inv-lead/invocation.json")["schema_outcome"] == "invalid"
    assert not (out / "legs/inv-implementer/invocation.json").exists()
    assert not (out / "legs/inv-reviewer/invocation.json").exists()
    assert RunArchive(out).verify_manifest() == []


@pytest.mark.parametrize(
    "mode",
    [
        "team-missing",
        "team-directory",
        "team-duplicate",
        "team-case-collision",
        "team-nonnfc",
        "team-handoff-reserved",
        pytest.param(
            "team-symlink",
            marks=pytest.mark.skipif(sys.platform == "win32", reason="symlink privilege varies"),
        ),
        pytest.param(
            "team-parent-symlink",
            marks=pytest.mark.skipif(sys.platform == "win32", reason="symlink privilege varies"),
        ),
    ],
)
def test_unsafe_declared_deliverable_fails_its_invocation(tmp_path: Path, mode: str) -> None:
    out = tmp_path / mode
    result = _invoke(out, env={"FAKE_MODE_CODEX": mode})
    assert result.exit_code == 1, result.output
    run = _json(out / "run.json")
    assert [row["status"] for row in run["tasks"]] == [
        "completed",
        "failed",
        "abandoned",
    ]
    invocation = _json(out / "legs/inv-implementer/invocation.json")
    assert invocation["status"] == "failed"
    assert invocation["schema_outcome"] == "valid"
    assert not (out / "legs/inv-reviewer/invocation.json").exists()
    assert RunArchive(out).verify_manifest() == []


def test_undeclared_member_write_is_inert_but_recorded(tmp_path: Path) -> None:
    out = tmp_path / "undeclared"
    result = _invoke(out, env={"FAKE_MODE_CODEX": "mutate-target"})
    assert result.exit_code == 0, result.output
    invocation = _json(out / "legs/inv-implementer/invocation.json")
    assert invocation["target"]["before"] != invocation["target"]["after"]
    assert not (out / "legs/inv-implementer/deliverables/fake-mutation.txt").exists()
    assert not (out / "legs/inv-reviewer/workspace/handoff/implement/fake-mutation.txt").exists()


def test_forward_reference_declaration_registers_in_stable_topological_order(
    tmp_path: Path,
) -> None:
    template_path = tmp_path / "forward.yaml"
    reviewer = os.path.relpath(
        REPO_ROOT / "examples/assistants/code-reviewer", template_path.parent
    )
    implementer = os.path.relpath(
        REPO_ROOT / "examples/assistants/implementer", template_path.parent
    )
    source = yaml.safe_load(
        (REPO_ROOT / "examples/teams/development.yaml").read_text(encoding="utf-8")
    )
    source["members"][0]["assistant"] = reviewer
    source["members"][1]["assistant"] = implementer
    source["members"][2]["assistant"] = reviewer
    source["workflow_skeleton"] = list(reversed(source["workflow_skeleton"]))
    template_path.write_text(yaml.safe_dump(source, sort_keys=False), encoding="utf-8")

    request_path = tmp_path / "forward-request.yaml"
    request = yaml.safe_load(REQUEST.read_text(encoding="utf-8"))
    request.update(
        {
            "template": str(template_path),
            "workspace": str(REPO_ROOT / "fixtures/review-target"),
            "task_file": str(REPO_ROOT / "examples/run-requests/review-task.md"),
        }
    )
    request_path.write_text(yaml.safe_dump(request, sort_keys=False), encoding="utf-8")
    out = tmp_path / "forward-run"
    result = runner.invoke(
        app,
        [
            "run",
            str(request_path),
            "--config",
            str(CI_FAKE),
            "--output-dir",
            str(out),
        ],
        env={"FAKE_MODE": "ok"},
    )
    assert result.exit_code == 0, result.output
    created = [event["task_id"] for event in _events(out) if event["event"] == "task-created"]
    assert created == ["plan", "implement", "review"]
    run = _json(out / "run.json")
    assert [row["id"] for row in run["tasks"]] == ["review", "implement", "plan"]
    assert [row["substrate_id"] for row in reversed(run["tasks"])] == [
        "t-1",
        "t-2",
        "t-3",
    ]


def test_pending_clawteam_disposition_fails_before_archive(tmp_path: Path) -> None:
    request_path = tmp_path / "clawteam.yaml"
    request = yaml.safe_load(REQUEST.read_text(encoding="utf-8"))
    request["template"] = str(REPO_ROOT / "examples/teams/development.yaml")
    request["workspace"] = str(REPO_ROOT / "fixtures/review-target")
    request["task_file"] = str(REPO_ROOT / "examples/run-requests/review-task.md")
    request["substrate"] = "clawteam"
    request_path.write_text(yaml.safe_dump(request, sort_keys=False), encoding="utf-8")
    out = tmp_path / "must-not-exist"
    result = runner.invoke(
        app,
        [
            "run",
            str(request_path),
            "--config",
            str(CI_FAKE),
            "--output-dir",
            str(out),
        ],
    )
    assert result.exit_code == 2
    assert "disposition: pending" in result.output
    assert not out.exists()
