"""Deterministic M1b TeamRun lifecycle over a CoordinationSubstrate."""

from __future__ import annotations

import asyncio
import json
import os
import stat
import sys
import tempfile
import unicodedata
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Any

from pydantic import ValidationError

from agentteam.coordination import create_provider
from agentteam.coordination.protocol import (
    CleanupOutcome,
    CleanupWarningCode,
    CoordinationSubstrate,
    SnapshotState,
    SubstrateTaskStatus,
    WaitTimeoutError,
    wait_for_tasks,
)
from agentteam.domain.bundle import AssistantRefV1, BundleManifestV1
from agentteam.domain.common import TERMINAL_STATUSES, RunStatus
from agentteam.domain.run import (
    Attendance,
    ExecutionBindingV1,
    ExecutionKind,
    ExitV1,
    HarnessInvocationV1,
    IndependenceRecordV1,
    InvocationAuthMode,
    RetryClassification,
    RetryV1,
    SchemaOutcome,
    SubstrateRecordV1,
    SubstrateSnapshotRefV1,
    TargetHashesV1,
    TeamMemberRecordV1,
    TeamRunRecordV1,
    TeamTaskRecordV1,
    TemplateRefV1,
    TimingV1,
)
from agentteam.domain.team import (
    DeliverableRefV1,
    HandoffPayloadV1,
    IndependenceDeclared,
    MemberResultV1,
    TeamTaskStatus,
)
from agentteam.harness import get_adapter
from agentteam.harness.capabilities import CLAUDE_SKILL_LADDER, select_verified
from agentteam.harness.environment import EnvironmentConflictError
from agentteam.harness.process import classify_failure
from agentteam.harness.protocol import StructuredExtractor
from agentteam.harness.rendering import RenderError
from agentteam.harness.skills import ManagedSkillsLease
from agentteam.harness.types import (
    InvocationScope,
    OutputContract,
    RawInvocationV1,
    RenderContext,
    RenderedInvocationV1,
)
from agentteam.resolution.archive import build_bundle_manifest, hash_package
from agentteam.resolution.team import TeamTemplateError, hash_team_template, load_team_template
from agentteam.run.archive import RunArchive
from agentteam.run.events import EventLog
from agentteam.run.ids import new_run_id
from agentteam.run.preflight import PreflightError
from agentteam.run.runner import RunOutcome, default_archive_root
from agentteam.run.team_preflight import ResolvedTeamRun, TeamMemberPlan
from agentteam.run.workspace import TargetError, copy_workspace, exclusions_for, hash_tree


class TeamContentError(ValueError):
    """A member result or declared deliverable violates the portable contract."""


class TeamInfrastructureError(RuntimeError):
    """Archive, transport, provider, or process-spawn infrastructure failed."""


@dataclass(frozen=True)
class _MemberExecution:
    task_id: str
    succeeded: bool


@dataclass(frozen=True)
class _LedgerFact:
    seq: int
    sha256: str
    task_id: str


ProviderFactory = Callable[[Path], CoordinationSubstrate]


def _assistant_ref(plan: TeamMemberPlan) -> AssistantRefV1:
    return AssistantRefV1(
        id=plan.package.definition.id,
        version=plan.package.definition.version,
        package_hash=plan.digest.package_hash,
    )


def _topological_tasks(resolved: ResolvedTeamRun) -> list[str]:
    """Kahn order with declaration-order ready-set tie breaking."""
    tasks = resolved.template.definition.workflow_skeleton
    declared = [task.id for task in tasks]
    blockers = {task.id: set(task.blocked_by) for task in tasks}
    emitted: list[str] = []
    emitted_set: set[str] = set()
    while len(emitted) < len(tasks):
        ready = [
            task_id
            for task_id in declared
            if task_id not in emitted_set and blockers[task_id] <= emitted_set
        ]
        if not ready:
            raise PreflightError("team workflow is cyclic")
        for task_id in ready:
            emitted.append(task_id)
            emitted_set.add(task_id)
    return emitted


def _stub_task(plan: TeamMemberPlan, goal: str) -> str:
    subject = plan.task.subject.replace("{goal}", goal)
    return (
        f"# Team task\n\n{subject}\n\n"
        "# Request\n\nRender-preflight only; do not execute.\n\n"
        "# Handoffs\n\nNo handoffs are available in the deterministic preflight stub.\n"
    )


def _render_context(
    resolved: ResolvedTeamRun,
    plan: TeamMemberPlan,
    bundle: BundleManifestV1,
    *,
    run_id: str,
    invocation_id: str,
    task_file: Path,
    workspace: Path,
    workspace_root: Path,
    config_root: Path,
    scratch: Path,
    environ: Mapping[str, str],
    platform: str,
) -> RenderContext:
    return RenderContext(
        profile=plan.leg.profile,
        definition=plan.package.definition,
        package_root=plan.package.root,
        bundle=bundle,
        selection=plan.selection.selection,
        requested=plan.leg.requested,
        task_file=task_file,
        workspace=workspace,
        workspace_root=workspace_root,
        config_root=config_root,
        scratch_dir=scratch,
        parent_env=dict(environ),
        platform=platform,
        run_id=run_id,
        invocation_id=invocation_id,
        timeout_seconds=min(resolved.timeout_seconds, plan.leg.profile.timeouts.attempt_seconds),
        cli_version=plan.leg.cli_version,
        profile_file=resolved.profile_path,
        output_contract=OutputContract.MEMBER_RESULT,
        workspace_access=plan.task.workspace_access,
        invocation_scope=InvocationScope.TEAM_MEMBER,
    )


