"""Deterministic three-member TeamRun acceptance (M1b plan section 13)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml
from typer.testing import CliRunner

from agentteam.cli import app
from agentteam.domain.run import TeamRunRecordV1
from agentteam.harness.types import FileWriteV1
from agentteam.resolution.archive import hash_package
from agentteam.resolution.team import hash_team_template, load_team_template
from agentteam.run.archive import RunArchive
from agentteam.run.workspace import exclusions_for, hash_tree

runner = CliRunner()
REPO_ROOT = Path(__file__).resolve().parents[2]
TEAM_REQUEST = REPO_ROOT / "examples" / "run-requests" / "team-review.yaml"
TEAM_TEMPLATE = REPO_ROOT / "examples" / "teams" / "development.yaml"
CI_FAKE = REPO_ROOT / "examples" / "profiles" / "ci-fake.yaml"
REVIEW_TARGET = REPO_ROOT / "fixtures" / "review-target"
ASSISTANTS = {
    "lead": REPO_ROOT / "examples" / "assistants" / "code-reviewer",
    "implementer": REPO_ROOT / "examples" / "assistants" / "implementer",
    "reviewer": REPO_ROOT / "examples" / "assistants" / "code-reviewer",
}
CLAUDE_READ_ALLOW = "Read,Grep,Glob,LS,Skill"
CLAUDE_READ_DENY = "Write,Edit,NotebookEdit,Bash,WebFetch,WebSearch"


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _jsonl(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert all(isinstance(row, dict) for row in rows)
    return rows


def _event(events: list[dict[str, Any]], event: str, **facts: object) -> tuple[int, dict[str, Any]]:
    matches = [
        (index, row)
        for index, row in enumerate(events)
        if row.get("event") == event and all(row.get(key) == value for key, value in facts.items())
    ]
    assert len(matches) == 1, (event, facts, matches)
    return matches[0]


def _option(argv: list[str], name: str) -> str:
    index = argv.index(name)
    return argv[index + 1]


def _target_hash(out: Path, member: str, rendered: dict[str, Any]) -> str:
    workspace = out / "legs" / f"inv-{member}" / "workspace"
    writes = [FileWriteV1.model_validate(row) for row in rendered["files_written"]]
    return hash_tree(workspace, exclude=exclusions_for(writes, workspace))


def test_three_member_cli_acceptance_satisfies_every_lifecycle_condition(
    tmp_path: Path,
) -> None:
    out = tmp_path / "team-acceptance"
    result = runner.invoke(
        app,
        [
            "run",
            str(TEAM_REQUEST),
            "--config",
            str(CI_FAKE),
            "--output-dir",
            str(out),
            "--json",
        ],
        env={"FAKE_MODE": "ok"},
    )
    assert result.exit_code == 0, result.output

    run = _load(out / "run.json")
    events = _jsonl(out / "events.jsonl")
    snapshot_path = out / run["substrate"]["snapshot"]["path"]
    snapshot = _load(snapshot_path)
    ledger = _jsonl(out / "coordination" / "messages.jsonl")
    template = load_team_template(TEAM_TEMPLATE)

    # 1. The authoritative run roster, committed template, and provider bundle agree.
    roster = [member.name for member in template.definition.members]
    assert roster == ["lead", "implementer", "reviewer"]
    assert [member["name"] for member in run["members"]] == roster
    assert snapshot["metadata"]["members"] == roster

    # 2. Every DAG task completed, with exact provider ids and remaining blockers.
    assert [task["status"] for task in run["tasks"]] == ["completed"] * 3
    provider_tasks = {task["id"]: task for task in snapshot["tasks"]}
    for task in run["tasks"]:
        provider = provider_tasks[task["substrate_id"]]
        assert provider["subject"] == task["subject"]
        assert provider["status"] == "completed"
        assert provider["blocked_by"] == []
    for predecessor, successor in (("plan", "implement"), ("implement", "review")):
        completed, _ = _event(events, "task-completed", task_id=predecessor)
        unblocked, _ = _event(events, "task-unblocked", task_id=successor)
        started, _ = _event(events, "leg-started", task_id=successor)
        assert completed < unblocked < started

    # 3. Every persisted/transported envelope stays inside the validated roster.
    assert ledger
    assert all({row["sender"], row["recipient"]} <= set(roster) for row in ledger)
    provider_envelopes = [row["message"] for row in snapshot["messages"]]
    assert all({row["sender"], row["recipient"]} <= set(roster) for row in provider_envelopes)

    # 4. The archived opaque bundle is digest-linked and reproduces provider state.
    assert snapshot["provider"] == "local"
    assert (
        hashlib.sha256(snapshot_path.read_bytes()).hexdigest()
        == run["substrate"]["snapshot"]["sha256"]
    )
    assert snapshot["metadata"]["id"] == run["substrate"]["namespace"]
    assert set(provider_tasks) == {task["substrate_id"] for task in run["tasks"]}
    assert [row["body"] for row in provider_envelopes] == [row["body"] for row in ledger]

    # 5. Every Member has an invocation binding, valid MemberResult, and exact grant.
    members = {member["name"]: member for member in run["members"]}
    invocations: dict[str, dict[str, Any]] = {}
    renders: dict[str, dict[str, Any]] = {}
    for member in roster:
        binding = members[member]["execution"]
        assert binding == {"kind": "invocation", "ref": f"inv-{member}"}
        leg = out / "legs" / binding["ref"]
        invocation = _load(leg / "invocation.json")
        rendered = _load(leg / "invocation.render.json")
        member_result = _load(leg / "member-result.json")
        invocations[member] = invocation
        renders[member] = rendered
        assert invocation["status"] == "succeeded"
        assert invocation["schema_outcome"] == "valid"
        assert (
            invocation["effective_definition_hash"] == members[member]["effective_definition_hash"]
        )
        assert member_result["kind"] == "member-result"
        artifacts = [row for row in invocation["artifacts"] if row["role"] == "member-result"]
        assert len(artifacts) == 1
        artifact_path = out / artifacts[0]["path"]
        assert artifact_path == leg / "member-result.json"
        assert hashlib.sha256(artifact_path.read_bytes()).hexdigest() == artifacts[0]["sha256"]
        assert rendered["command"]["launcher_policy"] == "python-script"
        assert any(Path(value).name.startswith("fake_") for value in rendered["argv"])

    assert {task["id"]: task["workspace_access"] for task in run["tasks"]} == {
        "plan": "read-only",
        "implement": "workspace-write",
        "review": "read-only",
    }
    for member in ("lead", "reviewer"):
        argv = renders[member]["command"]["argv_redacted"]
        assert renders[member]["harness"] == "claude-code"
        assert _option(argv, "--allowedTools") == CLAUDE_READ_ALLOW
        assert _option(argv, "--disallowedTools") == CLAUDE_READ_DENY
    implement_argv = renders["implementer"]["command"]["argv_redacted"]
    assert renders["implementer"]["harness"] == "codex"
    assert _option(implement_argv, "-s") == "workspace-write"
    assert "sandbox_workspace_write.network_access=false" in implement_argv

    # 6. The template layer decides the implementer and the run mixes harnesses.
    assert members["implementer"]["selection"]["decided_by"] == "team"
    assert len({rendered["harness"] for rendered in renders.values()}) >= 2

    # 7. Successful terminal lifecycle records the honest local isolation level.
    assert run["status"] == "succeeded"
    assert run["independence"] == {"declared": "advisory", "achieved": "data-dir"}
    assert run["substrate"]["namespace"]
    assert run["substrate"]["snapshot"]

    # 8. Portable definitions re-hash, while target facts reflect legal mutation.
    assert Path(run["template"]["ref"]).resolve() == TEAM_TEMPLATE.resolve()
    assert hash_team_template(template) == run["template"]["hash"]
    for member, package_root in ASSISTANTS.items():
        digest = hash_package(package_root).package_hash
        bundle = _load(out / "bundles" / f"{member}.json")
        assert members[member]["assistant"]["package_hash"] == digest
        assert members[member]["effective_definition_hash"] == digest
        assert bundle["effective_definition_hash"] == digest
    source_hash = hash_tree(REVIEW_TARGET)
    assert invocations["lead"]["target"] == {"before": source_hash, "after": source_hash}
    assert not (out / "legs" / "inv-implementer" / "workspace" / ".agents").exists()
    assert invocations["implementer"]["target"]["before"] == source_hash
    assert invocations["implementer"]["target"]["after"] != source_hash
    assert invocations["reviewer"]["target"]["before"] != source_hash
    assert invocations["reviewer"]["target"]["before"] == invocations["reviewer"]["target"]["after"]
    for member in roster:
        assert _target_hash(out, member, renders[member]) == invocations[member]["target"]["after"]

    # 9. Publication is complete before predecessor completion and successor launch.
    assert [row["member"] for row in events if row["event"] == "leg-started"] == roster
    plan_result, _ = _event(events, "member-result-written", task_id="plan")
    plan_send, _ = _event(events, "message-sent", task_id="plan")
    plan_done, _ = _event(events, "task-completed", task_id="plan")
    implement_start, _ = _event(events, "leg-started", task_id="implement")
    assert plan_result < plan_send < plan_done < implement_start
    implement_result, _ = _event(events, "member-result-written", task_id="implement")
    archived, archived_event = _event(events, "deliverable-archived", task_id="implement")
    materialized, materialized_event = _event(
        events, "deliverable-materialized", task_id="implement"
    )
    blinded, _ = _event(events, "handoff-blinded", task_id="implement")
    implement_done, _ = _event(events, "task-completed", task_id="implement")
    review_start, _ = _event(events, "leg-started", task_id="review")
    assert implement_result < archived < materialized < blinded < implement_done < review_start

    # 10-11. Non-blinded handoff bytes, ledger rows, and events are hash-linked.
    assert len(ledger) == 1
    handoff = ledger[0]
    assert (handoff["sender"], handoff["recipient"]) == ("lead", "implementer")
    provider_handoff = snapshot["messages"][0]["message"]
    assert provider_handoff["body"] == handoff["body"]
    implement_task = (out / "legs" / "inv-implementer" / "task.md").read_text(encoding="utf-8")
    assert handoff["body"] in implement_task
    digest = hashlib.sha256(handoff["body"].encode("utf-8")).hexdigest()
    sent, sent_event = _event(events, "message-sent", seq=handoff["seq"])
    claimed, claimed_event = _event(events, "message-claimed", seq=handoff["seq"])
    assert sent_event["sha256"] == claimed_event["sha256"] == digest
    assert sent_event["sender"] == claimed_event["sender"] == handoff["sender"]
    assert sent_event["recipient"] == claimed_event["recipient"] == handoff["recipient"]
    assert sent < plan_done < claimed < implement_start

    # 12. The independent edge transports only the declared deliverable artifact.
    implementation = _load(out / "legs" / "inv-implementer" / "member-result.json")
    assert implementation["deliverables"] == ["implementation.txt"]
    archived_file = out / "legs" / "inv-implementer" / "deliverables" / "implementation.txt"
    source_file = out / "legs" / "inv-implementer" / "workspace" / "implementation.txt"
    materialized_file = (
        out / "legs" / "inv-reviewer" / "workspace" / "handoff" / "implement" / "implementation.txt"
    )
    assert source_file.read_bytes() == archived_file.read_bytes() == materialized_file.read_bytes()
    assert archived_file.read_text(encoding="utf-8") == "deterministic team implementation\n"
    deliverable_digest = hashlib.sha256(archived_file.read_bytes()).hexdigest()
    assert deliverable_digest == "d3b0ba50d3d0f0029e079a1aa9adc0014535236933f80050c0e6a0acf5b903fd"
    assert archived_event["sha256"] == materialized_event["sha256"] == deliverable_digest
    assert not any(
        row["sender"] == "implementer" and row["recipient"] == "reviewer" for row in ledger
    )
    assert not any(
        row["event"] in {"message-sent", "message-claimed"}
        and row.get("sender") == "implementer"
        and row.get("recipient") == "reviewer"
        for row in events
    )
    review_task = (out / "legs" / "inv-reviewer" / "task.md").read_text(encoding="utf-8")
    assert "handoff blinded by declared independence: artifact only" in review_task
    assert implementation["summary"] not in review_task
    assert '"task_id":"implement"' not in review_task

    assert RunArchive(out).verify_team_bindings(TeamRunRecordV1.model_validate(run)) == []
    assert RunArchive(out).verify_manifest() == []


def test_out_of_roster_task_owner_is_rejected_before_provider_creation(
    tmp_path: Path,
) -> None:
    template = yaml.safe_load(TEAM_TEMPLATE.read_text(encoding="utf-8"))
    template["workflow_skeleton"][-1]["owner"] = "outsider"
    template_path = tmp_path / "invalid-team.yaml"
    template_path.write_text(yaml.safe_dump(template, sort_keys=False), encoding="utf-8")
    request = yaml.safe_load(TEAM_REQUEST.read_text(encoding="utf-8"))
    request.update(
        {
            "template": str(template_path),
            "workspace": str(REVIEW_TARGET),
            "task_file": str(REPO_ROOT / "examples" / "run-requests" / "review-task.md"),
        }
    )
    request_path = tmp_path / "invalid-request.yaml"
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
    assert "one-task-per-member bijection" in result.output
    assert not out.exists()
