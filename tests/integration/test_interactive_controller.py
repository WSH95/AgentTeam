"""Deterministic M1c lifecycle, recovery, permission, control, and cleanup matrix."""

from __future__ import annotations

import asyncio
import hashlib
import json
import shutil
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from agentteam.cli import app
from agentteam.domain.common import HarnessId
from agentteam.domain.interactive import (
    AssistantCatalogRefV1,
    CatalogKind,
    CatalogRefV1,
    CleanupFact,
    CloseFactsV1,
    CompletionCriterionV1,
    CompletionProposalV1,
    ControlAction,
    ControlActor,
    ControlRequestV1,
    InteractiveRunOutcome,
    InteractiveRunPhase,
    InteractiveRunRequestV1,
    ReceiptStatus,
    TeamMemberV2,
    TeamPreferencesV2,
    TeamTemplateV2,
    WorkItemV1,
    WorkspaceLayout,
)
from agentteam.domain.team import (
    HandoffRulesV1,
    TeamTaskStatus,
    WorkflowTaskV1,
    WorkspaceAccess,
)
from agentteam.execution.fakes import (
    ExternalHostFakeProvider,
    FakeProviderError,
    OwnedProcessFakeProvider,
)
from agentteam.execution.protocol import (
    OpenMemberSpec,
    ProviderEvent,
    ProviderSession,
    ProviderTurnStatus,
)
from agentteam.interactive.archive import (
    InteractiveArchive,
    InteractiveArchiveError,
    InteractiveRunStore,
)
from agentteam.interactive.controller import (
    InteractiveController,
    InteractiveControllerError,
    InteractiveInitializationError,
    MemberLaunch,
)
from agentteam.interactive.permissions import PermissionDecision
from agentteam.interactive.resolution import PreparedChat
from agentteam.interactive.stream import StreamSession
from agentteam.interactive.tty import run_tty
from agentteam.interactive.workspace import WorkspaceReservationError
from agentteam.resolution.archive import hash_package
from agentteam.resolution.package import load_package


def _assistant(tmp_path: Path, *, writable: bool = False) -> Path:
    source = Path("examples/assistants/implementer").resolve()
    if not writable:
        return source
    destination = tmp_path / "writable-assistant"
    shutil.copytree(source, destination)
    definition_path = destination / "assistant.yaml"
    payload = yaml.safe_load(definition_path.read_text(encoding="utf-8"))
    payload["permissions"] = {
        "filesystem": "read-write-workspace",
        "network": "deny",
        "shell": "deny",
    }
    definition_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return destination


def _team_and_request(
    tmp_path: Path,
    *,
    writable: bool = False,
) -> tuple[TeamTemplateV2, bytes, InteractiveRunRequestV1, dict[str, MemberLaunch]]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "tracked.txt").write_text("owner bytes\n", encoding="utf-8")
    assistant_path = _assistant(tmp_path, writable=writable)
    package = load_package(assistant_path)
    package_hash = hash_package(assistant_path).package_hash
    assistant_ref = AssistantCatalogRefV1(
        id=package.definition.id,
        version=package.definition.version,
        content_hash=package_hash,
    )
    team = TeamTemplateV2(
        schema_version=2,
        kind="team-template",
        id="interactive-test-team",
        version=1,
        summary="A deterministic two-Member interactive test Team.",
        members=[
            TeamMemberV2(name="lead", assistant=assistant_ref),
            TeamMemberV2(name="reviewer", assistant=assistant_ref),
        ],
        lead="lead",
        handoff=HandoffRulesV1(required_fields=[], acks=[]),
        independence=[],
        preferences=TeamPreferencesV2(),
        workflow_skeleton=[
            WorkflowTaskV1(
                id="implement",
                subject="Implement {goal}",
                owner="lead",
                workspace_access=WorkspaceAccess.WORKSPACE_WRITE,
            ),
            WorkflowTaskV1(
                id="review",
                subject="Review {goal}",
                owner="reviewer",
                blocked_by=["implement"],
            ),
        ],
        workspace_layout=WorkspaceLayout.SHARED_SUPPLIED,
    )
    team_source = yaml.safe_dump(team.model_dump(mode="json"), sort_keys=False).encode("utf-8")
    target_hash = hashlib.sha256(team_source).hexdigest()
    request = InteractiveRunRequestV1(
        schema_version=1,
        kind="interactive-run-request",
        target=CatalogRefV1(
            kind=CatalogKind.TEAM,
            id=team.id,
            version=team.version,
            content_hash=target_hash,
        ),
        workspace=str(workspace),
        goal="the bounded change",
        done_when=["tests pass"],
    )
    owned = OwnedProcessFakeProvider()
    external = ExternalHostFakeProvider()
    launches = {
        "lead": MemberLaunch(
            member="lead",
            assistant=package,
            provider=owned,
            harness=HarnessId.CODEX,
            executable=("fake",),
            environment={},
        ),
        "reviewer": MemberLaunch(
            member="reviewer",
            assistant=package,
            provider=external,
            harness=HarnessId.CLAUDE_CODE,
            executable=("fake",),
            environment={},
        ),
    }
    return team, team_source, request, launches


async def _controller(
    tmp_path: Path,
    *,
    writable: bool = False,
    run_id: str = "run-interactive-test-1",
) -> tuple[InteractiveController, TeamTemplateV2, bytes, dict[str, MemberLaunch]]:
    team, team_source, request, launches = _team_and_request(tmp_path, writable=writable)
    controller = await InteractiveController.create(
        request=request,
        team=team,
        team_source=team_source,
        launches=launches,
        runs_root=tmp_path / "home" / "runs",
        reservations_root=tmp_path / "home" / "workspace-reservations",
        run_id=run_id,
    )
    return controller, team, team_source, launches


def _git(workspace: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(workspace), *arguments],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
    )