def render_team_only(
    resolved: ResolvedTeamRun,
    *,
    environ: Mapping[str, str],
    platform: str = sys.platform,
) -> dict[str, Any]:
    """Emit disposable member-result stub renders without execution state."""
    if resolved.request.output_dir is None:
        raise PreflightError("--render-only needs an output directory")
    root = Path(resolved.request.output_dir)
    root.mkdir(parents=True, exist_ok=True)
    created = datetime.now(tz=UTC)
    members: list[dict[str, str]] = []
    for plan in resolved.members:
        member_root = root / plan.member.name
        workspace = member_root / "workspace"
        config_root = member_root / "config-home"
        scratch = member_root / "scratch"
        for directory in (workspace, config_root, scratch):
            directory.mkdir(parents=True, exist_ok=True)
        task_file = member_root / "task.stub.md"
        task_file.write_text(_stub_task(plan, resolved.request.goal), encoding="utf-8")
        bundle = build_bundle_manifest(
            assistant=_assistant_ref(plan), digest=plan.digest, created_at=created
        )
        (member_root / "bundle-manifest.json").write_text(
            bundle.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )
        rendered = get_adapter(plan.leg.harness).render(
            _render_context(
                resolved,
                plan,
                bundle,
                run_id="run-render-only",
                invocation_id=f"inv-{plan.member.name}",
                task_file=task_file,
                workspace=Path(resolved.request.workspace),
                workspace_root=workspace,
                config_root=config_root,
                scratch=scratch,
                environ=environ,
                platform=platform,
            )
        )
        (member_root / "invocation.render.json").write_text(
            rendered.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )
        members.append(
            {
                "member": plan.member.name,
                "harness": plan.leg.harness.value,
                "decided_by": plan.selection.selection.decided_by.value,
            }
        )
    return {"render_only": True, "mode": "team", "members": members, "output_dir": str(root)}


