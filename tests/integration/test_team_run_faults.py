"""Fault-injection matrix for M1b lifecycle closure and publication ordering."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, cast

import pytest
import yaml

from agentteam.coordination.local import LocalCoordinationProvider
from agentteam.coordination.protocol import CoordinationSubstrate, WaitTimeoutError
from agentteam.domain.run import HarnessInvocationV1
from agentteam.run.archive import RunArchive
from agentteam.run.team import _TeamRunner, execute_team_run
from agentteam.run.team_preflight import load_team_request, preflight_team

REPO_ROOT = Path(__file__).resolve().parents[2]
REQUEST = REPO_ROOT / "examples" / "run-requests" / "team-review.yaml"
CI_FAKE = REPO_ROOT / "examples" / "profiles" / "ci-fake.yaml"


class InjectedFault(RuntimeError):
    pass


class FaultInjectingProvider:
    """Wrap local and raise before/after one selected public method call."""

    def __init__(
        self,
        inner: LocalCoordinationProvider,
        *,
        method: str,
        occurrence: int = 1,
        after: bool = False,
    ) -> None:
        self.inner = inner
        self.method = method
        self.occurrence = occurrence
        self.after = after
        self.calls: dict[str, int] = {}

    def __getattr__(self, name: str) -> Any:
        target = getattr(self.inner, name)
        if not callable(target):
            return target

        def call(*args: Any, **kwargs: Any) -> Any:
            self.calls[name] = self.calls.get(name, 0) + 1
            selected = name == self.method and self.calls[name] == self.occurrence
            if selected and not self.after:
                raise InjectedFault(f"injected {name} before")
            value = target(*args, **kwargs)
            if selected and self.after:
                raise InjectedFault(f"injected {name} after")
            return value

        return call


def _resolved(out: Path, env: dict[str, str] | None = None) -> Any:
    parent = {**os.environ, "FAKE_MODE": "ok", **(env or {})}
    request = load_team_request(REQUEST, output_dir=out)
    return preflight_team(
        request,
        request_path=REQUEST,
        profile_path=CI_FAKE,
        live=True,
        environ=parent,
        platform=sys.platform,
    )


def _run(
    out: Path,
    *,
    method: str,
    occurrence: int = 1,
    after: bool = False,
    env: dict[str, str] | None = None,
) -> tuple[Any, FaultInjectingProvider]:
    resolved = _resolved(out, env)
    box: list[FaultInjectingProvider] = []

    def factory(root: Path) -> CoordinationSubstrate:
        provider = FaultInjectingProvider(
            LocalCoordinationProvider(root, platform=sys.platform),
            method=method,
            occurrence=occurrence,
            after=after,
        )
        box.append(provider)
        return cast(CoordinationSubstrate, provider)

    outcome = asyncio.run(
        execute_team_run(
            resolved,
            environ={**os.environ, "FAKE_MODE": "ok", **(env or {})},
            platform=sys.platform,
            provider_factory=factory,
        )
    )
    return outcome, box[0]


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _events(out: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line) for line in (out / "events.jsonl").read_text(encoding="utf-8").splitlines()
    ]


def _assert_closed(out: Path, *, space_minted: bool) -> dict[str, Any]:
    run = _json(out / "run.json")
    assert run["status"] in {"failed", "succeeded", "cancelled"}
    assert all(
        task["status"] in {"completed", "failed", "cancelled", "abandoned"} for task in run["tasks"]
    )
    events = _events(out)
    assert sum(event["event"] == "processes-stopped" for event in events) == 1
    assert sum(event["event"] == "provider-cleanup" for event in events) == int(space_minted)
    assert RunArchive(out).verify_manifest() == []
    bindings = {
        member["execution"]["ref"] for member in run["members"] if member["execution"] is not None
    }
    invocations = {path.parent.name for path in (out / "legs").glob("inv-*/invocation.json")}
    assert bindings == invocations
    for invocation_id in invocations:
        invocation = HarnessInvocationV1.model_validate_json(
            (out / "legs" / invocation_id / "invocation.json").read_text(encoding="utf-8")
        )
        assert invocation.status.value in {"succeeded", "failed", "cancelled", "timed-out"}
    return run


@pytest.mark.parametrize(
    ("method", "occurrence", "after", "space_minted"),
    [
        ("info", 1, False, False),
        ("create_space", 1, False, False),
        ("add_member", 1, False, True),
        ("create_task", 1, False, True),
        ("tasks", 1, False, True),
        ("send", 1, False, True),
        ("send", 1, True, True),
        ("receive", 1, False, True),
        ("update_task", 1, False, True),
        ("snapshot", 1, False, True),
        ("read_snapshot", 1, False, True),
    ],
)
def test_provider_faults_close_every_record_and_cleanup_exactly_once(
    tmp_path: Path,
    method: str,
    occurrence: int,
    after: bool,
    space_minted: bool,
) -> None:
    out = tmp_path / f"{method}-{occurrence}-{after}"
    outcome, _provider = _run(out, method=method, occurrence=occurrence, after=after)
    assert outcome.exit_code == 1
    run = _assert_closed(out, space_minted=space_minted)
    if not space_minted:
        assert run["substrate"]["namespace"] is None
        assert run["substrate"]["snapshot"] is None


@pytest.mark.parametrize("after", [False, True])
def test_provider_completion_fault_preserves_published_success_but_fails_task(
    tmp_path: Path, after: bool
) -> None:
    out = tmp_path / f"completion-{after}"
    outcome, provider = _run(
        out,
        method="update_task",
        occurrence=2,
        after=after,
    )
    assert outcome.exit_code == 1
    run = _assert_closed(out, space_minted=True)
    assert run["tasks"][0]["status"] == "failed"
    assert _json(out / "legs/inv-lead/invocation.json")["status"] == "succeeded"
    snapshot = _json(out / "coordination/snapshot.json")
    tasks = {row["id"]: row for row in snapshot["tasks"]}
    if after:
        assert tasks["t-1"]["status"] == "completed"
        assert tasks["t-2"]["status"] == "pending"
    else:
        assert tasks["t-1"]["status"] == "running"
        assert tasks["t-2"]["status"] == "blocked"
    assert provider.calls["update_task"] == 2
    assert not (out / "legs/inv-implementer/invocation.json").exists()


def test_cleanup_exception_is_warning_only_after_verified_copy_out(tmp_path: Path) -> None:
    out = tmp_path / "cleanup"
    outcome, _provider = _run(out, method="cleanup")
    assert outcome.exit_code == 0
    run = _assert_closed(out, space_minted=True)
    assert run["status"] == "succeeded"
    cleanup = next(event for event in _events(out) if event["event"] == "provider-cleanup")
    detail = json.loads(cleanup["detail"])
    assert detail["warning_codes"] == ["upstream-cleanup-failed"]
    assert run["substrate"]["snapshot"] is not None


def test_wait_helper_timeout_fault_aborts_without_launch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import agentteam.run.team as team_module

    def fail_wait(*_args: Any, **_kwargs: Any) -> Any:
        raise WaitTimeoutError("injected wait timeout")

    monkeypatch.setattr(team_module, "wait_for_tasks", fail_wait)
    out = tmp_path / "wait"
    resolved = _resolved(out)
    outcome = asyncio.run(
        execute_team_run(
            resolved,
            environ={**os.environ, "FAKE_MODE": "ok"},
            platform=sys.platform,
        )
    )
    assert outcome.exit_code == 1
    run = _assert_closed(out, space_minted=True)
    assert [task["status"] for task in run["tasks"]] == [
        "abandoned",
        "abandoned",
        "abandoned",
    ]
    assert not list((out / "legs").glob("inv-*/invocation.json"))


def test_snapshot_failure_keeps_primary_task_failure_reason(tmp_path: Path) -> None:
    out = tmp_path / "primary"
    outcome, _provider = _run(
        out,
        method="snapshot",
        env={"FAKE_MODE_CLAUDE": "schema-invalid"},
    )
    assert outcome.exit_code == 1
    run = _assert_closed(out, space_minted=True)
    assert run["failure_reason"].startswith("task plan:")
    assert run["substrate"]["snapshot"] is None
    assert any(event["event"] == "snapshot-failed" for event in _events(out))


def _plain_run(out: Path, env: dict[str, str] | None = None) -> Any:
    resolved = _resolved(out, env)
    return asyncio.run(
        execute_team_run(
            resolved,
            environ={**os.environ, "FAKE_MODE": "ok", **(env or {})},
            platform=sys.platform,
        )
    )


@pytest.mark.parametrize(
    ("fault", "expected_task", "binding"),
    [
        ("pending-before", "plan", False),
        ("pending-after", "plan", True),
        ("binding", "plan", True),
        ("spawn", "plan", True),
        ("member-result", "plan", True),
        ("deliverable", "implement", True),
        ("materialize", "plan", True),
        ("ledger", "plan", True),
        ("snapshot-copy", None, True),
    ],
)
def test_non_provider_fault_windows_preserve_binding_and_terminal_pairing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
    expected_task: str | None,
    binding: bool,
) -> None:
    from agentteam.harness.claude import ClaudeAdapter

    if fault.startswith("pending"):
        original = RunArchive.write_invocation
        calls = 0

        def fail_pending(self: RunArchive, record: HarnessInvocationV1) -> None:
            nonlocal calls
            calls += 1
            if calls == 1:
                if fault == "pending-after":
                    original(self, record)
                raise OSError("injected pending invocation write")
            original(self, record)

        monkeypatch.setattr(RunArchive, "write_invocation", fail_pending)
    elif fault == "binding":
        original_bind = _TeamRunner._bind
        calls = 0

        def fail_binding(self: _TeamRunner, member: str, invocation_id: str) -> None:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise OSError("injected binding write")
            original_bind(self, member, invocation_id)

        monkeypatch.setattr(_TeamRunner, "_bind", fail_binding)
    elif fault == "spawn":

        async def fail_spawn(self: ClaudeAdapter, _rendered: Any) -> Any:
            raise OSError("injected spawn failure")

        monkeypatch.setattr(ClaudeAdapter, "invoke", fail_spawn)
    elif fault == "member-result":
        original_result = RunArchive.write_member_result
        calls = 0

        def fail_result(self: RunArchive, invocation_id: str, result: Any) -> Any:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise OSError("injected member-result write")
            return original_result(self, invocation_id, result)

        monkeypatch.setattr(RunArchive, "write_member_result", fail_result)
    elif fault == "deliverable":

        def fail_deliverable(
            self: RunArchive, invocation_id: str, relative_path: str, data: bytes
        ) -> Any:
            raise OSError("injected deliverable archive write")

        monkeypatch.setattr(RunArchive, "write_deliverable", fail_deliverable)
    elif fault == "materialize":

        def fail_materialize(
            self: _TeamRunner, predecessor: str, successor: str, refs: list[Any]
        ) -> None:
            raise OSError("injected successor materialization")

        monkeypatch.setattr(_TeamRunner, "_materialize", fail_materialize)
    elif fault == "ledger":

        def fail_ledger(self: RunArchive, **_kwargs: Any) -> Any:
            raise OSError("injected ledger append")

        monkeypatch.setattr(RunArchive, "append_message", fail_ledger)
    elif fault == "snapshot-copy":

        def fail_snapshot_copy(self: RunArchive, _payload: dict[str, Any]) -> str:
            raise OSError("injected snapshot copy-out")

        monkeypatch.setattr(RunArchive, "write_coordination_snapshot", fail_snapshot_copy)

    out = tmp_path / fault
    outcome = _plain_run(out)
    assert outcome.exit_code == 1
    run = _assert_closed(out, space_minted=True)
    if expected_task is not None:
        task = next(row for row in run["tasks"] if row["id"] == expected_task)
        assert task["status"] == "failed"
    first_binding = run["members"][0]["execution"]
    assert (first_binding is not None) is binding
    if fault == "snapshot-copy":
        assert all(row["status"] == "completed" for row in run["tasks"])
        assert run["substrate"]["snapshot"] is None


def test_cancellation_terminalizes_allocated_work_and_abandons_the_rest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from agentteam.harness.claude import ClaudeAdapter

    entered = asyncio.Event()

    async def block(self: ClaudeAdapter, _rendered: Any) -> Any:
        entered.set()
        await asyncio.Event().wait()

    monkeypatch.setattr(ClaudeAdapter, "invoke", block)
    out = tmp_path / "cancelled"
    resolved = _resolved(out)

    async def scenario() -> None:
        task = asyncio.create_task(
            execute_team_run(
                resolved,
                environ={**os.environ, "FAKE_MODE": "ok"},
                platform=sys.platform,
            )
        )
        await asyncio.wait_for(entered.wait(), timeout=3)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(scenario())
    run = _assert_closed(out, space_minted=True)
    assert run["status"] == "cancelled"
    assert [row["status"] for row in run["tasks"]] == [
        "cancelled",
        "abandoned",
        "abandoned",
    ]
    assert _json(out / "legs/inv-lead/invocation.json")["status"] == "cancelled"


def test_parallel_failure_cascade_lets_inflight_sibling_finish(
    tmp_path: Path,
) -> None:
    template_path = tmp_path / "parallel-team.yaml"
    reviewer_root = tmp_path / "assistants" / "code-reviewer"
    implementer_root = tmp_path / "assistants" / "implementer"
    shutil.copytree(REPO_ROOT / "examples/assistants/code-reviewer", reviewer_root)
    shutil.copytree(REPO_ROOT / "examples/assistants/implementer", implementer_root)
    reviewer = reviewer_root.relative_to(template_path.parent).as_posix()
    implementer = implementer_root.relative_to(template_path.parent).as_posix()
    template = {
        "schema_version": 1,
        "kind": "team-template",
        "id": "parallel-fault",
        "version": 1,
        "summary": "Exercises a parallel failure cascade.",
        "members": [
            {"name": "root", "assistant": reviewer},
            {"name": "failing", "assistant": implementer},
            {"name": "survivor", "assistant": implementer},
            {"name": "dependent", "assistant": reviewer},
            {"name": "survivor-child", "assistant": implementer},
        ],
        "lead": "root",
        "handoff": {
            "required_fields": [
                "task_id",
                "summary",
                "deliverables",
                "risks",
                "done_when",
            ],
            "acks": ["ACK", "DONE", "BLOCKED"],
        },
        "independence": [],
        "preferences": {
            "harness_preferences": {},
            "run_defaults": {
                "fresh_instances": True,
                "archive": "always",
                "worktree_per_member": True,
            },
        },
        "workflow_skeleton": [
            {"id": "root-task", "subject": "Root {goal}", "owner": "root"},
            {
                "id": "fail-task",
                "subject": "Fail {goal}",
                "owner": "failing",
                "blocked_by": ["root-task"],
            },
            {
                "id": "survive-task",
                "subject": "Survive {goal}",
                "owner": "survivor",
                "blocked_by": ["root-task"],
            },
            {
                "id": "dependent-task",
                "subject": "Dependent {goal}",
                "owner": "dependent",
                "blocked_by": ["fail-task"],
            },
            {
                "id": "survivor-child-task",
                "subject": "Survivor child {goal}",
                "owner": "survivor-child",
                "blocked_by": ["survive-task"],
            },
        ],
    }
    template_path.write_text(yaml.safe_dump(template, sort_keys=False), encoding="utf-8")
    out = tmp_path / "parallel-run"
    request_path = tmp_path / "parallel-request.yaml"
    request = {
        "schema_version": 1,
        "kind": "team-run-request",
        "template": str(template_path),
        "workspace": str(REPO_ROOT / "fixtures/review-target"),
        "task_file": str(REPO_ROOT / "examples/run-requests/review-task.md"),
        "goal": "parallel closure",
        "substrate": "local",
        "members": {
            "root": {"harness": "claude-code"},
            "failing": {"harness": "codex"},
            "survivor": {"harness": "claude-code"},
            "dependent": {"harness": "claude-code"},
            "survivor-child": {"harness": "claude-code"},
        },
        "output_dir": str(out),
    }
    request_path.write_text(yaml.safe_dump(request, sort_keys=False), encoding="utf-8")
    loaded = load_team_request(request_path)
    env = {**os.environ, "FAKE_MODE": "ok", "FAKE_MODE_CODEX": "rate-limit"}
    resolved = preflight_team(
        loaded,
        request_path=request_path,
        profile_path=CI_FAKE,
        live=True,
        environ=env,
        platform=sys.platform,
    )
    outcome = asyncio.run(execute_team_run(resolved, environ=env, platform=sys.platform))
    assert outcome.exit_code == 1
    run = _assert_closed(out, space_minted=True)
    assert {row["id"]: row["status"] for row in run["tasks"]} == {
        "root-task": "completed",
        "fail-task": "failed",
        "survive-task": "completed",
        "dependent-task": "abandoned",
        "survivor-child-task": "abandoned",
    }
    events = _events(out)
    second_wave = [
        event["member"]
        for event in events
        if event["event"] == "leg-started"
        and event["member"] in {"failing", "survivor"}
        and event["detail"] == "attempt 1"
    ]
    assert second_wave == ["failing", "survivor"]
    dependent_abandoned = next(
        index
        for index, event in enumerate(events)
        if event["event"] == "task-abandoned" and event["task_id"] == "dependent-task"
    )
    survivor_child_abandoned = next(
        index
        for index, event in enumerate(events)
        if event["event"] == "task-abandoned" and event["task_id"] == "survivor-child-task"
    )
    stopped = next(
        index for index, event in enumerate(events) if event["event"] == "processes-stopped"
    )
    assert dependent_abandoned < stopped < survivor_child_abandoned
    assert _json(out / "legs/inv-survivor/invocation.json")["status"] == "succeeded"
    assert not (out / "legs/inv-dependent/invocation.json").exists()
    assert not (out / "legs/inv-survivor-child/invocation.json").exists()