async def test_multiturn_reset_workspace_reservation_and_exact_close(tmp_path: Path) -> None:
    controller, team, team_source, launches = await _controller(tmp_path)
    first = await controller.dispatch("lead", "remember-alpha")
    workspace = Path(controller.record.workspace)
    (workspace / "latest.txt").write_text("latest shared code\n", encoding="utf-8")
    second = await controller.dispatch("lead", "recall")
    review = await controller.dispatch("reviewer", "READFILE:latest.txt")
    assert first.text == "turn-1:remember-alpha"
    assert second.text == "turn-2:remember-alpha|recall"
    assert review.text == "file:latest shared code\n"
    event_text = (controller.archive.root / "events.jsonl").read_text(encoding="utf-8")
    events = [json.loads(line) for line in event_text.splitlines()]
    assert any(event["event"] == "workspace-external-drift" for event in events)
    assert controller.work_items["implement"].status is TeamTaskStatus.PENDING
    assert controller.work_items["review"].status is TeamTaskStatus.BLOCKED

    _other_team, _other_source, request, other_launches = _team_and_request(
        tmp_path / "other-input"
    )
    request = request.model_copy(update={"workspace": controller.record.workspace})
    with pytest.raises(WorkspaceReservationError, match="reserved by interactive run"):
        await InteractiveController.create(
            request=request,
            team=team,
            team_source=team_source,
            launches=other_launches,
            runs_root=tmp_path / "home" / "runs",
            reservations_root=tmp_path / "home" / "workspace-reservations",
            run_id="run-interactive-test-2",
        )

    old_session = controller.provider_sessions["lead"]
    reset = await controller.reset_member("lead")
    assert reset.generation == 2
    assert not old_session.state_dir.exists()
    fresh = await controller.dispatch("lead", "fresh")
    assert fresh.text == "turn-1:fresh"
    assert (controller.archive.root / "summaries" / "lead-g2.txt").is_file()

    record = await controller.close(InteractiveRunOutcome.CANCELLED, reason="test close")
    assert record.phase is InteractiveRunPhase.CLOSED
    assert record.cleanup is not None
    assert record.cleanup.provider_history.value == "unsupported"
    assert not any((controller.archive.root / "runtime").rglob("session.txt"))
    assert controller.archive.verify_manifest() == []
    assert (Path(record.workspace) / "tracked.txt").read_text(encoding="utf-8") == "owner bytes\n"
    assert (Path(record.workspace) / "latest.txt").read_text(encoding="utf-8") == (
        "latest shared code\n"
    )
    assert not list((tmp_path / "home" / "workspace-reservations").glob("*.json"))
    assert isinstance(launches["lead"].provider, OwnedProcessFakeProvider)


async def test_reset_revalidates_snapshot_and_can_retry_after_new_open_failure(
    tmp_path: Path,
) -> None:
    controller, _team, _source, _launches = await _controller(tmp_path)
    await controller.dispatch("lead", "old context")
    definition = controller.archive.root / "definitions" / "assistants" / "lead" / "assistant.yaml"
    original = definition.read_bytes()
    definition.write_bytes(original + b"\n# injected snapshot drift\n")

    with pytest.raises(InteractiveControllerError, match="snapshot changed"):
        await controller.reset_member("lead")
    assert controller.record.phase.value == "recovery-required"
    assert controller.session_records["lead"].status.value == "closed"
    assert "lead" not in controller.provider_sessions

    definition.write_bytes(original)
    reset = await controller.reset_member("lead")
    assert reset.generation == 2
    assert controller.record.phase.value == "open"
    fresh = await controller.dispatch("lead", "fresh context")
    assert fresh.text == "turn-1:fresh context"
    await controller.close(InteractiveRunOutcome.CANCELLED, reason="snapshot retry cleanup")


async def test_open_member_rejects_provider_session_identity_and_attempts_cleanup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    team, team_source, request, launches = _team_and_request(tmp_path)
    provider = launches["lead"].provider
    assert isinstance(provider, OwnedProcessFakeProvider)
    original_open = provider.open_member
    original_close = provider.close_member
    cleanup_attempts: list[ProviderSession] = []

    async def mismatched_open(spec: OpenMemberSpec) -> ProviderSession:
        session = await original_open(spec)
        return replace(session, run_id="run-wrong-owner")

    async def tolerant_close(session: ProviderSession, reason: str) -> CloseFactsV1:
        cleanup_attempts.append(session)
        stored = provider.sessions[session.session_id]
        return await original_close(stored, reason)

    monkeypatch.setattr(provider, "open_member", mismatched_open)
    monkeypatch.setattr(provider, "close_member", tolerant_close)
    with pytest.raises(InteractiveInitializationError, match="mismatched session identity"):
        await InteractiveController.create(
            request=request,
            team=team,
            team_source=team_source,
            launches=launches,
            runs_root=tmp_path / "home" / "runs",
            reservations_root=tmp_path / "home" / "workspace-reservations",
            run_id="run-provider-identity-mismatch",
        )
    assert len(cleanup_attempts) == 1
    assert not provider.sessions


async def test_reset_contains_close_summary_and_continuity_exceptions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    controller, _team, _source, launches = await _controller(tmp_path)
    provider = launches["lead"].provider
    assert isinstance(provider, OwnedProcessFakeProvider)
    original_close = provider.close_member

    async def fail_close(_session: ProviderSession, _reason: str) -> CloseFactsV1:
        raise FakeProviderError("injected reset close exception")

    monkeypatch.setattr(provider, "close_member", fail_close)
    with pytest.raises(InteractiveControllerError, match="cleanup is terminal"):
        await controller.reset_member("lead")
    assert controller.record.phase is InteractiveRunPhase.RECOVERY_REQUIRED
    assert controller.session_records["lead"].status.value == "close-failed"
    assert "lead" in controller.provider_sessions

    monkeypatch.setattr(provider, "close_member", original_close)
    original_summary = controller.run_state_summary

    def fail_summary(**_kwargs: object) -> str:
        raise OSError("injected summary checkpoint failure")

    monkeypatch.setattr(controller, "run_state_summary", fail_summary)
    with pytest.raises(InteractiveControllerError, match="could not prepare generation 2"):
        await controller.reset_member("lead")
    assert controller.session_records["lead"].status.value == "closed"
    assert "lead" not in controller.provider_sessions

    monkeypatch.setattr(controller, "run_state_summary", original_summary)
    original_verify = provider.verify_continuity

    async def fail_new_continuity(session: ProviderSession) -> bool:
        if session.generation == 2:
            raise FakeProviderError("injected continuity exception")
        return await original_verify(session)

    monkeypatch.setattr(provider, "verify_continuity", fail_new_continuity)
    with pytest.raises(InteractiveControllerError, match="continuity exception"):
        await controller.reset_member("lead")
    assert "lead" not in controller.provider_sessions
    assert not (
        controller.archive.root
        / "runtime"
        / provider.provider_id
        / "session-lead-g2"
        / "session.txt"
    ).exists()

    monkeypatch.setattr(provider, "verify_continuity", original_verify)
    reset = await controller.reset_member("lead")
    assert reset.generation == 2
    await controller.close(InteractiveRunOutcome.CANCELLED, reason="reset fault cleanup")


