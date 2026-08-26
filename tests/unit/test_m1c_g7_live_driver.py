"""Deterministic contracts for the dev-only M1c G7 attended driver."""

from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path
from typing import Any

import pytest

_DRIVER = Path(__file__).resolve().parents[2] / "dev" / "m1c_g7_live.py"
_SPEC = importlib.util.spec_from_file_location("agentteam_m1c_g7_live", _DRIVER)
assert _SPEC is not None and _SPEC.loader is not None
g7: Any = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = g7
_SPEC.loader.exec_module(g7)


class _Process:
    def __init__(self, frames: list[dict[str, object]]) -> None:
        self.pid = 999_999
        self.stdin = io.StringIO()
        self.stdout = io.StringIO("".join(json.dumps(frame) + "\n" for frame in frames))

    def poll(self) -> int | None:
        return None

    def wait(self, timeout: float | None = None) -> int:
        return 0

    def terminate(self) -> None:
        return None

    def kill(self) -> None:
        return None


def _server_frame(
    sequence: int,
    *,
    kind: str,
    correlation: str,
    **data: object,
) -> dict[str, object]:
    return {
        "schema": {"kind": kind, "version": 1},
        "run_id": "run-g7-test",
        "sequence": sequence,
        "correlation_id": correlation,
        **data,
    }


def test_exact_live_fixtures_and_workflow_contracts_are_pinned(tmp_path: Path) -> None:
    g7._verify_fixture_hashes()
    token = "deadbeef01234567"
    contracts = g7._workflow_contracts(tmp_path, token)
    assert [contract.member for contract in contracts] == [
        "implementer",
        "reviewer",
        "lead",
        "lead",
    ]
    assert [contract.work_item for contract in contracts] == [
        "implement",
        "review",
        "complete",
        None,
    ]
    assert contracts[-1].writable is None
    assert token not in contracts[-1].prompt
    workflow = g7.TEAM_PATH.read_text(encoding="utf-8")
    assert "implementer: [codex]" in workflow
    assert "reviewer: [claude-code]" in workflow
    assert "lead: [grok]" in workflow


def test_tool_scope_requires_one_exact_declared_workspace_path(tmp_path: Path) -> None:
    workspace = tmp_path.resolve()
    output = workspace / "implementation.txt"
    contract = g7.TurnContract(
        member="implementer",
        work_item="implement",
        prompt="bounded",
        expected_text="done",
        readable=frozenset(),
        writable=output,
    )
    exact = g7._tool_request(
        {
            "permission_id": "permission-1",
            "classification": "workspace-write",
            "tool_kind": "write",
            "tool_title": "write file",
            "tool_input": json.dumps(
                {
                    "cwd": str(workspace),
                    "file_path": "implementation.txt",
                    "path": "implementation.txt",
                }
            ),
        },
        workspace,
    )
    escaped = g7._tool_request(
        {
            "permission_id": "permission-2",
            "classification": "workspace-write",
            "tool_kind": "write",
            "tool_input": json.dumps({"path": "../escaped.txt"}),
        },
        workspace,
    )
    shell = g7.ToolRequest("permission-3", "full-access", "execute", "shell", ())
    assert g7._allowed_tool(exact, contract)
    assert not g7._allowed_tool(escaped, contract)
    assert not g7._allowed_tool(shell, contract)


def test_workspace_is_checked_after_each_call_and_rejects_extra_files(tmp_path: Path) -> None:
    marker = "deadbeef"
    (tmp_path / "implementation.txt").write_text(
        f"implementation marker: {marker}\n",
        encoding="utf-8",
    )
    g7._assert_workspace(tmp_path, marker, completed=1)
    (tmp_path / "extra.txt").write_text("unexpected\n", encoding="utf-8")
    with pytest.raises(g7.G7Error, match="unexpected entries"):
        g7._assert_workspace(tmp_path, marker, completed=1)


def test_ndjson_client_correlates_attended_exact_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path.resolve()
    output = workspace / "implementation.txt"
    permission = {
        "permission_id": "permission-1",
        "classification": "workspace-write",
        "reasons": ["workspace mutation needs attended user approval"],
        "tool_kind": "write",
        "tool_title": "write implementation",
        "tool_input": json.dumps({"path": "implementation.txt"}),
    }
    provider_permission = {
        "event": "permission-request",
        "text": None,
        "data": {
            "permission_id": "permission-1",
            "tool_kind": "write",
            "tool_title": "write implementation",
            "tool_input": json.dumps({"path": "implementation.txt"}),
        },
    }
    frames = [
        _server_frame(
            0,
            kind="stream-receipt",
            correlation="g7-1",
            command="negotiate",
            status="ok",
            protocol_version=1,
            client_mode="attended",
        ),
        _server_frame(
            1,
            kind="stream-receipt",
            correlation="g7-2",
            command="turn.start",
            status="accepted",
        ),
        _server_frame(
            2,
            kind="stream-event",
            correlation="g7-2",
            event="permission-awaiting",
            **permission,
        ),
        _server_frame(
            3,
            kind="stream-receipt",
            correlation="g7-3",
            command="permission.respond",
            status="ok",
        ),
        _server_frame(
            4,
            kind="stream-event",
            correlation="g7-2",
            event="provider-event",
            provider_event=provider_permission,
        ),
        _server_frame(
            5,
            kind="stream-event",
            correlation="g7-2",
            event="turn-terminal",
            turn={"turn_id": "turn-1"},
            result={"status": "completed", "text": "done"},
        ),
    ]
    process = _Process(frames)
    client = g7.NdjsonClient(process, workspace=workspace)
    confirmation_prompts: list[str] = []

    def confirm(prompt: str) -> bool:
        confirmation_prompts.append(prompt)
        return True

    monkeypatch.setattr(g7, "_confirm", confirm)
    client.negotiate()
    turn_id = client.turn(
        g7.TurnContract(
            member="implementer",
            work_item="implement",
            prompt="bounded",
            expected_text="done",
            readable=frozenset(),
            writable=output,
        )
    )
    assert turn_id == "turn-1"
    commands = [json.loads(line) for line in process.stdin.getvalue().splitlines()]
    assert [command["sequence"] for command in commands] == [0, 1, 2]
    assert commands[-1]["command"] == "permission.respond"
    assert commands[-1]["approved"] is True
    assert commands[-1]["attended"] is True
    assert confirmation_prompts == [
        "Allow once [workspace-write/write] exact path implementation.txt "
        "(answer within 30 seconds)?"
    ]