class _TeamRunner:
    def __init__(
        self,
        resolved: ResolvedTeamRun,
        *,
        environ: Mapping[str, str],
        platform: str,
        home: Path | None,
        provider_factory: ProviderFactory | None,
    ) -> None:
        self.resolved = resolved
        self.environ = dict(environ)
        self.platform = platform
        self.home = home
        self.run_id = new_run_id()
        self.provider_factory = provider_factory
        self.provider: CoordinationSubstrate | None = None
        self.space: str | None = None
        self.archive: RunArchive
        self.events: EventLog
        self.record: TeamRunRecordV1
        self.bundles: dict[str, BundleManifestV1] = {}
        self.workspaces: dict[str, Path] = {}
        self.substrate_ids: dict[str, str] = {}
        self.records: dict[str, HarnessInvocationV1] = {}
        self.ledger: dict[str, _LedgerFact] = {}
        self.blinded: dict[str, list[str]] = {}
        self.causal_tasks: set[str] = set()
        self.failure_reason: str | None = None
        self.processes_stopped = False
        self.provider_completion_returned: set[str] = set()

        definition = resolved.template.definition
        self.plan_by_member = {plan.member.name: plan for plan in resolved.members}
        self.task_by_id = {task.id: task for task in definition.workflow_skeleton}
        self.owner_by_task = {task.id: task.owner for task in definition.workflow_skeleton}
        self.task_by_owner = {task.owner: task.id for task in definition.workflow_skeleton}
        self.outgoing: dict[str, list[str]] = {task.id: [] for task in definition.workflow_skeleton}
        for task in definition.workflow_skeleton:
            for blocker in task.blocked_by:
                self.outgoing[blocker].append(task.id)
        self.independent_pairs = {frozenset(rule.between) for rule in definition.independence}

    def _emit(self, event: str, **facts: Any) -> None:
        self.events.emit(event, **facts)

    def _write_record(self) -> None:
        self.archive.write_run_record(self.record)

    def _task_row(self, task_id: str) -> TeamTaskRecordV1:
        return next(row for row in self.record.tasks if row.id == task_id)

    def _set_task(self, task_id: str, status: TeamTaskStatus) -> None:
        self.record = self.record.model_copy(
            update={
                "tasks": [
                    row.model_copy(update={"status": status}) if row.id == task_id else row
                    for row in self.record.tasks
                ]
            }
        )
        self._write_record()

    def _set_substrate_id(self, task_id: str, substrate_id: str) -> None:
        self.record = self.record.model_copy(
            update={
                "tasks": [
                    row.model_copy(update={"substrate_id": substrate_id})
                    if row.id == task_id
                    else row
                    for row in self.record.tasks
                ]
            }
        )
        self._write_record()

    def _bind(self, member: str, invocation_id: str) -> None:
        binding = ExecutionBindingV1(kind=ExecutionKind.INVOCATION, ref=invocation_id)
        self.record = self.record.model_copy(
            update={
                "members": [
                    row.model_copy(update={"execution": binding}) if row.name == member else row
                    for row in self.record.members
                ]
            }
        )
        self._write_record()

    def create_archive(self) -> None:
        now = datetime.now(tz=UTC)
        for plan in self.resolved.members:
            self.bundles[plan.member.name] = build_bundle_manifest(
                assistant=_assistant_ref(plan), digest=plan.digest, created_at=now
            )
        task_rows = [
            TeamTaskRecordV1(
                id=task.id,
                subject=task.subject.replace("{goal}", self.resolved.request.goal),
                status=(TeamTaskStatus.BLOCKED if task.blocked_by else TeamTaskStatus.PENDING),
                owner=task.owner,
                blocked_by=task.blocked_by,
                workspace_access=task.workspace_access,
                substrate_id=None,
            )
            for task in self.resolved.template.definition.workflow_skeleton
        ]
        declared = IndependenceDeclared.ADVISORY
        self.record = TeamRunRecordV1(
            schema_version=1,
            kind="run-record",
            run_id=self.run_id,
            mode="team",
            template=TemplateRefV1(
                ref=str(self.resolved.template.path), hash=self.resolved.template_hash
            ),
            members=[
                TeamMemberRecordV1(
                    name=plan.member.name,
                    assistant=_assistant_ref(plan),
                    effective_definition_hash=self.bundles[
                        plan.member.name
                    ].effective_definition_hash,
                    execution=None,
                    origin="persistent",
                    visibility="visible",
                    selection=plan.selection.selection,
                )
                for plan in self.resolved.members
            ],
            substrate=SubstrateRecordV1(
                kind=self.resolved.request.substrate, namespace=None, snapshot=None
            ),
            tasks=task_rows,
            independence=IndependenceRecordV1(declared=declared, achieved=None),
            events="events.jsonl",
            timing=TimingV1(started_at=now),
            status=RunStatus.PENDING,
        )
        root = (
            Path(self.resolved.request.output_dir)
            if self.resolved.request.output_dir is not None
            else default_archive_root(self.environ) / self.run_id
        )
        try:
            self.archive, warnings = RunArchive.create_team(
                root,
                run_record=self.record,
                resolved_request=self.resolved.request,
                bundles=self.bundles,
                retain_raw_streams=self.resolved.request.evidence.retain_raw_streams,
                platform=self.platform,
                home=self.home,
            )
        except ValueError as error:
            raise PreflightError(str(error)) from None
        self.events = EventLog(self.archive.events_path, run_id=self.run_id)
        self._emit("run-created")
        for _warning in warnings:
            self._emit("archive-warning", detail="archive root outside the user profile")

    def prepare_workspaces(self) -> None:
        source = Path(self.resolved.request.workspace)
        source_hash = hash_tree(source)
        for plan in self.resolved.members:
            invocation_id = f"inv-{plan.member.name}"
            workspace, _config, _scratch = self.archive.working_dirs(invocation_id)
            copy_workspace(source, workspace, platform=self.platform)
            if hash_tree(workspace) != source_hash:
                raise TeamInfrastructureError(
                    f"workspace copy for {plan.member.name} does not match the source"
                )
            if any(self._path_key(child.name) == "handoff" for child in workspace.iterdir()):
                raise TargetError("the casefolded handoff/ tree is reserved in team workspaces")
            self.workspaces[plan.member.name] = workspace

    def create_coordination(self) -> None:
        root = self.archive.root / "coordination"
        self.provider = (
            self.provider_factory(root)
            if self.provider_factory is not None
            else create_provider(
                self.resolved.request.substrate,
                root,
                environ=self.environ,
                platform=self.platform,
            )
        )
        info = self.provider.info()
        definition = self.resolved.template.definition
        self.space = self.provider.create_space(lead=definition.lead)
        self.record = self.record.model_copy(
            update={
                "substrate": self.record.substrate.model_copy(update={"namespace": self.space}),
                "independence": self.record.independence.model_copy(
                    update={"achieved": info.achieved_isolation}
                ),
                "status": RunStatus.RUNNING,
            }
        )
        self._write_record()
        self._emit("space-created")
        for member in definition.members:
            if member.name != definition.lead:
                self.provider.add_member(self.space, member.name)
                self._emit("member-added", member=member.name)

        by_id = self.task_by_id
        for task_id in _topological_tasks(self.resolved):
            task = by_id[task_id]
            provider_blockers = [self.substrate_ids[item] for item in task.blocked_by]
            minted = self.provider.create_task(
                self.space,
                task.subject.replace("{goal}", self.resolved.request.goal),
                blocked_by=provider_blockers,
            )
            self.substrate_ids[task_id] = minted
            self._set_substrate_id(task_id, minted)
            self._emit("task-created", task_id=task_id, member=task.owner)

    def render_preflight(self) -> None:
        with tempfile.TemporaryDirectory(prefix="agentteam-team-preflight-") as temporary:
            base = Path(temporary)
            for plan in self.resolved.members:
                member_root = base / plan.member.name
                workspace = member_root / "workspace"
                config = member_root / "config-home"
                scratch = member_root / "scratch"
                for directory in (workspace, config, scratch):
                    directory.mkdir(parents=True, exist_ok=True)
                task_file = member_root / "task.stub.md"
                task_file.write_text(_stub_task(plan, self.resolved.request.goal), encoding="utf-8")
                get_adapter(plan.leg.harness).render(
                    _render_context(
                        self.resolved,
                        plan,
                        self.bundles[plan.member.name],
                        run_id=self.run_id,
                        invocation_id=f"inv-{plan.member.name}",
                        task_file=task_file,
                        workspace=Path(self.resolved.request.workspace),
                        workspace_root=workspace,
                        config_root=config,
                        scratch=scratch,
                        environ=self.environ,
                        platform=self.platform,
                    )
                )
                self._emit("render-preflight", task_id=plan.task.id, member=plan.member.name)

    def _incoming_tasks(self, task_id: str) -> list[str]:
        return list(self.task_by_id[task_id].blocked_by)

    def _is_blinded(self, predecessor: str, successor: str) -> bool:
        pair = frozenset({self.owner_by_task[predecessor], self.owner_by_task[successor]})
        return pair in self.independent_pairs

    def _claim_handoffs(self, task_id: str) -> list[tuple[str, str]]:
        incoming = self._incoming_tasks(task_id)
        non_blinded = [item for item in incoming if not self._is_blinded(item, task_id)]
        if not non_blinded:
            return []
        assert self.provider is not None and self.space is not None
        recipient = self.owner_by_task[task_id]
        messages = self.provider.receive(self.space, recipient, limit=len(non_blinded))
        if len(messages) != len(non_blinded):
            raise TeamInfrastructureError(
                f"handoff transport returned {len(messages)} of {len(non_blinded)} bodies"
            )
        claimed: dict[str, str] = {}
        for message in messages:
            try:
                payload = HandoffPayloadV1.model_validate_json(message.body)
            except ValidationError as error:
                raise TeamInfrastructureError("claimed handoff body is not canonical") from error
            if payload.task_id not in non_blinded or payload.task_id in claimed:
                raise TeamInfrastructureError("claimed handoff body has an unexpected task id")
            fact = self.ledger.get(message.body)
            if fact is None or fact.task_id != payload.task_id:
                raise TeamInfrastructureError("claimed handoff body has no matching ledger row")
            claimed[payload.task_id] = message.body
            self._emit(
                "message-claimed",
                task_id=payload.task_id,
                member=recipient,
                seq=fact.seq,
                sender=message.sender,
                recipient=message.recipient,
                sha256=fact.sha256,
            )
        if set(claimed) != set(non_blinded):
            raise TeamInfrastructureError("claimed handoff set does not match completed edges")
        return [(predecessor, claimed[predecessor]) for predecessor in sorted(claimed)]

    def _task_document(self, task_id: str, claimed: list[tuple[str, str]]) -> str:
        row = self._task_row(task_id)
        request_text = Path(self.resolved.request.task_file).read_text(encoding="utf-8")
        sections = [f"# Team task\n\n{row.subject}", f"# Request\n\n{request_text}"]
        handoffs: list[str] = []
        for predecessor, body in claimed:
            handoffs.append(f"## {predecessor}\n\n```json\n{body}\n```")
        for predecessor in sorted(self.blinded.get(task_id, [])):
            handoffs.append(
                f"## {predecessor}\n\nhandoff blinded by declared independence: artifact only"
            )
        sections.append("# Handoffs\n\n" + ("\n\n".join(handoffs) or "None."))
        return "\n\n".join(section.rstrip() for section in sections) + "\n"

    def _render_real(
        self, task_id: str, claimed: list[tuple[str, str]]
    ) -> tuple[RenderedInvocationV1, Path, ManagedSkillsLease | None]:
        member = self.owner_by_task[task_id]
        plan = self.plan_by_member[member]
        invocation_id = f"inv-{member}"
        workspace = self.workspaces[member]
        _workspace, _synthetic_config, scratch = self.archive.working_dirs(invocation_id)
        task_ref = self.archive.write_leg_text(
            invocation_id,
            "task.md",
            self._task_document(task_id, claimed),
            role="team-task",
        )
        task_file = self.archive.root / task_ref.path
        lease: ManagedSkillsLease | None = None
        if (
            plan.leg.harness.value == "claude-code"
            and select_verified(
                plan.leg.profile,
                CLAUDE_SKILL_LADDER,
                cli_version=plan.leg.cli_version,
            )
            == "skills-config-home"
        ):
            lease = ManagedSkillsLease(
                Path(plan.leg.profile.config_home), platform=self.platform
            ).acquire()
        try:
            rendered = get_adapter(plan.leg.harness).render(
                _render_context(
                    self.resolved,
                    plan,
                    self.bundles[member],
                    run_id=self.run_id,
                    invocation_id=invocation_id,
                    task_file=task_file,
                    workspace=workspace,
                    workspace_root=workspace,
                    config_root=Path(plan.leg.profile.config_home),
                    scratch=scratch,
                    environ=self.environ,
                    platform=self.platform,
                )
            )
        except BaseException:
            if lease is not None:
                lease.close()
            raise
        self.archive.write_rendered(invocation_id, rendered)
        return rendered, workspace, lease

    def _pending_invocation(
        self,
        task_id: str,
        rendered: RenderedInvocationV1,
        workspace: Path,
    ) -> HarnessInvocationV1:
        member = self.owner_by_task[task_id]
        plan = self.plan_by_member[member]
        invocation_id = f"inv-{member}"
        before = hash_tree(workspace, exclude=exclusions_for(rendered.files_written, workspace))
        record = HarnessInvocationV1(
            schema_version=1,
            kind="harness-invocation",
            invocation_id=invocation_id,
            run_id=self.run_id,
            requested=plan.leg.requested,
            selection=plan.selection.selection,
            effective_definition_hash=self.bundles[member].effective_definition_hash,
            target=TargetHashesV1(before=before),
            injection=rendered.injection,
            command=rendered.command,
            environment=rendered.environment,
            placeholders=rendered.placeholders,
            attendance=Attendance.ATTENDED,
            auth_mode=InvocationAuthMode.NATIVE_SUBSCRIPTION,
            timing=TimingV1(started_at=datetime.now(tz=UTC)),
            status=RunStatus.PENDING,
        )
        self.archive.write_invocation(record)
        self.records[invocation_id] = record
        self._emit(
            "invocation-allocated",
            invocation_id=invocation_id,
            task_id=task_id,
            member=member,
        )
        self._bind(member, invocation_id)
        return record

    async def _attempt_loop(
        self,
        task_id: str,
        rendered: RenderedInvocationV1,
    ) -> tuple[RawInvocationV1, int, RetryClassification]:
        member = self.owner_by_task[task_id]
        plan = self.plan_by_member[member]
        adapter = get_adapter(plan.leg.harness)
        attempt = 1
        retried_for = RetryClassification.NONE
        max_attempts = 1 + self.resolved.transient_retries
        while True:
            self._emit(
                "leg-started",
                invocation_id=f"inv-{member}",
                task_id=task_id,
                member=member,
                detail=f"attempt {attempt}",
            )
            raw = await adapter.invoke(rendered)
            if raw.exit_code == 0 and not raw.timed_out:
                return raw, attempt, retried_for
            classification = classify_failure(raw)
            if classification is RetryClassification.TRANSIENT and attempt < max_attempts:
                retried_for = classification
                attempt += 1
                self._emit(
                    "leg-retry",
                    invocation_id=f"inv-{member}",
                    task_id=task_id,
                    member=member,
                    detail="transient",
                )
                continue
            return raw, attempt, classification

    def _finish_invocation(
        self,
        record: HarnessInvocationV1,
        *,
        status: RunStatus,
        rendered: RenderedInvocationV1,
        workspace: Path,
        raw: RawInvocationV1 | None,
        attempt: int = 1,
        classification: RetryClassification = RetryClassification.NONE,
        artifacts: list[Any] | None = None,
        schema_outcome: SchemaOutcome = SchemaOutcome.NOT_REQUESTED,
        observed: Any = None,
        usage: Any = None,
        problems: list[str] | None = None,
    ) -> HarnessInvocationV1:
        now = (
            raw.finished_at
            if raw is not None and raw.finished_at is not None
            else datetime.now(tz=UTC)
        )
        final_problems = list(problems or [])
        after: str | None = None
        try:
            after = hash_tree(workspace, exclude=exclusions_for(rendered.files_written, workspace))
        except TargetError as error:
            final_problems.append(str(error))
        target = (
            record.target.model_copy(update={"after": after})
            if after is not None
            else record.target
        )
        final = record.model_copy(
            update={
                "observed": observed if observed is not None else record.observed,
                "usage": usage if usage is not None else record.usage,
                "target": target,
                "retry": RetryV1(
                    classification=classification,
                    attempt=attempt,
                    max_attempts=1 + self.resolved.transient_retries,
                ),
                "exit": ExitV1(
                    code=raw.exit_code if raw is not None else None,
                    signal=raw.signal if raw is not None else None,
                ),
                "schema_outcome": schema_outcome,
                "problems": final_problems,
                "artifacts": artifacts or [],
                "timing": TimingV1(
                    started_at=record.timing.started_at,
                    finished_at=now,
                    duration_ms=max(
                        0,
                        int((now - record.timing.started_at).total_seconds() * 1000),
                    ),
                ),
                "status": status,
            }
        )
        self.records[record.invocation_id] = final
        self.archive.write_invocation(final)
        return final

    @staticmethod
    def _path_key(path: str) -> str:
        return unicodedata.normalize("NFC", path).casefold()

    def _deliverables(
        self,
        task_id: str,
        result: MemberResultV1,
        rendered: RenderedInvocationV1,
        workspace: Path,
    ) -> list[DeliverableRefV1]:
        member = self.owner_by_task[task_id]
        invocation_id = f"inv-{member}"
        keys: list[str] = []
        for value in result.deliverables:
            if value != unicodedata.normalize("NFC", value):
                raise TeamContentError(f"deliverable path is not NFC: {value!r}")
            try:
                DeliverableRefV1(path=value, sha256="0" * 64)
            except ValidationError as error:
                raise TeamContentError(f"unsafe deliverable path: {value!r}") from error
            key = self._path_key(value)
            if key == "handoff" or key.startswith("handoff/"):
                raise TeamContentError("the handoff/ tree is reserved")
            keys.append(key)
        if len(set(keys)) != len(keys):
            raise TeamContentError("declared deliverable paths collide canonically")
        for index, key in enumerate(keys):
            for other in keys[index + 1 :]:
                if key.startswith(other + "/") or other.startswith(key + "/"):
                    raise TeamContentError("declared deliverable paths have a prefix collision")

        denied: set[str] = set()
        for write in rendered.files_written:
            try:
                relative = write.path.relative_to(workspace).as_posix()
            except ValueError:
                continue
            parts = PurePosixPath(relative).parts
            for length in range(1, len(parts) + 1):
                denied.add(self._path_key(PurePosixPath(*parts[:length]).as_posix()))
        for key in keys:
            if any(key == prefix or key.startswith(prefix + "/") for prefix in denied):
                raise TeamContentError("deliverable collides with a renderer-owned path")

        refs: list[DeliverableRefV1] = []
        for value in result.deliverables:
            current = workspace
            parts = PurePosixPath(value).parts
            for index, part in enumerate(parts):
                current = current / part
                try:
                    metadata = os.lstat(current)
                except OSError as error:
                    raise TeamContentError(f"declared deliverable is missing: {value}") from error
                if stat.S_ISLNK(metadata.st_mode):
                    raise TeamContentError(f"deliverable path contains a symlink: {value}")
                if index < len(parts) - 1 and not stat.S_ISDIR(metadata.st_mode):
                    raise TeamContentError(f"deliverable parent is not a directory: {value}")
                if index == len(parts) - 1 and not stat.S_ISREG(metadata.st_mode):
                    raise TeamContentError(f"deliverable is not a regular file: {value}")
            data = current.read_bytes()
            digest = sha256(data).hexdigest()
            artifact = self.archive.write_deliverable(invocation_id, value, data)
            archived = self.archive.root / artifact.path
            if artifact.sha256 != digest or sha256(archived.read_bytes()).hexdigest() != digest:
                raise OSError(f"archived deliverable digest mismatch: {value}")
            refs.append(DeliverableRefV1(path=artifact.path, sha256=digest))
            self._emit(
                "deliverable-archived",
                invocation_id=invocation_id,
                task_id=task_id,
                member=member,
                sha256=digest,
                detail=value,
            )
        return refs

    def _materialize(
        self,
        predecessor: str,
        successor: str,
        refs: list[DeliverableRefV1],
    ) -> None:
        successor_member = self.owner_by_task[successor]
        root = self.workspaces[successor_member] / "handoff" / predecessor
        for ref in refs:
            archive_prefix = (
                self.archive.leg_dir(f"inv-{self.owner_by_task[predecessor]}")
                .relative_to(self.archive.root)
                .as_posix()
                + "/deliverables/"
            )
            if not ref.path.startswith(archive_prefix):
                raise OSError("deliverable reference does not belong to its predecessor")
            relative = ref.path[len(archive_prefix) :]
            destination = root.joinpath(*PurePosixPath(relative).parts)
            current = destination.parent
            ancestry: list[Path] = []
            while current != self.workspaces[successor_member]:
                ancestry.append(current)
                current = current.parent
            for directory in reversed(ancestry):
                if directory.exists() or directory.is_symlink():
                    metadata = os.lstat(directory)
                    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                        raise TeamContentError("handoff destination has an unsafe parent")
                else:
                    directory.mkdir(mode=0o700)
            if destination.exists() or destination.is_symlink():
                raise TeamContentError("handoff destination collides with workspace content")
            data = (self.archive.root / ref.path).read_bytes()
            if sha256(data).hexdigest() != ref.sha256:
                raise OSError("deliverable changed before materialization")
            descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            try:
                with os.fdopen(descriptor, "wb") as handle:
                    descriptor = -1
                    handle.write(data)
            finally:
                if descriptor >= 0:
                    os.close(descriptor)
            if sha256(destination.read_bytes()).hexdigest() != ref.sha256:
                raise OSError("materialized deliverable digest mismatch")
            self._emit(
                "deliverable-materialized",
                task_id=predecessor,
                member=successor_member,
                sha256=ref.sha256,
                detail=relative,
            )

    def _publish_edges(
        self,
        task_id: str,
        result: MemberResultV1,
        deliverables: list[DeliverableRefV1],
    ) -> None:
        assert self.provider is not None and self.space is not None
        sender = self.owner_by_task[task_id]
        for successor in self.outgoing[task_id]:
            self._materialize(task_id, successor, deliverables)
            if self._is_blinded(task_id, successor):
                self.blinded.setdefault(successor, []).append(task_id)
                self._emit(
                    "handoff-blinded",
                    task_id=task_id,
                    member=self.owner_by_task[successor],
                )
                continue
            payload = HandoffPayloadV1(
                task_id=task_id,
                summary=result.summary,
                deliverables=deliverables,
                risks=result.risks,
                done_when=self._task_row(successor).subject,
            )
            body = json.dumps(
                payload.model_dump(mode="json"),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
            recipient = self.owner_by_task[successor]
            seq, digest = self.archive.append_message(sender=sender, recipient=recipient, body=body)
            self.ledger[body] = _LedgerFact(seq=seq, sha256=digest, task_id=task_id)
            self.provider.send(self.space, sender, recipient, body)
            self._emit(
                "message-sent",
                task_id=task_id,
                member=sender,
                seq=seq,
                sender=sender,
                recipient=recipient,
                sha256=digest,
            )

    def _abandon_dependents(self, task_id: str) -> None:
        pending = list(self.outgoing[task_id])
        seen: set[str] = set()
        while pending:
            dependent = pending.pop(0)
            if dependent in seen:
                continue
            seen.add(dependent)
            pending.extend(self.outgoing[dependent])
            row = self._task_row(dependent)
            if row.status not in {TeamTaskStatus.BLOCKED, TeamTaskStatus.PENDING}:
                continue
            member = row.owner
            if f"inv-{member}" in self.records:
                continue
            self._set_task(dependent, TeamTaskStatus.ABANDONED)
            self._emit("task-abandoned", task_id=dependent, member=member)

    def _fail_task(self, task_id: str, reason: str, *, cascade: bool) -> None:
        self.causal_tasks.add(task_id)
        if self.failure_reason is None:
            self.failure_reason = f"task {task_id}: {reason}"
        if self._task_row(task_id).status not in {
            TeamTaskStatus.COMPLETED,
            TeamTaskStatus.FAILED,
        }:
            self._set_task(task_id, TeamTaskStatus.FAILED)
            self._emit("task-failed", task_id=task_id, member=self.owner_by_task[task_id])
        if cascade:
            self._abandon_dependents(task_id)

    async def _execute_member(self, task_id: str) -> _MemberExecution:
        member = self.owner_by_task[task_id]
        invocation_id = f"inv-{member}"
        rendered: RenderedInvocationV1 | None = None
        workspace = self.workspaces[member]
        record: HarnessInvocationV1 | None = None
        lease: ManagedSkillsLease | None = None
        raw: RawInvocationV1 | None = None
        refs: list[Any] = []
        attempt = 1
        classification = RetryClassification.NONE
        schema_outcome = SchemaOutcome.NOT_REQUESTED
        observed: Any = None
        usage: Any = None
        parse_problems: list[str] = []
        try:
            claimed = self._claim_handoffs(task_id)
            rendered, workspace, lease = self._render_real(task_id, claimed)
            record = self._pending_invocation(task_id, rendered, workspace)
            assert self.provider is not None and self.space is not None
            self.provider.update_task(
                self.space,
                self.substrate_ids[task_id],
                SubstrateTaskStatus.RUNNING,
                caller=member,
            )
            self._set_task(task_id, TeamTaskStatus.RUNNING)
            self._emit("task-running", task_id=task_id, member=member)
            try:
                raw, attempt, classification = await self._attempt_loop(task_id, rendered)
            except asyncio.CancelledError:
                raise
            except Exception as error:
                raise TeamInfrastructureError(
                    f"member process could not be spawned: {error}"
                ) from error
            refs = self.archive.write_raw_streams(invocation_id, raw)
            if raw.exit_code != 0 or raw.timed_out:
                status = RunStatus.TIMED_OUT if raw.timed_out else RunStatus.FAILED
                self._finish_invocation(
                    record,
                    status=status,
                    rendered=rendered,
                    workspace=workspace,
                    raw=raw,
                    attempt=attempt,
                    classification=classification,
                    artifacts=refs,
                )
                self._emit(
                    "leg-finished",
                    invocation_id=invocation_id,
                    task_id=task_id,
                    member=member,
                    detail=status.value,
                )
                self._fail_task(task_id, "member invocation failed", cascade=True)
                return _MemberExecution(task_id=task_id, succeeded=False)

            adapter = get_adapter(self.plan_by_member[member].leg.harness)
            if not isinstance(adapter, StructuredExtractor):
                raise TeamInfrastructureError("selected adapter lacks structured extraction")
            extracted = adapter.extract_structured(raw)
            observed = extracted.observed
            usage = extracted.usage
            parse_problems = list(extracted.problems)
            if extracted.hard_failure or extracted.candidate is None:
                schema_outcome = SchemaOutcome.MISSING
                raise TeamContentError("member structured output is missing")
            try:
                result = MemberResultV1.model_validate(extracted.candidate)
            except ValidationError as error:
                schema_outcome = SchemaOutcome.INVALID
                raise TeamContentError(f"invalid member result: {error}") from error
            schema_outcome = SchemaOutcome.VALID
            try:
                hash_tree(
                    workspace,
                    exclude=exclusions_for(rendered.files_written, workspace),
                )
            except TargetError as error:
                raise TeamContentError(str(error)) from error

            refs.append(self.archive.write_member_result(invocation_id, result))
            self._emit(
                "member-result-written",
                invocation_id=invocation_id,
                task_id=task_id,
                member=member,
            )
            deliverables = self._deliverables(task_id, result, rendered, workspace)
            refs.extend(
                [
                    next(
                        artifact
                        for artifact in self._artifact_refs_for_record(invocation_id)
                        if artifact.path == ref.path
                    )
                    for ref in deliverables
                ]
            )
            self._publish_edges(task_id, result, deliverables)
            final = self._finish_invocation(
                record,
                status=RunStatus.SUCCEEDED,
                rendered=rendered,
                workspace=workspace,
                raw=raw,
                attempt=attempt,
                classification=classification,
                artifacts=refs,
                schema_outcome=schema_outcome,
                observed=observed,
                usage=usage,
                problems=parse_problems,
            )
            self._emit(
                "leg-finished",
                invocation_id=invocation_id,
                task_id=task_id,
                member=member,
                detail=final.status.value,
            )
            self.provider.update_task(
                self.space,
                self.substrate_ids[task_id],
                SubstrateTaskStatus.COMPLETED,
                caller=member,
            )
            self.provider_completion_returned.add(task_id)
            self._set_task(task_id, TeamTaskStatus.COMPLETED)
            self._emit("task-completed", task_id=task_id, member=member)
            provider_rows = {row.id: row for row in self.provider.tasks(self.space)}
            for successor in self.outgoing[task_id]:
                run_row = self._task_row(successor)
                provider_row = provider_rows[self.substrate_ids[successor]]
                if (
                    run_row.status is TeamTaskStatus.BLOCKED
                    and provider_row.status is SubstrateTaskStatus.PENDING
                ):
                    self._set_task(successor, TeamTaskStatus.PENDING)
                    self._emit(
                        "task-unblocked",
                        task_id=successor,
                        member=self.owner_by_task[successor],
                    )
            return _MemberExecution(task_id=task_id, succeeded=True)
        except (RenderError, EnvironmentConflictError, TargetError, TeamContentError) as error:
            if record is not None and rendered is not None:
                final = self.records.get(invocation_id, record)
                if final.status not in TERMINAL_STATUSES:
                    self._finish_invocation(
                        final,
                        status=RunStatus.FAILED,
                        rendered=rendered,
                        workspace=workspace,
                        raw=raw,
                        attempt=attempt,
                        classification=classification,
                        artifacts=refs,
                        schema_outcome=schema_outcome,
                        observed=observed,
                        usage=usage,
                        problems=[*parse_problems, str(error)],
                    )
                    self._emit(
                        "leg-finished",
                        invocation_id=invocation_id,
                        task_id=task_id,
                        member=member,
                        detail="failed",
                    )
            self._fail_task(task_id, str(error), cascade=True)
            return _MemberExecution(task_id=task_id, succeeded=False)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            current = self.records.get(invocation_id)
            if (
                current is not None
                and current.status not in TERMINAL_STATUSES
                and rendered is not None
            ):
                self._finish_invocation(
                    current,
                    status=RunStatus.FAILED,
                    rendered=rendered,
                    workspace=workspace,
                    raw=raw,
                    attempt=attempt,
                    classification=classification,
                    artifacts=refs,
                    schema_outcome=schema_outcome,
                    observed=observed,
                    usage=usage,
                    problems=[*parse_problems, "infrastructure failure"],
                )
            self._fail_task(task_id, "infrastructure failure", cascade=False)
            if isinstance(error, TeamInfrastructureError):
                raise
            raise TeamInfrastructureError(f"task {task_id} infrastructure failure") from error
        finally:
            if lease is not None:
                lease.close()

    def _artifact_refs_for_record(self, invocation_id: str) -> list[Any]:
        """Recreate deliverable refs already verified by the archive writer."""
        refs: list[Any] = []
        root = self.archive.leg_dir(invocation_id) / "deliverables"
        if not root.is_dir():
            return refs
        for path in sorted(root.rglob("*")):
            if path.is_file():
                data = path.read_bytes()
                relative = path.relative_to(self.archive.root).as_posix()
                from agentteam.domain.run import ArtifactRefV1

                refs.append(
                    ArtifactRefV1(
                        role="deliverable", path=relative, sha256=sha256(data).hexdigest()
                    )
                )
        return refs

    async def schedule(self) -> None:
        assert self.provider is not None and self.space is not None
        while True:
            try:
                rows = wait_for_tasks(
                    self.provider,
                    self.space,
                    lambda values: (
                        any(row.status is SubstrateTaskStatus.PENDING for row in values)
                        or all(row.status is SubstrateTaskStatus.COMPLETED for row in values)
                    ),
                    timeout_seconds=0.5,
                    poll_interval_seconds=0.01,
                )
            except WaitTimeoutError as error:
                raise TeamInfrastructureError(str(error)) from error
            ready_provider = {row.id for row in rows if row.status is SubstrateTaskStatus.PENDING}
            ready = [
                task.id
                for task in self.resolved.template.definition.workflow_skeleton
                if task.id in self.substrate_ids
                and self.substrate_ids[task.id] in ready_provider
                and self._task_row(task.id).status is TeamTaskStatus.PENDING
            ]
            if not ready:
                if all(row.status is TeamTaskStatus.COMPLETED for row in self.record.tasks):
                    return
                raise TeamInfrastructureError("provider reported no runnable task before closure")

            wave = [asyncio.create_task(self._execute_member(task_id)) for task_id in ready]
            try:
                done, pending = await asyncio.wait(wave, return_when=asyncio.FIRST_EXCEPTION)
            except asyncio.CancelledError:
                for task in wave:
                    task.cancel()
                await asyncio.gather(*wave, return_exceptions=True)
                raise
            fault: BaseException | None = None
            for task in done:
                if not task.cancelled() and task.exception() is not None:
                    fault = task.exception()
                    break
            if fault is not None:
                for task in pending:
                    task.cancel()
                await asyncio.gather(*pending, return_exceptions=True)
                await asyncio.gather(*done, return_exceptions=True)
                if isinstance(fault, Exception):
                    raise fault
                raise TeamInfrastructureError("team wave aborted")
            outcomes = [task.result() for task in done]
            if pending:
                outcomes.extend(await asyncio.gather(*pending))
            if any(not outcome.succeeded for outcome in outcomes):
                return

    def _discover_and_repair_invocations(self) -> None:
        legs = self.archive.root / "legs"
        if legs.is_dir():
            for path in sorted(legs.glob("inv-*/invocation.json")):
                try:
                    record = HarnessInvocationV1.model_validate_json(
                        path.read_text(encoding="utf-8")
                    )
                except (OSError, ValueError):
                    continue
                self.records[record.invocation_id] = record
        now = datetime.now(tz=UTC)
        for invocation_id, record in list(self.records.items()):
            member = invocation_id.removeprefix("inv-")
            task_id = self.task_by_owner.get(member)
            if task_id is None:
                continue
            if record.status not in TERMINAL_STATUSES:
                status = RunStatus.FAILED if task_id in self.causal_tasks else RunStatus.CANCELLED
                final = record.model_copy(
                    update={
                        "status": status,
                        "timing": record.timing.model_copy(update={"finished_at": now}),
                    }
                )
                self.archive.write_invocation(final)
                self.records[invocation_id] = final
            member_row = next(item for item in self.record.members if item.name == member)
            if member_row.execution is None:
                self._bind(member, invocation_id)

    def _terminal_sweep(self) -> None:
        self._discover_and_repair_invocations()
        for row in list(self.record.tasks):
            if row.status in {
                TeamTaskStatus.COMPLETED,
                TeamTaskStatus.FAILED,
                TeamTaskStatus.CANCELLED,
                TeamTaskStatus.ABANDONED,
            }:
                continue
            if row.id in self.provider_completion_returned:
                self._set_task(row.id, TeamTaskStatus.COMPLETED)
                self._emit("task-completed", task_id=row.id, member=row.owner)
                continue
            member = row.owner
            if f"inv-{member}" in self.records:
                self._set_task(row.id, TeamTaskStatus.CANCELLED)
                self._emit("task-cancelled", task_id=row.id, member=member)
            else:
                self._set_task(row.id, TeamTaskStatus.ABANDONED)
                self._emit("task-abandoned", task_id=row.id, member=member)

    def _snapshot_and_cleanup(self) -> bool:
        if self.processes_stopped is False:
            self._emit("processes-stopped", detail="0 active processes")
            self.processes_stopped = True
        if self.provider is None or self.space is None:
            return False
        verified = False
        try:
            snapshot_id = self.provider.snapshot(self.space, f"run-{self.run_id}-final")
            payload = self.provider.read_snapshot(self.space, snapshot_id)
            digest = self.archive.write_coordination_snapshot(payload)
            self.record = self.record.model_copy(
                update={
                    "substrate": self.record.substrate.model_copy(
                        update={
                            "snapshot": SubstrateSnapshotRefV1(
                                id=snapshot_id,
                                path="coordination/snapshot.json",
                                sha256=digest,
                            )
                        }
                    )
                }
            )
            self._write_record()
            verified = True
            self._emit("snapshot-archived", sha256=digest)
        except Exception:
            self._emit("snapshot-failed")
        try:
            outcome = self.provider.cleanup(self.space, copy_out_verified=verified)
        except Exception:
            outcome = CleanupOutcome(
                space_closed=False,
                snapshot_state=SnapshotState.UNKNOWN,
                warning_codes=(CleanupWarningCode.UPSTREAM_CLEANUP_FAILED,),
            )
        detail = json.dumps(
            {
                "space_closed": outcome.space_closed,
                "snapshot_state": outcome.snapshot_state.value,
                "warning_codes": [code.value for code in outcome.warning_codes],
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        self._emit("provider-cleanup", detail=detail)
        if outcome.snapshot_state is SnapshotState.RETAINED:
            self._emit("snapshot-retained")
        return verified

    def _immutability_problem(self) -> str | None:
        for plan in self.resolved.members:
            try:
                current = hash_package(plan.package.root).package_hash
            except Exception:
                return f"member {plan.member.name} package could not be re-hashed"
            if current != plan.digest.package_hash:
                return f"member {plan.member.name} package changed during the run"
        try:
            current_template = load_team_template(self.resolved.template.path)
            current_hash = hash_team_template(current_template)
        except TeamTemplateError:
            return "team template could not be re-hashed"
        if current_hash != self.resolved.template_hash:
            return "team template changed during the run"
        return None

    def finalize(self, *, requested_exit: int, cancelled: bool = False) -> RunOutcome:
        snapshot_ok = self._snapshot_and_cleanup()
        mutation = self._immutability_problem()
        if mutation is not None and self.failure_reason is None:
            self.failure_reason = mutation
        if self.space is not None and not snapshot_ok and self.failure_reason is None:
            self.failure_reason = "final coordination snapshot could not be verified"
        self._terminal_sweep()

        all_completed = all(row.status is TeamTaskStatus.COMPLETED for row in self.record.tasks)
        if cancelled:
            status = RunStatus.CANCELLED
            exit_code = 130
            reason = self.failure_reason or "cancelled by the owner"
        elif self.failure_reason is None and all_completed and snapshot_ok:
            status = RunStatus.SUCCEEDED
            exit_code = 0
            reason = None
        else:
            status = RunStatus.FAILED
            exit_code = requested_exit if requested_exit in {1, 2} else 1
            reason = self.failure_reason or "team workflow did not complete"
        now = datetime.now(tz=UTC)
        self.record = self.record.model_copy(
            update={
                "status": status,
                "failure_reason": reason,
                "timing": self.record.timing.model_copy(
                    update={
                        "finished_at": now,
                        "duration_ms": max(
                            0,
                            int((now - self.record.timing.started_at).total_seconds() * 1000),
                        ),
                    }
                ),
            }
        )
        self._write_record()
        binding_problems = self.archive.verify_team_bindings(self.record)
        if binding_problems:
            raise TeamInfrastructureError("; ".join(binding_problems))
        self._emit("run-cancelled" if cancelled else "run-finished", detail=f"exit {exit_code}")
        self.archive.finalize_manifest()
        summary = {
            "run_id": self.run_id,
            "mode": "team",
            "status": status.value,
            "exit_code": exit_code,
            "archive": str(self.archive.root),
            "tasks": {row.id: row.status.value for row in self.record.tasks},
            "failure_reason": reason,
        }
        human = (
            f"team run {self.run_id} {status.value} (exit {exit_code}); "
            f"archive: {self.archive.root}"
        )
        if reason:
            human += f"; reason: {reason}"
        return RunOutcome(
            exit_code=exit_code,
            run_id=self.run_id,
            archive_root=self.archive.root,
            summary=summary,
            human=human,
        )


async def execute_team_run(
    resolved: ResolvedTeamRun,
    *,
    environ: Mapping[str, str],
    platform: str = sys.platform,
    home: Path | None = None,
    provider_factory: ProviderFactory | None = None,
) -> RunOutcome:
    if not resolved.live_ready:
        raise PreflightError(
            "execute_team_run requires live readiness checks; call preflight_team(..., live=True)"
        )
    if any(plan.leg.cli_version is None for plan in resolved.members):
        raise PreflightError("execute_team_run requires observed CLI versions")
    runner = _TeamRunner(
        resolved,
        environ=environ,
        platform=platform,
        home=home,
        provider_factory=provider_factory,
    )
    runner.create_archive()
    try:
        try:
            runner.prepare_workspaces()
        except TargetError as error:
            runner.failure_reason = str(error)
            return runner.finalize(requested_exit=2)
        except Exception as error:
            runner.failure_reason = str(error)
            return runner.finalize(requested_exit=1)
        try:
            runner.create_coordination()
        except Exception:
            runner.failure_reason = "coordination setup failed"
            return runner.finalize(requested_exit=1)
        try:
            runner.render_preflight()
        except (RenderError, EnvironmentConflictError, TargetError) as error:
            runner.failure_reason = str(error)
            return runner.finalize(requested_exit=2)
        except Exception:
            runner.failure_reason = "render preflight infrastructure failed"
            return runner.finalize(requested_exit=2)
        try:
            await runner.schedule()
        except Exception:
            if runner.failure_reason is None:
                runner.failure_reason = "coordination infrastructure failed"
            return runner.finalize(requested_exit=1)
        requested_exit = 1 if runner.failure_reason is not None else 0
        return runner.finalize(requested_exit=requested_exit)
    except asyncio.CancelledError:
        runner.finalize(requested_exit=130, cancelled=True)
        raise