async def test_failed_open_verification_cleanup_retains_a_recoverable_generation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    controller, _team, _source, launches = await _controller(tmp_path)
    provider = launches["lead"].provider
    assert isinstance(provider, OwnedProcessFakeProvider)
    original_verify = provider.verify_continuity
    original_close = provider.close_member

    async def fail_generation_two_verify(session: ProviderSession) -> bool:
        if session.generation == 2:
            raise FakeProviderError("injected verification failure")
        return await original_verify(session)

    async def fail_generation_two_close(
        session: ProviderSession,
        reason: str,
    ) -> CloseFactsV1:
        if session.generation == 2:
            raise FakeProviderError("injected verification cleanup failure")
        return await original_close(session, reason)

    monkeypatch.setattr(provider, "verify_continuity", fail_generation_two_verify)
    monkeypatch.setattr(provider, "close_member", fail_generation_two_close)
    with pytest.raises(InteractiveControllerError, match="verification failure"):
        await controller.reset_member("lead")

    retained = controller.session_records["lead"]
    assert retained.generation == 2
    assert retained.status.value == "continuity-unverified"
    assert controller.provider_sessions["lead"].generation == 2
    assert next(item for item in controller.record.members if item.name == "lead").session_id == (
        retained.session_id
    )
    assert controller.archive.load_launch_record("lead")["generation"] == 2

    monkeypatch.setattr(provider, "verify_continuity", original_verify)
    monkeypatch.setattr(provider, "close_member", original_close)
    reset = await controller.reset_member("lead")
    assert reset.generation == 3
    await controller.close(InteractiveRunOutcome.CANCELLED, reason="retained generation cleanup")


async def test_cross_run_isolation_and_separate_projects_run_concurrently(
    tmp_path: Path,
) -> None:
    team_one, source_one, request_one, launches_one = _team_and_request(tmp_path / "one")
    team_two, source_two, request_two, launches_two = _team_and_request(tmp_path / "two")
    runs_root = tmp_path / "home" / "runs"
    reservations_root = tmp_path / "home" / "workspace-reservations"
    first, second = await asyncio.gather(
        InteractiveController.create(
            request=request_one,
            team=team_one,
            team_source=source_one,
            launches=launches_one,
            runs_root=runs_root,
            reservations_root=reservations_root,
            run_id="run-cross-isolation-1",
        ),
        InteractiveController.create(
            request=request_two,
            team=team_two,
            team_source=source_two,
            launches=launches_two,
            runs_root=runs_root,
            reservations_root=reservations_root,
            run_id="run-cross-isolation-2",
        ),
    )
    try:
        await asyncio.gather(
            first.dispatch("lead", "first-only"),
            second.dispatch("lead", "second-only"),
        )
        first_recall, second_recall = await asyncio.gather(
            first.dispatch("lead", "recall"),
            second.dispatch("lead", "recall"),
        )
        assert first_recall.text == "turn-2:first-only|recall"
        assert second_recall.text == "turn-2:second-only|recall"
        assert first.record.workspace != second.record.workspace
        assert len(list(reservations_root.glob("*.json"))) == 2
    finally:
        await asyncio.gather(
            first.close(InteractiveRunOutcome.CANCELLED, reason="cross-run cleanup"),
            second.close(InteractiveRunOutcome.CANCELLED, reason="cross-run cleanup"),
        )


async def test_dirty_git_state_is_preserved_across_dispatch_and_close(tmp_path: Path) -> None:
    team, source, request, launches = _team_and_request(tmp_path)
    workspace = Path(request.workspace)
    _git(workspace, "init", "-q")
    _git(workspace, "config", "user.email", "tests@example.invalid")
    _git(workspace, "config", "user.name", "AgentTeam tests")
    _git(workspace, "add", "tracked.txt")
    _git(workspace, "commit", "-qm", "fixture")
    (workspace / "tracked.txt").write_text("owner dirty bytes\n", encoding="utf-8")
    (workspace / "untracked.txt").write_text("owner untracked bytes\n", encoding="utf-8")
    head_before = _git(workspace, "rev-parse", "HEAD").stdout
    status_before = _git(
        workspace,
        "status",
        "--porcelain=v2",
        "-z",
        "--untracked-files=all",
        "--ignored=no",
    ).stdout
    controller = await InteractiveController.create(
        request=request,
        team=team,
        team_source=source,
        launches=launches,
        runs_root=tmp_path / "home" / "runs",
        reservations_root=tmp_path / "home" / "workspace-reservations",
        run_id="run-dirty-git-preservation",
    )
    assert controller.record.initial_checkpoint.git_head == head_before.decode().strip()
    await controller.dispatch("reviewer", "review without mutation")
    await controller.close(InteractiveRunOutcome.CANCELLED, reason="dirty-tree test close")
    assert _git(workspace, "rev-parse", "HEAD").stdout == head_before
    assert (
        _git(
            workspace,
            "status",
            "--porcelain=v2",
            "-z",
            "--untracked-files=all",
            "--ignored=no",
        ).stdout
        == status_before
    )
    assert (workspace / "tracked.txt").read_text(encoding="utf-8") == "owner dirty bytes\n"
    assert (workspace / "untracked.txt").read_text(encoding="utf-8") == ("owner untracked bytes\n")