def test_workflow_stops_before_another_prompt_when_candidate_drifts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Client:
        def __init__(self, _process: object, *, workspace: Path) -> None:
            self.run_id = "run-g7-test"
            self.turn_count = 0

        def negotiate(self) -> None:
            return None

        def turn(self, _contract: object) -> str:
            self.turn_count += 1
            return f"turn-{self.turn_count}"

        def command(self, _command: str, **_data: object) -> dict[str, object]:
            return {"record": {"phase": "open"}}

        def abort(self) -> None:
            return None

    process = _Process([])
    clients: list[_Client] = []

    def client_factory(process: object, *, workspace: Path) -> _Client:
        client = _Client(process, workspace=workspace)
        clients.append(client)
        return client

    checks = 0

    def candidate_gate(_head: str) -> str:
        nonlocal checks
        checks += 1
        if checks == 3:
            raise g7.G7Error("candidate drifted")
        return "a" * 40

    monkeypatch.setattr(g7, "_confirm", lambda _prompt: True)
    monkeypatch.setattr(g7, "_spawn_workflow", lambda *_args: process)
    monkeypatch.setattr(g7, "NdjsonClient", client_factory)
    monkeypatch.setattr(g7, "_update_work", lambda *_args: None)
    monkeypatch.setattr(g7, "_assert_workspace", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(g7, "_candidate_head", candidate_gate)
    with pytest.raises(g7.G7Error, match="candidate drifted"):
        g7._run_workflow(
            tmp_path,
            "deadbeef",
            candidate_head="a" * 40,
            environ={},
        )
    assert checks == 3
    assert clients[0].turn_count == 1


def test_candidate_cleanliness_ignores_only_codex_user_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    head = "a" * 40
    replies = iter([head, "?? .codex/settings.json"])
    monkeypatch.setattr(g7, "_run_git", lambda *_args: next(replies))
    assert g7._candidate_head(head) == head

    replies = iter([head, "?? notes.txt"])
    monkeypatch.setattr(g7, "_run_git", lambda *_args: next(replies))
    with pytest.raises(g7.G7Error, match="not clean"):
        g7._candidate_head(head)


def test_hosted_gate_requires_exact_eight_green_non_windows_jobs() -> None:
    head = "a" * 40
    names = [
        "scaffold (ubuntu-latest, py3.11)",
        "scaffold (ubuntu-latest, py3.13)",
        "scaffold (macos-latest, py3.11)",
        "scaffold (macos-latest, py3.13)",
        "clawteam (ubuntu-latest, py3.11)",
        "clawteam (macos-latest, py3.11)",
        "vendor-smoke (ubuntu-latest, py3.11)",
        "vendor-smoke (macos-latest, py3.11)",
    ]
    jobs: list[dict[str, str]] = [
        {"name": name, "status": "completed", "conclusion": "success"} for name in names
    ]
    payload = {
        "headSha": head,
        "status": "completed",
        "conclusion": "success",
        "jobs": jobs,
    }
    g7._validate_hosted_run_payload(payload, head)
    jobs[7]["name"] = "scaffold (windows-latest, py3.11)"
    with pytest.raises(g7.G7Error, match="Windows"):
        g7._validate_hosted_run_payload(payload, head)


def test_evidence_date_cannot_escape_the_dated_directory() -> None:
    destination = g7._evidence_destination("2026-08-26")
    assert destination == g7.REPO_ROOT / "docs" / "evidence" / "m1c-live-2026-08-26"
    with pytest.raises(g7.G7Error, match="YYYY-MM-DD"):
        g7._evidence_destination("../../outside")
    with pytest.raises(g7.G7Error, match="real calendar"):
        g7._evidence_destination("2026-02-30")


def test_ci_windows_matrix_is_manual_opt_in() -> None:
    workflow = (g7.REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch:" in workflow
    assert "include_windows:" in workflow
    assert workflow.count("inputs.include_windows &&") == 3
    assert workflow.count("windows-latest") == 3