async def test_final_workspace_observation_failure_is_audited_without_poisoning_close(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    controller, _team, _source, _launches = await _controller(tmp_path)

    def fail_checkpoint(_workspace: Path, **_kwargs: object) -> object:
        raise OSError("injected final observation failure")

    monkeypatch.setattr(
        "agentteam.interactive.controller.checkpoint_workspace",
        fail_checkpoint,
    )
    record = await controller.close(
        InteractiveRunOutcome.CANCELLED,
        reason="final observation failure test",
    )

    assert record.phase is InteractiveRunPhase.CLOSED
    assert record.final_checkpoint == record.initial_checkpoint
    events = [
        json.loads(line)
        for line in (controller.archive.root / "events.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert any(
        event["event"] == "workspace-observation-failed"
        and event["data"] == {"error": "OSError", "stage": "final"}
        for event in events
    )
    assert controller.archive.verify_manifest() == []
    assert not list((tmp_path / "home" / "workspace-reservations").glob("*.json"))


async def test_detach_attach_strict_recovery_retains_context(tmp_path: Path) -> None:
    controller, team, _team_source, launches = await _controller(tmp_path)
    await controller.dispatch("lead", "persist-me")
    archive_root = controller.archive.root
    await controller.detach()
    assert controller.record.phase is InteractiveRunPhase.INTERRUPTED

    recovered_launches = {
        member: MemberLaunch(
            member=member,
            assistant=launch.assistant,
            provider=(
                OwnedProcessFakeProvider() if member == "lead" else ExternalHostFakeProvider()
            ),
            harness=launch.harness,
            executable=launch.executable,
            environment={},
        )
        for member, launch in launches.items()
    }
    mismatched_launches = dict(recovered_launches)
    lead_launch = mismatched_launches["lead"]
    mismatched_launches["lead"] = MemberLaunch(
        member=lead_launch.member,
        assistant=lead_launch.assistant,
        provider=lead_launch.provider,
        harness=HarnessId.GROK,
        executable=lead_launch.executable,
        environment=lead_launch.environment,
    )
    with pytest.raises(InteractiveControllerError, match="archived launch"):
        InteractiveController.attach(
            archive=InteractiveArchive(archive_root),
            team=team,
            launches=mismatched_launches,
            reservations_root=tmp_path / "home" / "workspace-reservations",
        )
    attached = InteractiveController.attach(
        archive=InteractiveArchive(archive_root),
        team=team,
        launches=recovered_launches,
        reservations_root=tmp_path / "home" / "workspace-reservations",
    )
    with pytest.raises(InteractiveControllerError, match="does not accept prompts"):
        await attached.dispatch("lead", "must-not-run-before-recovery")
    assert await attached.recover() == {"lead": True, "reviewer": True}
    recalled = await attached.dispatch("lead", "recall")
    assert recalled.text == "turn-2:persist-me|recall"
    await attached.close(InteractiveRunOutcome.CANCELLED, reason="recovery test close")


async def test_permission_intersection_denies_then_allows_attended_write(tmp_path: Path) -> None:
    denied, _team, _source, _launches = await _controller(tmp_path / "denied")
    denied_turn = await denied.dispatch("lead", "PERMISSION:workspace-write")
    assert denied_turn.result.status is ProviderTurnStatus.CANCELLED
    await denied.close(InteractiveRunOutcome.CANCELLED, reason="denial test complete")

    allowed, _team, _source, _launches = await _controller(tmp_path / "allowed", writable=True)
    approvals: list[str] = []

    async def approve(_event: ProviderEvent, decision: PermissionDecision) -> bool:
        approvals.append(str(decision))
        return True

    allowed_turn = await allowed.dispatch(
        "lead",
        "PERMISSION:workspace-write",
        work_item_id="implement",
        permission_approver=approve,
    )
    assert allowed_turn.result.status is ProviderTurnStatus.COMPLETED
    assert len(approvals) == 1
    read_turn = await allowed.dispatch("reviewer", "PERMISSION:workspace-read")
    assert read_turn.result.status is ProviderTurnStatus.COMPLETED
    await allowed.close(InteractiveRunOutcome.CANCELLED, reason="permission test close")


async def test_cancel_provider_crash_and_recovery_required(tmp_path: Path) -> None:
    controller, _team, _source, launches = await _controller(tmp_path)
    waiting = asyncio.create_task(controller.dispatch("lead", "WAIT"))
    await asyncio.sleep(0.02)
    assert await controller.cancel_turn() == "running"
    assert (await waiting).result.status is ProviderTurnStatus.CANCELLED
    assert controller.record.phase.value == "open"

    provider = launches["lead"].provider
    assert isinstance(provider, OwnedProcessFakeProvider)
    process = provider.processes[controller.provider_sessions["lead"].session_id]
    process.kill()
    process.wait()
    await controller.dispatch("lead", "after-crash")
    assert controller.record.phase.value == "recovery-required"
    close = await controller.close(InteractiveRunOutcome.FAILED, reason="crash test close")
    assert close.phase is InteractiveRunPhase.CLOSED
    assert close.outcome is InteractiveRunOutcome.FAILED


async def test_task_cancellation_is_durable_and_not_rewritten_as_failure(tmp_path: Path) -> None:
    controller, _team, _source, _launches = await _controller(tmp_path)
    dispatch = asyncio.create_task(controller.dispatch("lead", "WAIT"))
    await asyncio.sleep(0.02)
    dispatch.cancel()
    with pytest.raises(asyncio.CancelledError):
        await dispatch

    turn = controller.archive.load_turn("turn-1")
    assert turn.status.value == "cancelled"
    assert turn.finished_at is not None
    assert controller.session_records["lead"].status.value == "open"
    assert controller.record.phase is InteractiveRunPhase.OPEN
    assert controller.active_turn is None
    await controller.close(InteractiveRunOutcome.CANCELLED, reason="task cancellation cleanup")


async def test_start_turn_failure_commits_a_terminal_record_and_allows_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    controller, _team, _source, launches = await _controller(tmp_path)
    provider = launches["lead"].provider
    original = provider.start_turn

    async def fail_start(_session: ProviderSession, _spec: object) -> object:
        raise FakeProviderError("injected start failure")

    monkeypatch.setattr(provider, "start_turn", fail_start)
    failed = await controller.dispatch("lead", "will fail before start")
    assert failed.result.status is ProviderTurnStatus.FAILED
    assert failed.turn.status.value == "failed"
    assert failed.turn.started_at is None
    assert failed.turn.finished_at is not None
    assert controller.record.phase is InteractiveRunPhase.OPEN
    assert controller.active_turn is None

    monkeypatch.setattr(provider, "start_turn", original)
    retried = await controller.dispatch("lead", "retry")
    assert retried.result.status is ProviderTurnStatus.COMPLETED
    await controller.close(InteractiveRunOutcome.CANCELLED, reason="start failure cleanup")


async def test_provider_structured_control_applies_only_after_turn_terminal(
    tmp_path: Path,
) -> None:
    controller, _team, _source, _launches = await _controller(tmp_path)
    request = ControlRequestV1(
        schema_version=1,
        kind="control-request",
        request_id="provider-work-update",
        run_id=controller.record.run_id,
        source_turn_id="turn-1",
        actor=ControlActor.LEAD,
        actor_member="lead",
        action=ControlAction.WORK_UPDATE,
        work_item_id="implement",
        status=TeamTaskStatus.RUNNING,
    )
    outcome = await controller.dispatch("lead", "EMIT:" + request.model_dump_json())
    assert outcome.result.status is ProviderTurnStatus.COMPLETED
    receipt = controller.archive.load_control_receipt(request.request_id)
    terminal_sequence = controller.archive.event_sequence("turn-terminal", "turn-1")
    queued_sequence = controller.archive.event_sequence("control-queued", request.request_id)
    assert receipt.status is ReceiptStatus.APPLIED
    assert receipt.committed_source_sequence == terminal_sequence
    assert queued_sequence > terminal_sequence
    assert controller.work_items["implement"].status is TeamTaskStatus.RUNNING
    await controller.close(InteractiveRunOutcome.CANCELLED, reason="control test cleanup")


async def test_turn_control_batch_is_conflict_safe_and_applies_completion_last(
    tmp_path: Path,
) -> None:
    controller, _team, _source, _launches = await _controller(tmp_path)
    await controller.dispatch("lead", "proposal source")
    proposal = CompletionProposalV1(
        schema_version=1,
        kind="completion-proposal",
        run_id=controller.record.run_id,
        proposal_id="proposal-batch",
        proposed_by="lead",
        source_turn_id="turn-1",
        summary="Ready for owner review.",
        criteria=[CompletionCriterionV1(criterion="tests pass", evidence=["green"])],
        work_items=["implement"],
        proposed_at=controller.clock(),
    )
    controller.proposals[proposal.proposal_id] = proposal
    controller.archive.write_proposal(proposal)
    controller._update_run(completion_proposals=[proposal.proposal_id])
    completion = ControlRequestV1(
        schema_version=1,
        kind="control-request",
        request_id="batch-completion",
        run_id=controller.record.run_id,
        source_turn_id="turn-2",
        actor=ControlActor.LEAD,
        actor_member="lead",
        action=ControlAction.COMPLETION_PROPOSE,
        completion_proposal=proposal.proposal_id,
    )
    update = ControlRequestV1(
        schema_version=1,
        kind="control-request",
        request_id="batch-work-update",
        run_id=controller.record.run_id,
        source_turn_id="turn-2",
        actor=ControlActor.LEAD,
        actor_member="lead",
        action=ControlAction.WORK_UPDATE,
        work_item_id="implement",
        status=TeamTaskStatus.RUNNING,
    )
    outcome = await controller.dispatch(
        "lead",
        "EMIT:" + completion.model_dump_json() + "\n" + update.model_dump_json(),
    )

    assert outcome.result.status is ProviderTurnStatus.COMPLETED
    assert controller.work_items["implement"].status is TeamTaskStatus.RUNNING
    assert (
        controller.archive.load_control_receipt("batch-work-update").status is ReceiptStatus.APPLIED
    )
    assert (
        controller.archive.load_control_receipt("batch-completion").status is ReceiptStatus.APPLIED
    )
    assert controller.record.phase is InteractiveRunPhase.COMPLETION_PENDING
    assert controller.session_records["lead"].status.value == "open"
    await controller.decide_completion(accept=False)

    first = update.model_copy(
        update={"request_id": "conflicting-control", "source_turn_id": "turn-3"}
    )
    second = first.model_copy(update={"status": TeamTaskStatus.COMPLETED})
    conflict_outcome = await controller.dispatch(
        "lead",
        "EMIT:" + first.model_dump_json() + "\n" + second.model_dump_json(),
    )
    assert conflict_outcome.result.status is ProviderTurnStatus.COMPLETED
    conflict = controller.archive.load_control_receipt("conflicting-control")
    assert conflict.status is ReceiptStatus.FAILED
    assert "conflicting duplicate" in (conflict.reason or "")
    assert controller.work_items["implement"].status is TeamTaskStatus.RUNNING
    assert controller.session_records["lead"].status.value == "open"
    await controller.close(InteractiveRunOutcome.CANCELLED, reason="control batch cleanup")


async def test_control_request_idempotency_rejects_payload_substitution(tmp_path: Path) -> None:
    controller, _team, _source, _launches = await _controller(tmp_path)
    first = ControlRequestV1(
        schema_version=1,
        kind="control-request",
        request_id="stable-control-id",
        run_id=controller.record.run_id,
        actor=ControlActor.USER,
        action=ControlAction.WORK_UPDATE,
        work_item_id="implement",
        status=TeamTaskStatus.RUNNING,
    )
    receipt = await controller.queue_control(first)
    assert await controller.queue_control(first) == receipt
    with pytest.raises(InteractiveControllerError, match="different payload"):
        await controller.queue_control(
            first.model_copy(update={"status": TeamTaskStatus.COMPLETED})
        )
    assert controller.archive.load_control_request(first.request_id) == first
    await controller.close(InteractiveRunOutcome.CANCELLED, reason="idempotency cleanup")


async def test_close_failure_is_truthful_and_retains_the_workspace_reservation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    controller, _team, _source, launches = await _controller(tmp_path)
    provider = launches["reviewer"].provider
    original = provider.close_member

    async def close_but_report_failure(
        session: ProviderSession,
        reason: str,
    ) -> CloseFactsV1:
        facts = await original(session, reason)
        return facts.model_copy(update={"logical_session": CleanupFact.FAILED})

    monkeypatch.setattr(provider, "close_member", close_but_report_failure)
    record = await controller.close(
        InteractiveRunOutcome.CANCELLED,
        reason="injected close failure",
    )
    assert record.phase is InteractiveRunPhase.CLOSE_FAILED
    assert record.outcome is None
    assert record.cleanup is not None
    assert record.cleanup.logical_session is CleanupFact.FAILED
    assert len(list((tmp_path / "home" / "workspace-reservations").glob("*.json"))) == 1
    assert controller.lease.descriptor is not None

    controller.reservation.release(Path(record.workspace), record.run_id)
    controller.lease.release()


async def test_manifest_and_reservation_failures_remain_retryable_and_reserved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_controller, _team, _source, _launches = await _controller(
        tmp_path / "manifest",
        run_id="run-manifest-close-failure",
    )
    original_finalize = manifest_controller.archive.finalize_manifest

    def fail_manifest() -> None:
        raise InteractiveArchiveError("injected manifest failure")

    monkeypatch.setattr(manifest_controller.archive, "finalize_manifest", fail_manifest)
    failed = await manifest_controller.close(
        InteractiveRunOutcome.CANCELLED,
        reason="manifest failure",
    )
    assert failed.phase is InteractiveRunPhase.CLOSE_FAILED
    assert failed.outcome is None
    assert failed.cleanup is not None
    assert failed.cleanup.local_state is CleanupFact.FAILED
    assert manifest_controller.lease.descriptor is not None
    assert list((tmp_path / "manifest" / "home" / "workspace-reservations").glob("*.json"))

    monkeypatch.setattr(manifest_controller.archive, "finalize_manifest", original_finalize)
    retried = await manifest_controller.close(
        InteractiveRunOutcome.CANCELLED,
        reason="manifest retry",
    )
    assert retried.phase is InteractiveRunPhase.CLOSED
    assert manifest_controller.archive.verify_manifest() == []

    reservation_controller, _team, _source, _launches = await _controller(
        tmp_path / "reservation",
        run_id="run-reservation-close-failure",
    )
    original_release = reservation_controller.reservation.release

    def fail_release(_workspace: Path, _run_id: str) -> None:
        raise OSError("injected reservation release failure")

    monkeypatch.setattr(reservation_controller.reservation, "release", fail_release)
    failed = await reservation_controller.close(
        InteractiveRunOutcome.CANCELLED,
        reason="reservation failure",
    )
    assert failed.phase is InteractiveRunPhase.CLOSE_FAILED
    assert failed.outcome is None
    assert reservation_controller.archive.verify_manifest() == []
    assert reservation_controller.lease.descriptor is not None
    assert list((tmp_path / "reservation" / "home" / "workspace-reservations").glob("*.json"))

    monkeypatch.setattr(reservation_controller.reservation, "release", original_release)
    retried = await reservation_controller.close(
        InteractiveRunOutcome.CANCELLED,
        reason="reservation retry",
    )
    assert retried.phase is InteractiveRunPhase.CLOSED
    assert reservation_controller.archive.verify_manifest() == []


async def test_failed_event_append_does_not_create_a_sequence_gap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    controller, _team, _source, _launches = await _controller(tmp_path)
    original_append = controller.archive._append_json_line
    before = controller.archive._event_sequence

    def fail_append(_relative: str, _payload: object) -> None:
        raise OSError("injected append failure")

    monkeypatch.setattr(controller.archive, "_append_json_line", fail_append)
    with pytest.raises(OSError, match="injected append failure"):
        controller.archive.append_event(controller.record.run_id, "injected-event")
    assert controller.archive._event_sequence == before

    monkeypatch.setattr(controller.archive, "_append_json_line", original_append)
    event = controller.archive.append_event(controller.record.run_id, "append-retry")
    assert event.sequence == before + 1
    assert InteractiveArchive(controller.archive.root)._event_sequence == before + 1
    await controller.close(InteractiveRunOutcome.CANCELLED, reason="event sequence cleanup")


async def test_work_controls_completion_reject_continue_accept_and_cleanup(tmp_path: Path) -> None:
    controller, _team, _source, _launches = await _controller(tmp_path)
    turn = await controller.dispatch("lead", "work complete")
    created = WorkItemV1(
        schema_version=1,
        kind="work-item",
        run_id=controller.record.run_id,
        id="extra",
        subject="Extra bounded work",
        owner="lead",
        status=TeamTaskStatus.PENDING,
    )
    receipt = await controller.queue_control(
        ControlRequestV1(
            schema_version=1,
            kind="control-request",
            request_id="control-user-create",
            run_id=controller.record.run_id,
            actor=ControlActor.USER,
            action=ControlAction.WORK_CREATE,
            work_item=created,
        )
    )
    assert receipt.status is ReceiptStatus.APPLIED
    denied = await controller.queue_control(
        ControlRequestV1(
            schema_version=1,
            kind="control-request",
            request_id="control-member-update",
            run_id=controller.record.run_id,
            actor=ControlActor.MEMBER,
            actor_member="reviewer",
            action=ControlAction.WORK_UPDATE,
            work_item_id="extra",
            status=TeamTaskStatus.RUNNING,
        )
    )
    assert denied.status is ReceiptStatus.DENIED

    criteria = [CompletionCriterionV1(criterion="tests pass", evidence=["focused green"])]
    with pytest.raises(InteractiveControllerError, match="non-empty evidence"):
        await controller.propose_completion(
            proposed_by="lead",
            source_turn_id=turn.turn.turn_id,
            summary="unsupported completion",
            criteria=[CompletionCriterionV1(criterion="tests pass", evidence=[])],
            work_items=["implement", "review", "extra"],
        )
    first = await controller.propose_completion(
        proposed_by="lead",
        source_turn_id=turn.turn.turn_id,
        summary="ready for owner review",
        criteria=criteria,
        work_items=["implement", "review", "extra"],
    )
    assert first.status is ReceiptStatus.APPLIED
    assert first.committed_source_sequence == controller.archive.event_sequence(
        "turn-terminal", turn.turn.turn_id
    )
    assert controller.record.phase.value == "completion-pending"
    await controller.decide_completion(accept=False)
    assert controller.record.phase.value == "open"
    reviewer_turn = await controller.dispatch("reviewer", "continue review")
    with pytest.raises(InteractiveControllerError, match="originate from a Lead turn"):
        await controller.propose_completion(
            proposed_by="lead",
            source_turn_id=reviewer_turn.turn.turn_id,
            summary="reviewer cannot originate completion",
            criteria=criteria,
            work_items=["implement", "review", "extra"],
        )
    continued = await controller.dispatch("lead", "continue after review")
    assert continued.result.status is ProviderTurnStatus.COMPLETED

    await controller.propose_completion(
        proposed_by="lead",
        source_turn_id=continued.turn.turn_id,
        summary="ready after continuation",
        criteria=criteria,
        work_items=["implement", "review", "extra"],
    )
    closed = await controller.decide_completion(accept=True)
    assert closed.phase is InteractiveRunPhase.CLOSED
    assert closed.outcome is InteractiveRunOutcome.SUCCEEDED
    export = controller.archive.export_audit(tmp_path / "audit-export")
    assert not any(export.rglob("*.events.jsonl"))
    assert not (export / "runtime").exists()
    assert InteractiveArchive(export).verify_manifest() == []
    exported_bytes = b"\n".join(path.read_bytes() for path in export.rglob("*") if path.is_file())
    assert b"work complete" not in exported_bytes
    assert b"continue after review" not in exported_bytes

    unsafe = controller.archive.root / "unsafe-link"
    try:
        unsafe.symlink_to(Path(controller.record.workspace) / "tracked.txt")
    except OSError:
        pass
    else:
        assert controller.archive.verify_manifest() == ["unsafe symlink: unsafe-link"]
        with pytest.raises(InteractiveArchiveError, match="manifest is invalid"):
            controller.archive.export_audit(tmp_path / "rejected-audit-export")
        unsafe.unlink()
        assert controller.archive.verify_manifest() == []

    store = InteractiveRunStore(tmp_path / "home" / "runs")
    assert [record.run_id for record in store.list_records()] == [closed.run_id]
    store.cleanup_closed(closed.run_id)
    assert not controller.archive.root.exists()


async def test_stream_protocol_negotiates_recovers_from_bad_frames_and_correlates(
    tmp_path: Path,
) -> None:
    controller, _team, _source, _launches = await _controller(tmp_path, writable=True)
    frames: list[dict[str, object]] = []

    async def write(frame: dict[str, object]) -> None:
        frames.append(frame)

    stream = StreamSession(controller, write)
    await stream.feed(b"x" * (stream.decoder.max_frame_bytes + 1))
    assert frames[-1]["error"]["code"] == "malformed"  # type: ignore[index]
    await stream.feed(b"{bad json}\n")
    negotiate = {
        "schema": {"kind": "stream-command", "version": 1},
        "id": "negotiate",
        "sequence": 0,
        "command": "negotiate",
        "versions": [1],
        "client_mode": "attended",
    }
    encoded = (json.dumps(negotiate) + "\n").encode()
    await stream.feed(encoded[:13])
    assert frames[-1]["status"] == "error"
    await stream.feed(encoded[13:])
    assert frames[-1]["protocol_version"] == 1

    async def command(sequence: int, command_id: str, name: str, **data: object) -> None:
        payload = {
            "schema": {"kind": "stream-command", "version": 1},
            "id": command_id,
            "sequence": sequence,
            "command": name,
            **data,
        }
        await stream.feed((json.dumps(payload) + "\n").encode())

    await command(2, "too-early", "status")
    assert frames[-1]["error"] == {
        "code": "out-of-order",
        "message": "expected client sequence 1, got 2",
    }
    await command(1, "status", "status")
    await command(2, "status", "status")
    assert frames[-1]["error"]["code"] == "duplicate"
    await command(3, "unsupported", "future.command")
    assert frames[-1]["error"]["code"] == "unsupported-command"

    await command(4, "turn-one", "turn.start", member="lead", text="hello")
    assert stream.turn_task is not None
    await stream.turn_task
    terminal = next(
        frame
        for frame in reversed(frames)
        if frame.get("event") == "turn-terminal" and frame.get("correlation_id") == "turn-one"
    )
    assert terminal["result"]["text"] == "turn-1:hello"  # type: ignore[index]

    await command(
        5,
        "turn-permission",
        "turn.start",
        member="lead",
        text="PERMISSION:workspace-write",
        work_item_id="implement",
    )
    for _ in range(100):
        if stream.permission_waiters:
            break
        await asyncio.sleep(0.01)
    assert list(stream.permission_waiters) == ["permission-1"]
    await command(
        6,
        "permission-answer",
        "permission.respond",
        permission_id="permission-1",
        approved=True,
        attended=True,
    )
    assert stream.turn_task is not None
    await stream.turn_task
    await command(7, "dynamic-denied", "dynamic.member.create")
    assert frames[-1]["error"]["code"] == "dynamic-members-disabled"

    await stream.finish()
    assert controller.record.phase is InteractiveRunPhase.INTERRUPTED
    assert [frame["sequence"] for frame in frames] == list(range(len(frames)))
    assert all(frame["run_id"] == controller.record.run_id for frame in frames)
    assert all("kind" in frame["schema"] for frame in frames)  # type: ignore[operator]
    controller.lease.acquire()
    await controller.close(InteractiveRunOutcome.CANCELLED, reason="stream test cleanup")


async def test_stream_partial_eof_is_reported_and_interrupts_without_success(
    tmp_path: Path,
) -> None:
    controller, _team, _source, _launches = await _controller(tmp_path)
    frames: list[dict[str, object]] = []

    async def write(frame: dict[str, object]) -> None:
        frames.append(frame)

    stream = StreamSession(controller, write)
    partial = json.dumps(
        {
            "schema": {"kind": "stream-command", "version": 1},
            "id": "negotiate",
            "sequence": 0,
            "command": "negotiate",
            "versions": [1],
        }
    ).encode()
    await stream.feed(partial)
    assert frames == []
    await stream.finish()
    assert frames[-1]["error"]["code"] == "malformed"  # type: ignore[index]
    assert controller.record.phase is InteractiveRunPhase.INTERRUPTED
    assert controller.record.outcome is None
    controller.lease.acquire()
    await controller.close(InteractiveRunOutcome.CANCELLED, reason="partial EOF cleanup")


async def test_stream_terminal_command_marks_session_closed_without_waiting_for_eof(
    tmp_path: Path,
) -> None:
    controller, _team, _source, _launches = await _controller(tmp_path)
    frames: list[dict[str, object]] = []

    async def write(frame: dict[str, object]) -> None:
        frames.append(frame)

    stream = StreamSession(controller, write)

    async def send(sequence: int, command_id: str, command: str, **data: object) -> None:
        frame = {
            "schema": {"kind": "stream-command", "version": 1},
            "id": command_id,
            "sequence": sequence,
            "command": command,
            **data,
        }
        await stream.feed((json.dumps(frame) + "\n").encode())

    await send(0, "negotiate", "negotiate", versions=[1], client_mode="attended")
    await send(1, "close", "close")
    assert stream.closed
    assert controller.record.phase is InteractiveRunPhase.CLOSED
    assert controller.record.outcome is InteractiveRunOutcome.ABANDONED
    with pytest.raises(InteractiveControllerError, match="does not allow reset"):
        await controller.reset_member("lead")
    with pytest.raises(InteractiveControllerError, match="does not accept controls"):
        await controller.queue_control(
            ControlRequestV1(
                schema_version=1,
                kind="control-request",
                request_id="after-close-control",
                run_id=controller.record.run_id,
                actor=ControlActor.USER,
                action=ControlAction.WORK_UPDATE,
                work_item_id="implement",
                status=TeamTaskStatus.RUNNING,
            )
        )
    await stream.finish()
    assert controller.record.phase is InteractiveRunPhase.CLOSED


async def test_tty_shell_routes_members_and_detaches_on_command(tmp_path: Path) -> None:
    controller, _team, _source, _launches = await _controller(tmp_path)
    inputs = iter(["hello", "/members", "/tasks", "/to reviewer", "review", "/detach"])
    output: list[str] = []
    await run_tty(
        controller,
        input_fn=lambda _prompt: next(inputs),
        output_fn=output.append,
    )
    assert any("turn-1:hello" in line for line in output)
    assert any("reviewer:" in line for line in output)
    assert any("implement:" in line for line in output)
    assert any("turn-1:review" in line for line in output)
    assert controller.record.phase is InteractiveRunPhase.INTERRUPTED
    controller.lease.acquire()
    await controller.close(InteractiveRunOutcome.CANCELLED, reason="TTY test cleanup")


async def test_machine_stream_cannot_self_attest_a_mutation_approval(tmp_path: Path) -> None:
    controller, _team, _source, _launches = await _controller(tmp_path, writable=True)
    frames: list[dict[str, object]] = []

    async def write(frame: dict[str, object]) -> None:
        frames.append(frame)

    stream = StreamSession(controller, write)

    async def send(sequence: int, command_id: str, command: str, **data: object) -> None:
        frame = {
            "schema": {"kind": "stream-command", "version": 1},
            "id": command_id,
            "sequence": sequence,
            "command": command,
            **data,
        }
        await stream.feed((json.dumps(frame) + "\n").encode())

    await send(0, "negotiate", "negotiate", versions=[1])
    await send(
        1,
        "machine-turn",
        "turn.start",
        member="lead",
        text="PERMISSION:workspace-write",
        work_item_id="implement",
    )
    for _ in range(100):
        if stream.permission_waiters:
            break
        await asyncio.sleep(0.01)
    await send(
        2,
        "machine-approval",
        "permission.respond",
        permission_id="permission-1",
        approved=True,
        attended=True,
    )
    assert stream.turn_task is not None
    await stream.turn_task
    terminal = next(frame for frame in reversed(frames) if frame.get("event") == "turn-terminal")
    assert terminal["result"]["status"] == "cancelled"  # type: ignore[index]
    await stream.finish()
    controller.lease.acquire()
    await controller.close(InteractiveRunOutcome.CANCELLED, reason="machine test cleanup")


async def test_initial_member_failure_closes_opened_sessions_and_releases_reservation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    team, source, request, launches = _team_and_request(tmp_path)
    failing = launches["reviewer"].provider

    async def fail_open(_spec: OpenMemberSpec) -> ProviderSession:
        raise FakeProviderError("injected open failure")

    monkeypatch.setattr(failing, "open_member", fail_open)
    with pytest.raises(InteractiveInitializationError, match="injected open failure"):
        await InteractiveController.create(
            request=request,
            team=team,
            team_source=source,
            launches=launches,
            runs_root=tmp_path / "home" / "runs",
            reservations_root=tmp_path / "home" / "workspace-reservations",
            run_id="run-initialization-failure",
        )
    archive = InteractiveArchive(tmp_path / "home" / "runs" / "run-initialization-failure")
    record = archive.load_run()
    assert record.phase is InteractiveRunPhase.CLOSED
    assert record.outcome is InteractiveRunOutcome.FAILED
    assert archive.verify_manifest() == []
    assert not list((tmp_path / "home" / "workspace-reservations").glob("*.json"))
    owned = launches["lead"].provider
    assert isinstance(owned, OwnedProcessFakeProvider)
    assert all(handle.poll() is not None for handle in owned.processes.values())


def test_public_chat_and_runs_cli_use_the_same_controller_service(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    team, source, request, launches = _team_and_request(tmp_path)
    prepared = PreparedChat(
        request=request,
        team=team,
        team_source=source,
        launches=launches,
        runs_root=tmp_path / "home" / "runs",
        reservations_root=tmp_path / "home" / "workspace-reservations",
    )
    monkeypatch.setattr(
        "agentteam.commands.interactive.prepare_assistant_chat",
        lambda **_kwargs: prepared,
    )
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "assistant",
            "chat",
            "implementer",
            "--version",
            "1",
            "--workspace",
            request.workspace,
            "--goal",
            request.goal,
        ],
        input="/abort\n",
        env={"AGENTTEAM_HOME": str(tmp_path / "home")},
    )
    assert result.exit_code == 0, result.output
    assert "run closed" in result.output
    listed = runner.invoke(
        app,
        ["runs", "list", "--json"],
        env={"AGENTTEAM_HOME": str(tmp_path / "home")},
    )
    assert listed.exit_code == 0
    payload = json.loads(listed.output)
    assert len(payload["runs"]) == 1
    assert payload["runs"][0]["phase"] == "closed"

    team, source, request, launches = _team_and_request(tmp_path / "team-cli")
    team_prepared = PreparedChat(
        request=request,
        team=team,
        team_source=source,
        launches=launches,
        runs_root=tmp_path / "home" / "runs",
        reservations_root=tmp_path / "home" / "workspace-reservations",
    )
    monkeypatch.setattr(
        "agentteam.commands.interactive.prepare_team_chat",
        lambda **_kwargs: team_prepared,
    )
    team_result = runner.invoke(
        app,
        [
            "team",
            "chat",
            "interactive-test-team",
            "--version",
            "1",
            "--workspace",
            request.workspace,
            "--goal",
            request.goal,
        ],
        input="/abort\n",
        env={"AGENTTEAM_HOME": str(tmp_path / "home")},
    )
    assert team_result.exit_code == 0, team_result.output

    listed = runner.invoke(
        app,
        ["runs", "list", "--json"],
        env={"AGENTTEAM_HOME": str(tmp_path / "home")},
    )
    runs = json.loads(listed.output)["runs"]
    assert len(runs) == 2
    selected_run = runs[0]["run_id"]
    status = runner.invoke(
        app,
        ["runs", "status", selected_run, "--json"],
        env={"AGENTTEAM_HOME": str(tmp_path / "home")},
    )
    assert status.exit_code == 0, status.output
    assert json.loads(status.output)["manifest_problems"] == []

    export = tmp_path / "cli-audit-export"
    exported = runner.invoke(
        app,
        ["runs", "export", selected_run, str(export), "--json"],
        env={"AGENTTEAM_HOME": str(tmp_path / "home")},
    )
    assert exported.exit_code == 0, exported.output
    assert InteractiveArchive(export).verify_manifest() == []

    cleaned = runner.invoke(
        app,
        ["runs", "cleanup", selected_run, "--json"],
        env={"AGENTTEAM_HOME": str(tmp_path / "home")},
    )
    assert cleaned.exit_code == 0, cleaned.output
    assert json.loads(cleaned.output) == {
        "run_id": selected_run,
        "removed": True,
        "recoverable": False,
    }
