"""Durable, serialized interactive TeamRun lifecycle controller."""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
import shutil
import sys
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path

from agentteam.domain.assistant import ArtifactKind, RequirementLevel
from agentteam.domain.common import HarnessId
from agentteam.domain.interactive import (
    CatalogKind,
    CleanupFact,
    CloseFactsV1,
    CompletionCriterionV1,
    CompletionProposalStatus,
    CompletionProposalV1,
    ControlAction,
    ControlActor,
    ControlReceiptV1,
    ControlRequestV1,
    InteractiveMemberRecordV1,
    InteractiveRunOutcome,
    InteractiveRunPhase,
    InteractiveRunRecordV1,
    InteractiveRunRequestV1,
    MemberSessionV1,
    ReceiptStatus,
    SessionStatus,
    TeamTemplateV2,
    TurnRecordV1,
    TurnStatus,
    WorkItemV1,
    WorkspaceCheckpointV1,
)
from agentteam.domain.team import TeamTaskStatus, WorkspaceAccess
from agentteam.execution.protocol import (
    ActiveTurn,
    MemberExecutionProvider,
    OpenMemberSpec,
    ProviderEvent,
    ProviderSession,
    ProviderSuspendFacts,
    ProviderTurnResult,
    ProviderTurnStatus,
    RetireEmptyMemberSpec,
    TurnSpec,
)
from agentteam.interactive.archive import InteractiveArchive, InteractiveArchiveError
from agentteam.interactive.permissions import PermissionDecision, decide_permission
from agentteam.interactive.workspace import (
    ControllerLease,
    WorkspaceReservation,
    best_effort_release,
    canonical_workspace,
    checkpoint_workspace,
)
from agentteam.resolution.archive import ArchiveContractError, hash_package
from agentteam.resolution.package import LoadedPackage, PackageError, load_package
from agentteam.run.ids import new_run_id


class InteractiveControllerError(RuntimeError):
    pass


class InteractiveInitializationError(InteractiveControllerError):
    def __init__(self, run_id: str, message: str) -> None:
        super().__init__(f"interactive run {run_id} initialization failed: {message}")
        self.run_id = run_id


@dataclass(frozen=True)
class MemberLaunch:
    member: str
    assistant: LoadedPackage
    provider: MemberExecutionProvider
    harness: HarnessId
    executable: tuple[str, ...]
    environment: Mapping[str, str]
    config_home_variable: str | None = None
    config_home: Path | None = None
    model: str | None = None
    allowed_tools: tuple[str, ...] = ()
    max_turns: int | None = None


@dataclass(frozen=True)
class TurnOutcome:
    turn: TurnRecordV1
    result: ProviderTurnResult
    text: str
    before_tree_sha256: str
    after_tree_sha256: str


PermissionApprover = Callable[[ProviderEvent, PermissionDecision], Awaitable[bool]]
EventSink = Callable[[ProviderEvent], Awaitable[None]]


_TERMINAL_WORK = {
    TeamTaskStatus.COMPLETED,
    TeamTaskStatus.FAILED,
    TeamTaskStatus.CANCELLED,
    TeamTaskStatus.ABANDONED,
}


class InteractiveController:
    def __init__(
        self,
        *,
        request: InteractiveRunRequestV1,
        team: TeamTemplateV2,
        launches: Mapping[str, MemberLaunch],
        archive: InteractiveArchive,
        reservation: WorkspaceReservation,
        lease: ControllerLease,
        record: InteractiveRunRecordV1,
        platform: str = sys.platform,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.request = request
        self.team = team
        self.launches = dict(launches)
        self.archive = archive
        self.reservation = reservation
        self.lease = lease
        self.record = record
        self.platform = platform
        self.clock = clock or (lambda: datetime.now(tz=UTC))
        self.provider_sessions: dict[str, ProviderSession] = {}
        self.session_records: dict[str, MemberSessionV1] = {}
        self.work_items: dict[str, WorkItemV1] = {}
        self.proposals: dict[str, CompletionProposalV1] = {}
        self.active_turn: ActiveTurn | None = None
        self.active_member: str | None = None
        self.active_turn_id: str | None = None
        self._turn_lock = asyncio.Lock()
        self.last_checkpoint = archive.latest_checkpoint()

    @classmethod
    async def create(
        cls,
        *,
        request: InteractiveRunRequestV1,
        team: TeamTemplateV2,
        team_source: bytes,
        launches: Mapping[str, MemberLaunch],
        runs_root: Path,
        reservations_root: Path,
        run_id: str | None = None,
        platform: str = sys.platform,
        clock: Callable[[], datetime] | None = None,
    ) -> InteractiveController:
        now = clock or (lambda: datetime.now(tz=UTC))
        actual_run_id = run_id or new_run_id(now())
        workspace = canonical_workspace(Path(request.workspace))
        cls._validate_inputs(request, team, launches)
        cls._validate_target(request, team, team_source)
        reservation = WorkspaceReservation(reservations_root, platform=platform)
        reservation.acquire(workspace, actual_run_id)
        archive_root = Path(runs_root) / actual_run_id
        lease: ControllerLease | None = None
        try:
            initial_checkpoint = checkpoint_workspace(workspace, clock=now)
            members = [
                InteractiveMemberRecordV1(
                    name=member.name,
                    assistant=member.assistant,
                    origin="persistent",
                    visibility="visible",
                    session_id=_session_id(member.name, 1),
                )
                for member in team.members
            ]
            work_items = _initial_work_items(actual_run_id, request, team)
            created_at = now()
            record = InteractiveRunRecordV1(
                schema_version=1,
                kind="interactive-run-record",
                run_id=actual_run_id,
                target=request.target,
                goal=request.goal,
                done_when=request.done_when,
                workspace=str(workspace),
                workspace_layout="shared-supplied",
                phase=InteractiveRunPhase.INITIALIZING,
                members=members,
                work_items=list(work_items),
                sessions=[member.session_id for member in members],
                turns=[],
                completion_proposals=[],
                workspace_reservation="reservation.json",
                events="events.jsonl",
                initial_checkpoint=initial_checkpoint,
                created_at=created_at,
                updated_at=created_at,
            )
            assistant_sources = {
                member: launch.assistant.root for member, launch in launches.items()
            }
            archive = InteractiveArchive.create(
                archive_root,
                request=request.model_copy(update={"workspace": str(workspace)}),
                record=record,
                team_source=team_source,
                assistant_sources=assistant_sources,
                platform=platform,
                clock=now,
            )
            snapshot_launches = {
                member: replace(
                    launch,
                    assistant=load_package(archive.root / "definitions" / "assistants" / member),
                )
                for member, launch in launches.items()
            }
            cls._validate_inputs(request, team, snapshot_launches)
            archive.write_workspace_reservation(run_id=actual_run_id, workspace=workspace)
            for item in work_items.values():
                archive.write_work_item(item)
            for member, launch in snapshot_launches.items():
                archive.write_launch_record(
                    member,
                    cls._launch_record_payload(
                        launch,
                        assistant_hash=next(
                            item.assistant.content_hash
                            for item in team.members
                            if item.name == member
                        ),
                        generation=1,
                    ),
                )
            lease = ControllerLease(archive_root / "controller.lock", platform=platform)
            lease.acquire()
            controller = cls(
                request=request.model_copy(update={"workspace": str(workspace)}),
                team=team,
                launches=snapshot_launches,
                archive=archive,
                reservation=reservation,
                lease=lease,
                record=record,
                platform=platform,
                clock=now,
            )
            controller.work_items = work_items
            archive.append_event(actual_run_id, "run-initializing")
            await controller._open_initial_members()
            controller._update_run(phase=InteractiveRunPhase.OPEN, failure_reason=None)
            archive.append_event(actual_run_id, "run-open")
            return controller
        except InteractiveInitializationError:
            raise
        except BaseException:
            best_effort_release(lease)
            if archive_root.exists() and not archive_root.is_symlink():
                shutil.rmtree(archive_root, ignore_errors=True)
            with contextlib.suppress(Exception):
                reservation.release(workspace, actual_run_id)
            raise

    @classmethod
    def attach(
        cls,
        *,
        archive: InteractiveArchive,
        team: TeamTemplateV2,
        launches: Mapping[str, MemberLaunch],
        reservations_root: Path,
        platform: str = sys.platform,
        clock: Callable[[], datetime] | None = None,
    ) -> InteractiveController:
        record = archive.load_run()
        if record.phase is InteractiveRunPhase.CLOSED:
            raise InteractiveControllerError("closed interactive runs cannot be attached")
        request = archive.load_request()
        try:
            snapshot_launches = {
                member: replace(
                    launch,
                    assistant=load_package(archive.root / "definitions" / "assistants" / member),
                )
                for member, launch in launches.items()
            }
            cls._validate_inputs(request, team, snapshot_launches)
            cls._validate_target(
                request,
                team,
                (archive.root / "definitions" / "team.yaml").read_bytes(),
            )
            cls._validate_archived_launches(archive, snapshot_launches)
        except (
            PackageError,
            ArchiveContractError,
            InteractiveArchiveError,
            InteractiveControllerError,
            ValueError,
        ) as error:
            raise InteractiveControllerError(
                f"invalid archived definition snapshot: {error}"
            ) from None
        reservation = WorkspaceReservation(reservations_root, platform=platform)
        try:
            reservation.acquire(Path(record.workspace), record.run_id)
        except Exception as error:
            raise InteractiveControllerError(
                f"cannot prove the workspace reservation for {record.run_id}: {error}"
            ) from None
        lease = ControllerLease(archive.root / "controller.lock", platform=platform)
        lease.acquire()
        controller = cls(
            request=request,
            team=team,
            launches=snapshot_launches,
            archive=archive,
            reservation=reservation,
            lease=lease,
            record=record,
            platform=platform,
            clock=clock,
        )
        try:
            controller.work_items = {item.id: item for item in archive.list_work_items()}
            controller.proposals = {
                proposal.proposal_id: proposal for proposal in archive.list_proposals()
            }
            for member in record.members:
                controller.session_records[member.name] = archive.load_session(member.session_id)
            controller._update_run(
                phase=InteractiveRunPhase.RECOVERY_REQUIRED,
                failure_reason="controller attached; provider continuity is not yet verified",
            )
            archive.append_event(record.run_id, "recovery-required")
            return controller
        except BaseException:
            lease.release()
            raise

    @staticmethod
    def _validate_inputs(
        request: InteractiveRunRequestV1,
        team: TeamTemplateV2,
        launches: Mapping[str, MemberLaunch],
    ) -> None:
        if team.workspace_layout.value != "shared-supplied":
            raise InteractiveControllerError("interactive chat requires shared-supplied layout")
        roster = {member.name for member in team.members}
        if set(launches) != roster:
            raise InteractiveControllerError("launch set must exactly match the Team roster")
        if set(request.members) - roster:
            raise InteractiveControllerError("run request has overrides for unknown Members")
        for member, launch in launches.items():
            if launch.member != member:
                raise InteractiveControllerError(f"launch identity mismatch for Member {member}")
            expected = next(item.assistant for item in team.members if item.name == member)
            definition = launch.assistant.definition
            if (definition.id, definition.version) != (expected.id, expected.version):
                raise InteractiveControllerError(
                    f"Assistant coordinate mismatch for Member {member}"
                )
            try:
                digest = hash_package(launch.assistant.root).package_hash
            except ArchiveContractError as error:
                raise InteractiveControllerError(
                    f"Assistant snapshot is invalid for Member {member}: {error}"
                ) from None
            if digest != expected.content_hash:
                raise InteractiveControllerError(
                    f"Assistant content hash mismatch for Member {member}"
                )

    @staticmethod
    def _validate_target(
        request: InteractiveRunRequestV1,
        team: TeamTemplateV2,
        team_source: bytes,
    ) -> None:
        target = request.target
        if target.kind is CatalogKind.TEAM:
            if (target.id, target.version) != (team.id, team.version):
                raise InteractiveControllerError("Team target coordinate mismatch")
            if hashlib.sha256(team_source).hexdigest() != target.content_hash:
                raise InteractiveControllerError("Team target content hash mismatch")
        elif len(team.members) != 1 or (
            team.members[0].assistant.id,
            team.members[0].assistant.version,
            team.members[0].assistant.content_hash,
        ) != (target.id, target.version, target.content_hash):
            raise InteractiveControllerError(
                "Assistant chat target must exactly match the synthetic Team Member"
            )

    @staticmethod
    def _launch_record_payload(
        launch: MemberLaunch,
        *,
        assistant_hash: str,
        generation: int,
    ) -> dict[str, object]:
        descriptor = launch.provider.describe()
        return {
            "provider": descriptor.provider_id,
            "provider_version": descriptor.version,
            "harness": launch.harness.value,
            "assistant_hash": assistant_hash,
            "generation": generation,
            "executable": list(launch.executable),
            "config_home_variable": launch.config_home_variable,
            "config_home": None if launch.config_home is None else str(launch.config_home),
            "model": launch.model,
            "allowed_tools": list(launch.allowed_tools),
            "max_turns": launch.max_turns,
            "environment_names": sorted(launch.environment),
        }

    @classmethod
    def _validate_archived_launches(
        cls,
        archive: InteractiveArchive,
        launches: Mapping[str, MemberLaunch],
    ) -> None:
        run = archive.load_run()
        current_members = {member.name: member for member in run.members}
        for member, launch in launches.items():
            row = archive.load_launch_record(member)
            session = archive.load_session(current_members[member].session_id)
            expected = cls._launch_record_payload(
                launch,
                assistant_hash=current_members[member].assistant.content_hash,
                generation=session.generation,
            )
            if row != expected:
                raise InteractiveControllerError(
                    f"current launch does not match the archived launch for Member {member}"
                )

    async def _open_initial_members(self) -> None:
        try:
            for member in self.team.members:
                await self._open_member(member.name, generation=1, summary=None)
        except BaseException as error:
            await self._close_initialization_failure(error)
            raise InteractiveInitializationError(self.record.run_id, str(error)) from None

    async def _close_initialization_failure(self, error: BaseException) -> None:
        close_facts: list[CloseFactsV1] = []
        now = self.clock()
        for member_record in self.record.members:
            member = member_record.name
            provider_session = self.provider_sessions.get(member)
            session_record = self.session_records.get(member)
            if provider_session is None:
                facts = CloseFactsV1(
                    logical_session=CleanupFact.NOT_APPLICABLE,
                    process=CleanupFact.NOT_APPLICABLE,
                    local_state=CleanupFact.NOT_APPLICABLE,
                    provider_history=CleanupFact.NOT_APPLICABLE,
                )
                if session_record is None:
                    launch = self.launches[member]
                    session_record = MemberSessionV1(
                        schema_version=1,
                        kind="member-session",
                        run_id=self.record.run_id,
                        session_id=member_record.session_id,
                        member=member,
                        generation=1,
                        provider=launch.provider.describe().provider_id,
                        provider_session_ref="not-opened",
                        status=SessionStatus.CLOSED,
                        continuity_verified=False,
                        opened_at=self.record.created_at,
                        closed_at=now,
                        close=facts,
                    )
            else:
                try:
                    facts = await self.launches[member].provider.close_member(
                        provider_session,
                        "interactive initialization failed",
                    )
                except Exception:
                    facts = CloseFactsV1(
                        logical_session=CleanupFact.FAILED,
                        process=CleanupFact.UNKNOWN,
                        local_state=CleanupFact.UNKNOWN,
                        provider_history=CleanupFact.UNKNOWN,
                    )
                assert session_record is not None
                session_record = session_record.model_copy(
                    update={
                        "status": (
                            SessionStatus.CLOSED
                            if _required_cleanup_terminal(facts)
                            else SessionStatus.CLOSE_FAILED
                        ),
                        "closed_at": now,
                        "close": facts,
                    }
                )
            close_facts.append(facts)
            self.session_records[member] = session_record
            self.archive.write_session(session_record)
        disposals: list[CleanupFact] = []
        seen: set[int] = set()
        for launch in self.launches.values():
            if id(launch.provider) in seen:
                continue
            seen.add(id(launch.provider))
            try:
                disposals.append(await launch.provider.dispose_run(self.record.run_id))
            except Exception:
                disposals.append(CleanupFact.FAILED)
        aggregate = _aggregate_close(close_facts, disposals)
        final = self._observe_final_workspace()
        self.archive.write_checkpoint("run", "final", final)
        if _required_cleanup_terminal(aggregate):
            try:
                self.reservation.release(Path(self.record.workspace), self.record.run_id)
            except Exception:
                aggregate = aggregate.model_copy(update={"local_state": CleanupFact.FAILED})
        if _required_cleanup_terminal(aggregate):
            self._update_run(
                phase=InteractiveRunPhase.CLOSED,
                outcome=InteractiveRunOutcome.FAILED,
                cleanup=aggregate,
                final_checkpoint=final,
                failure_reason=f"initial Member open failed: {error}",
            )
            self.archive.append_event(
                self.record.run_id,
                "initialization-failed-closed",
                data={"reason": type(error).__name__},
            )
            self.archive.finalize_manifest()
        else:
            self._update_run(
                phase=InteractiveRunPhase.CLOSE_FAILED,
                cleanup=aggregate,
                final_checkpoint=final,
                failure_reason=f"initial Member open and cleanup failed: {error}",
            )
            self.archive.append_event(
                self.record.run_id,
                "initialization-close-failed",
                data={"reason": type(error).__name__},
            )
        self.provider_sessions.clear()
        self.lease.release()

    async def _open_member(
        self,
        member: str,
        *,
        generation: int,
        summary: str | None,
        resume_ref: str | None = None,
    ) -> ProviderSession:
        self._reload_member_snapshot(member)
        launch = self.launches[member]
        session_id = _session_id(member, generation)
        state_dir = (
            self.archive.root / "runtime" / launch.provider.describe().provider_id / session_id
        )
        prompt = _system_prompt(
            launch.assistant,
            team=self.team,
            member=member,
            goal=self.request.goal,
            done_when=self.request.done_when,
            summary=summary,
        )
        spec = OpenMemberSpec(
            run_id=self.record.run_id,
            member=member,
            session_id=session_id,
            generation=generation,
            workspace=Path(self.record.workspace),
            state_dir=state_dir,
            harness=launch.harness,
            executable=launch.executable,
            config_home_variable=launch.config_home_variable,
            config_home=launch.config_home,
            environment=launch.environment,
            resume_session_ref=resume_ref,
            system_prompt=prompt,
            model=launch.model,
            allowed_tools=launch.allowed_tools,
            max_turns=launch.max_turns,
        )
        session = await launch.provider.open_member(spec)
        try:
            self._validate_provider_session(session, spec, launch.provider.describe().provider_id)
            verified = session.continuity_verified and await launch.provider.verify_continuity(
                session
            )
            if not verified:
                raise InteractiveControllerError(f"provider did not prove continuity for {member}")
        except BaseException:
            cleanup_terminal = False
            try:
                cleanup = await launch.provider.close_member(
                    session, "continuity verification failed"
                )
            except Exception:
                pass
            else:
                cleanup_terminal = _required_cleanup_terminal(cleanup)
            if not cleanup_terminal:
                self._retain_unverified_session(member, spec, session)
            raise
        opened_at = self.clock()
        record = MemberSessionV1(
            schema_version=1,
            kind="member-session",
            run_id=self.record.run_id,
            session_id=session_id,
            member=member,
            generation=generation,
            provider=session.provider_id,
            provider_session_ref=session.provider_session_ref,
            status=SessionStatus.OPEN,
            continuity_verified=True,
            opened_at=opened_at,
        )
        self.provider_sessions[member] = session
        self.session_records[member] = record
        self.archive.write_session(record)
        self.archive.append_event(
            self.record.run_id,
            "member-open",
            correlation_id=session_id,
            data={"member": member, "generation": generation, "provider": session.provider_id},
        )
        return session

    def _retain_unverified_session(
        self,
        member: str,
        spec: OpenMemberSpec,
        session: ProviderSession,
    ) -> None:
        record = MemberSessionV1(
            schema_version=1,
            kind="member-session",
            run_id=self.record.run_id,
            session_id=spec.session_id,
            member=member,
            generation=spec.generation,
            provider=self.launches[member].provider.describe().provider_id,
            provider_session_ref=session.provider_session_ref,
            status=SessionStatus.CONTINUITY_UNVERIFIED,
            continuity_verified=False,
            opened_at=self.clock(),
        )
        self.provider_sessions[member] = session
        self.session_records[member] = record
        self.archive.write_session(record)
        current = next(item for item in self.record.members if item.name == member)
        replacement = current.model_copy(update={"session_id": spec.session_id})
        members = [replacement if item.name == member else item for item in self.record.members]
        self._update_run(
            members=members,
            sessions=[item.session_id for item in members],
            phase=InteractiveRunPhase.RECOVERY_REQUIRED,
            failure_reason=f"provider cleanup is unverified for {member}",
        )
        self.archive.write_launch_record(
            member,
            self._launch_record_payload(
                self.launches[member],
                assistant_hash=replacement.assistant.content_hash,
                generation=spec.generation,
            ),
        )
        self.archive.append_event(
            self.record.run_id,
            "member-open-cleanup-incomplete",
            correlation_id=spec.session_id,
            data={"member": member, "generation": spec.generation},
        )

    @staticmethod
    def _validate_provider_session(
        session: ProviderSession,
        spec: OpenMemberSpec,
        provider_id: str,
    ) -> None:
        identity = (
            session.provider_id,
            session.run_id,
            session.member,
            session.session_id,
            session.generation,
        )
        expected = (
            provider_id,
            spec.run_id,
            spec.member,
            spec.session_id,
            spec.generation,
        )
        if identity != expected:
            raise InteractiveControllerError(
                f"provider returned a mismatched session identity for {spec.member}"
            )
        if session.workspace.resolve(strict=False) != spec.workspace.resolve(strict=False):
            raise InteractiveControllerError(
                f"provider returned a mismatched workspace for {spec.member}"
            )
        if session.state_dir.resolve(strict=False) != spec.state_dir.resolve(strict=False):
            raise InteractiveControllerError(
                f"provider returned a mismatched state directory for {spec.member}"
            )

    def _reload_member_snapshot(self, member: str) -> None:
        launch = self.launches[member]
        expected = next(item.assistant for item in self.team.members if item.name == member)
        try:
            package = load_package(launch.assistant.root)
            digest = hash_package(package.root).package_hash
        except (PackageError, ArchiveContractError) as error:
            raise InteractiveControllerError(
                f"Assistant snapshot is invalid for Member {member}: {error}"
            ) from None
        if (
            package.definition.id,
            package.definition.version,
            digest,
        ) != (expected.id, expected.version, expected.content_hash):
            raise InteractiveControllerError(f"Assistant snapshot changed for Member {member}")
        self.launches[member] = replace(launch, assistant=package)

    async def recover(self) -> dict[str, bool]:
        if self.record.phase is not InteractiveRunPhase.RECOVERY_REQUIRED:
            raise InteractiveControllerError("run is not awaiting recovery")
        results: dict[str, bool] = {}
        for member_record in self.record.members:
            member = member_record.name
            session_record = self.session_records[member]
            launch = self.launches[member]
            existing = self.provider_sessions.get(member)
            if existing is not None:
                try:
                    verified = await launch.provider.verify_continuity(existing)
                except Exception:
                    verified = False
                results[member] = verified
                if not verified:
                    failed = session_record.model_copy(
                        update={
                            "status": SessionStatus.CONTINUITY_UNVERIFIED,
                            "continuity_verified": False,
                        }
                    )
                    self.session_records[member] = failed
                    self.archive.write_session(failed)
                continue
            try:
                await self._open_member(
                    member,
                    generation=session_record.generation,
                    summary=None,
                    resume_ref=session_record.provider_session_ref,
                )
            except Exception:
                try:
                    recreated = await self._recreate_empty_generation(member, session_record)
                except Exception:
                    recreated = False
                results[member] = recreated
                if recreated:
                    continue
                current_record = self.session_records.get(member, session_record)
                if current_record.status is SessionStatus.CLOSED:
                    continue
                failed = current_record.model_copy(
                    update={
                        "status": SessionStatus.CONTINUITY_UNVERIFIED,
                        "continuity_verified": False,
                    }
                )
                self.session_records[member] = failed
                self.archive.write_session(failed)
            else:
                results[member] = True
        if all(results.values()):
            phase = (
                InteractiveRunPhase.COMPLETION_PENDING
                if any(
                    proposal.status is CompletionProposalStatus.PENDING
                    for proposal in self.proposals.values()
                )
                else InteractiveRunPhase.OPEN
            )
            self._update_run(phase=phase, failure_reason=None)
            self.archive.append_event(self.record.run_id, "recovery-complete")
        else:
            self._update_run(
                phase=InteractiveRunPhase.RECOVERY_REQUIRED,
                failure_reason="one or more provider sessions failed strict continuity",
            )
            self.archive.append_event(self.record.run_id, "recovery-incomplete")
        return results

    def _generation_has_turn_attempt(self, session: MemberSessionV1) -> bool:
        for turn_id in self.record.turns:
            turn = self.archive.load_turn(turn_id)
            if turn.session_id == session.session_id and turn.generation == session.generation:
                return True
        return False

    async def _recreate_empty_generation(
        self,
        member: str,
        old: MemberSessionV1,
    ) -> bool:
        if self._generation_has_turn_attempt(old):
            return False
        launch = self.launches[member]
        state_dir = (
            self.archive.root / "runtime" / launch.provider.describe().provider_id / old.session_id
        )
        facts = await launch.provider.retire_empty_member(
            RetireEmptyMemberSpec(
                run_id=self.record.run_id,
                member=member,
                session_id=old.session_id,
                generation=old.generation,
                provider_session_ref=old.provider_session_ref,
                state_dir=state_dir,
            )
        )
        if not _required_cleanup_terminal(facts):
            return False
        closed = old.model_copy(
            update={
                "status": SessionStatus.CLOSED,
                "continuity_verified": False,
                "closed_at": self.clock(),
                "close": facts,
            }
        )
        self.session_records[member] = closed
        self.archive.write_session(closed)
        generation = old.generation + 1
        summary = self.run_state_summary(member=member, generation=generation)
        self.archive.write_state_summary(member, generation, summary)
        replacement_session = await self._open_member(
            member,
            generation=generation,
            summary=summary,
        )
        current = next(item for item in self.record.members if item.name == member)
        replacement = current.model_copy(update={"session_id": replacement_session.session_id})
        members = [replacement if item.name == member else item for item in self.record.members]
        self._update_run(
            members=members,
            sessions=[item.session_id for item in members],
        )
        self.archive.write_launch_record(
            member,
            self._launch_record_payload(
                launch,
                assistant_hash=replacement.assistant.content_hash,
                generation=generation,
            ),
        )
        self.archive.append_event(
            self.record.run_id,
            "empty-session-recreated",
            correlation_id=replacement_session.session_id,
            data={
                "member": member,
                "old-generation": old.generation,
                "new-generation": generation,
            },
        )
        return True

    async def dispatch(
        self,
        member: str,
        text: str,
        *,
        work_item_id: str | None = None,
        permission_approver: PermissionApprover | None = None,
        event_sink: EventSink | None = None,
    ) -> TurnOutcome:
        if not text.strip():
            raise InteractiveControllerError("turn text must be non-empty")
        async with self._turn_lock:
            if self.record.phase is not InteractiveRunPhase.OPEN:
                raise InteractiveControllerError(
                    f"run does not accept prompts in phase {self.record.phase.value}"
                )
            if member not in self.provider_sessions:
                raise InteractiveControllerError(f"Member session is not available: {member}")
            turn_id = _bounded_slug("turn", len(self.record.turns) + 1)
            try:
                before = checkpoint_workspace(Path(self.record.workspace), clock=self.clock)
            except Exception as error:
                self._update_run(
                    phase=InteractiveRunPhase.RECOVERY_REQUIRED,
                    failure_reason=f"workspace observation failed before dispatch: {error}",
                )
                self.archive.append_event(
                    self.record.run_id,
                    "workspace-observation-failed",
                    data={"stage": "before", "error": type(error).__name__},
                )
                raise InteractiveControllerError(
                    f"workspace cannot be observed before dispatch: {error}"
                ) from None
            if (
                before.tree_sha256 != self.last_checkpoint.tree_sha256
                or before.git_status_sha256 != self.last_checkpoint.git_status_sha256
                or before.git_head != self.last_checkpoint.git_head
            ):
                self.archive.append_event(
                    self.record.run_id,
                    "workspace-external-drift",
                    data={"attribution": "unknown"},
                )
            request_id = _bounded_slug("request", len(self.record.turns) + 1)
            session = self.provider_sessions[member]
            queued_at = self.clock()
            turn = TurnRecordV1(
                schema_version=1,
                kind="turn-record",
                run_id=self.record.run_id,
                turn_id=turn_id,
                member=member,
                session_id=session.session_id,
                generation=session.generation,
                prompt_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                status=TurnStatus.QUEUED,
                events=f"turns/{turn_id}.events.jsonl",
                queued_at=queued_at,
            )
            self.archive.write_checkpoint(turn_id, "before", before)
            self.archive.write_turn(turn)
            self._update_run(turns=[*self.record.turns, turn_id])
            self.archive.append_event(
                self.record.run_id, "turn-queued", correlation_id=turn_id, data={"member": member}
            )
            text_parts: list[str] = []
            control_candidates: list[ControlRequestV1] = []
            interruption: BaseException | None = None
            try:
                active = await self.launches[member].provider.start_turn(
                    session,
                    TurnSpec(
                        turn_id=turn_id,
                        request_id=request_id,
                        text=text,
                        timeout_seconds=self.request.limits.attempt_seconds,
                    ),
                )
            except (asyncio.CancelledError, KeyboardInterrupt) as error:
                interruption = error
                result = ProviderTurnResult(
                    status=ProviderTurnStatus.CANCELLED,
                    error=type(error).__name__,
                )
            except Exception as error:
                result = ProviderTurnResult(status=ProviderTurnStatus.FAILED, error=str(error))
            else:
                self.active_turn = active
                self.active_member = member
                self.active_turn_id = turn_id
                started_at = self.clock()
                turn = turn.model_copy(
                    update={"status": TurnStatus.RUNNING, "started_at": started_at}
                )
                self.archive.write_turn(turn)
                self.archive.write_session(
                    self._updated_session(member, status=SessionStatus.TURN_RUNNING)
                )
                self.archive.append_event(
                    self.record.run_id,
                    "turn-running",
                    correlation_id=turn_id,
                    data={"member": member},
                )
                try:
                    async for provider_event in active:
                        self.archive.append_provider_event(turn_id, provider_event)
                        if provider_event.text is not None:
                            text_parts.append(provider_event.text)
                        if provider_event.event == "permission-request":
                            await self._handle_permission(
                                member,
                                provider_event,
                                active,
                                work_item_id=work_item_id,
                                approver=permission_approver,
                            )
                        control_candidates.extend(
                            self._controls_from_event(
                                provider_event,
                                member=member,
                                turn_id=turn_id,
                            )
                        )
                        if event_sink is not None:
                            await event_sink(provider_event)
                    result = await active.result()
                except (asyncio.CancelledError, KeyboardInterrupt) as error:
                    with contextlib.suppress(Exception):
                        await active.cancel("controller turn handling failed")
                    with contextlib.suppress(Exception):
                        await active.result()
                    interruption = error
                    result = ProviderTurnResult(
                        status=ProviderTurnStatus.CANCELLED,
                        error=type(error).__name__,
                    )
                except Exception as error:
                    with contextlib.suppress(Exception):
                        await active.cancel("controller turn handling failed")
                    with contextlib.suppress(Exception):
                        await active.result()
                    result = ProviderTurnResult(
                        status=ProviderTurnStatus.FAILED,
                        error=str(error),
                    )
                finally:
                    self.active_turn = None
                    self.active_member = None
                    self.active_turn_id = None

            output = result.text if result.text is not None else "".join(text_parts)
            control_candidates.extend(
                self._controls_from_text(output, member=member, turn_id=turn_id)
            )
            status = {
                ProviderTurnStatus.COMPLETED: TurnStatus.COMPLETED,
                ProviderTurnStatus.CANCELLED: TurnStatus.CANCELLED,
                ProviderTurnStatus.FAILED: TurnStatus.FAILED,
            }[result.status]
            finished_at = self.clock()
            turn = turn.model_copy(
                update={
                    "status": status,
                    "finished_at": finished_at,
                    "result_sha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
                    "failure_reason": result.error,
                }
            )
            self.archive.write_turn(turn)
            terminal_event = self.archive.append_event(
                self.record.run_id,
                "turn-terminal",
                correlation_id=turn_id,
                data={"member": member, "status": status.value},
            )
            observation_error: Exception | None = None
            try:
                after = checkpoint_workspace(Path(self.record.workspace), clock=self.clock)
            except Exception as error:
                observation_error = error
                after = before
                self.archive.append_event(
                    self.record.run_id,
                    "workspace-observation-failed",
                    correlation_id=turn_id,
                    data={"stage": "after", "error": type(error).__name__},
                )
            self.archive.write_checkpoint(turn_id, "after", after)
            self.last_checkpoint = after
            self.archive.append_event(
                self.record.run_id,
                "workspace-observed",
                correlation_id=turn_id,
                data={
                    "changed": before.tree_sha256 != after.tree_sha256,
                    "git-status-changed": before.git_status_sha256 != after.git_status_sha256,
                    "attribution": "unknown",
                },
            )
            controls, conflicts = _partition_controls(control_candidates)
            for request in conflicts:
                self._record_control_failure(
                    request,
                    terminal_event.sequence,
                    "conflicting duplicate control payload for one request id",
                )
            controls.sort(key=lambda item: item.action is ControlAction.COMPLETION_PROPOSE)
            for request in controls:
                try:
                    await self.queue_control(
                        request,
                        committed_source_sequence=terminal_event.sequence,
                    )
                except InteractiveControllerError as error:
                    self._record_control_failure(
                        request,
                        terminal_event.sequence,
                        str(error),
                    )
            try:
                continuity = await self.launches[member].provider.verify_continuity(session)
            except Exception:
                continuity = False
            if continuity and observation_error is None:
                self.archive.write_session(self._updated_session(member, status=SessionStatus.OPEN))
            else:
                if not continuity:
                    self.archive.write_session(
                        self._updated_session(
                            member,
                            status=SessionStatus.CONTINUITY_UNVERIFIED,
                            continuity_verified=False,
                        )
                    )
                else:
                    self.archive.write_session(
                        self._updated_session(member, status=SessionStatus.OPEN)
                    )
                failure_reason = (
                    f"provider continuity lost for {member}"
                    if not continuity
                    else f"workspace observation failed after {turn_id}: {observation_error}"
                )
                self._update_run(
                    phase=InteractiveRunPhase.RECOVERY_REQUIRED,
                    failure_reason=failure_reason,
                )
            outcome = TurnOutcome(
                turn=turn,
                result=result,
                text=output,
                before_tree_sha256=before.tree_sha256,
                after_tree_sha256=after.tree_sha256,
            )
            if interruption is not None:
                raise interruption
            return outcome

    async def _handle_permission(
        self,
        member: str,
        event: ProviderEvent,
        active: ActiveTurn,
        *,
        work_item_id: str | None,
        approver: PermissionApprover | None,
    ) -> None:
        permission_id = event.data.get("permission_id")
        if not isinstance(permission_id, str) or not permission_id:
            raise InteractiveControllerError("provider permission event has no non-empty id")
        launch = self.launches[member]
        access = self._member_access(member, work_item_id)
        provisional = decide_permission(
            event,
            workspace=Path(self.record.workspace),
            assistant=launch.assistant.definition.permissions,
            member_access=access,
            provider=launch.provider.describe().capabilities,
            attended_approval=False,
        )
        approved = False
        if approver is not None and provisional.attended_approval_required:
            non_attendance_reasons = tuple(
                reason
                for reason in provisional.reasons
                if reason
                not in {
                    "workspace mutation needs attended user approval",
                    "full-access needs attended one-time user approval",
                }
            )
            if not non_attendance_reasons:
                approved = await approver(event, provisional)
        decision = (
            decide_permission(
                event,
                workspace=Path(self.record.workspace),
                assistant=launch.assistant.definition.permissions,
                member_access=access,
                provider=launch.provider.describe().capabilities,
                attended_approval=True,
            )
            if approved
            else provisional
        )
        await active.respond_permission(permission_id, decision.outcome)
        self.archive.append_event(
            self.record.run_id,
            "permission-decided",
            correlation_id=self.active_turn_id,
            data={
                "member": member,
                "classification": decision.classification.value,
                "outcome": decision.outcome.value,
                "attended": approved,
            },
        )

    async def cancel_turn(self, reason: str = "user cancellation") -> str:
        if self.active_turn is None or self.active_member is None:
            return "terminal"
        disposition = await self.launches[self.active_member].provider.cancel_turn(
            self.provider_sessions[self.active_member], reason
        )
        self.archive.append_event(
            self.record.run_id,
            "turn-cancel-requested",
            correlation_id=self.active_turn_id,
            data={"disposition": disposition.value},
        )
        return disposition.value

    async def queue_control(
        self,
        request: ControlRequestV1,
        *,
        committed_source_sequence: int | None = None,
    ) -> ControlReceiptV1:
        if request.run_id != self.record.run_id:
            raise InteractiveControllerError("control request run id mismatch")
        if (self.archive.root / "controls" / "receipts" / f"{request.request_id}.json").exists():
            existing = self.archive.load_control_request(request.request_id)
            if existing != request:
                raise InteractiveControllerError(
                    "control request id was already used for a different payload"
                )
            return self.archive.load_control_receipt(request.request_id)
        turn_committed = False
        if request.source_turn_id is not None:
            if committed_source_sequence is None:
                raise InteractiveControllerError(
                    "turn-sourced control cannot apply before turn commit"
                )
            try:
                expected_sequence = self.archive.event_sequence(
                    "turn-terminal", request.source_turn_id
                )
            except InteractiveArchiveError as error:
                raise InteractiveControllerError(str(error)) from None
            if expected_sequence != committed_source_sequence:
                raise InteractiveControllerError("control source commit sequence mismatch")
            turn_committed = True
        elif committed_source_sequence is not None:
            raise InteractiveControllerError(
                "control without a source turn cannot claim a source commit sequence"
            )
        if self.record.phase is not InteractiveRunPhase.OPEN and not (
            turn_committed and self.record.phase is InteractiveRunPhase.COMPLETION_PENDING
        ):
            raise InteractiveControllerError(
                f"run does not accept controls in phase {self.record.phase.value}"
            )
        queued_at = self.clock()
        receipt = ControlReceiptV1(
            schema_version=1,
            kind="control-receipt",
            request_id=request.request_id,
            run_id=request.run_id,
            status=ReceiptStatus.QUEUED,
            queued_at=queued_at,
            committed_source_sequence=committed_source_sequence,
        )
        self.archive.write_control_request(request)
        self.archive.write_control_receipt(receipt)
        queued_event = self.archive.append_event(
            self.record.run_id,
            "control-queued",
            correlation_id=request.request_id,
            data={"action": request.action.value},
        )
        committed = (
            committed_source_sequence
            if committed_source_sequence is not None
            else queued_event.sequence
        )
        return self._apply_control(request, receipt, committed)

    def _record_control_failure(
        self,
        request: ControlRequestV1,
        committed_sequence: int,
        reason: str,
    ) -> ControlReceiptV1:
        receipt_path = self.archive.root / "controls" / "receipts" / f"{request.request_id}.json"
        if receipt_path.exists():
            existing_request = self.archive.load_control_request(request.request_id)
            if existing_request != request:
                self.archive.append_event(
                    self.record.run_id,
                    "control-replay-conflict",
                    correlation_id=request.request_id,
                )
            return self.archive.load_control_receipt(request.request_id)
        queued_at = self.clock()
        receipt = ControlReceiptV1(
            schema_version=1,
            kind="control-receipt",
            request_id=request.request_id,
            run_id=request.run_id,
            status=ReceiptStatus.QUEUED,
            queued_at=queued_at,
            committed_source_sequence=committed_sequence,
        )
        self.archive.write_control_request(request)
        self.archive.write_control_receipt(receipt)
        self.archive.append_event(
            self.record.run_id,
            "control-queued",
            correlation_id=request.request_id,
            data={"action": request.action.value},
        )
        terminal = receipt.model_copy(
            update={
                "status": ReceiptStatus.FAILED,
                "applied_at": self.clock(),
                "reason": reason,
            }
        )
        self.archive.write_control_receipt(terminal)
        self.archive.append_event(
            self.record.run_id,
            "control-terminal",
            correlation_id=request.request_id,
            data={"status": ReceiptStatus.FAILED.value, "action": request.action.value},
        )
        return terminal

    def _apply_control(
        self,
        request: ControlRequestV1,
        receipt: ControlReceiptV1,
        committed_sequence: int,
    ) -> ControlReceiptV1:
        reason = self._control_denial_reason(request)
        status = ReceiptStatus.APPLIED
        try:
            if reason is not None:
                status = ReceiptStatus.DENIED
            elif request.action is ControlAction.WORK_CREATE:
                assert request.work_item is not None
                self._create_work(request.work_item)
            elif request.action is ControlAction.WORK_UPDATE:
                assert request.work_item_id is not None and request.status is not None
                self._update_work(request.work_item_id, request.status)
            elif request.action is ControlAction.WORK_ASSIGN:
                assert request.work_item_id is not None and request.owner is not None
                self._assign_work(request.work_item_id, request.owner)
            elif request.action is ControlAction.COMPLETION_PROPOSE:
                assert request.completion_proposal is not None
                self._activate_proposal(request.completion_proposal)
        except (InteractiveControllerError, ValueError) as error:
            status = ReceiptStatus.FAILED
            reason = str(error)
        terminal = receipt.model_copy(
            update={
                "status": status,
                "committed_source_sequence": committed_sequence,
                "applied_at": self.clock(),
                "reason": reason,
            }
        )
        self.archive.write_control_receipt(terminal)
        self.archive.append_event(
            self.record.run_id,
            "control-terminal",
            correlation_id=request.request_id,
            data={"status": status.value, "action": request.action.value},
        )
        return terminal

    def _control_denial_reason(self, request: ControlRequestV1) -> str | None:
        if request.actor is ControlActor.USER:
            return None
        if request.actor_member not in self.launches:
            return "control actor is not in the run roster"
        if request.actor is ControlActor.LEAD and request.actor_member != self.team.lead:
            return "only the declared Lead may use Lead controls"
        if request.actor is ControlActor.MEMBER:
            return "non-Lead Members cannot mutate the work graph"
        return None

    def _create_work(self, item: WorkItemV1) -> None:
        if item.run_id != self.record.run_id or item.id in self.work_items:
            raise InteractiveControllerError("work item id is invalid or already exists")
        if item.owner not in self.launches:
            raise InteractiveControllerError("work item owner is not in the roster")
        if set(item.blocked_by) - set(self.work_items):
            raise InteractiveControllerError("work item names unknown blockers")
        expected = (
            TeamTaskStatus.BLOCKED
            if any(
                self.work_items[blocker].status is not TeamTaskStatus.COMPLETED
                for blocker in item.blocked_by
            )
            else TeamTaskStatus.PENDING
        )
        if item.status is not expected:
            raise InteractiveControllerError(f"new work item status must be {expected.value}")
        candidate = {**self.work_items, item.id: item}
        _validate_work_graph(candidate)
        self.work_items[item.id] = item
        self.archive.write_work_item(item)
        self._update_run(work_items=[*self.record.work_items, item.id])

    def _update_work(self, item_id: str, status: TeamTaskStatus) -> None:
        item = self.work_items.get(item_id)
        if item is None:
            raise InteractiveControllerError(f"unknown work item: {item_id}")
        allowed = {
            TeamTaskStatus.BLOCKED: {TeamTaskStatus.PENDING, TeamTaskStatus.CANCELLED},
            TeamTaskStatus.PENDING: {TeamTaskStatus.RUNNING, TeamTaskStatus.CANCELLED},
            TeamTaskStatus.RUNNING: {
                TeamTaskStatus.COMPLETED,
                TeamTaskStatus.FAILED,
                TeamTaskStatus.CANCELLED,
            },
        }.get(item.status, set())
        if status not in allowed:
            raise InteractiveControllerError(
                f"invalid work transition: {item.status.value} -> {status.value}"
            )
        updated = item.model_copy(update={"status": status})
        self.work_items[item_id] = updated
        self.archive.write_work_item(updated)
        if status is TeamTaskStatus.COMPLETED:
            self._unblock_work()

    def _assign_work(self, item_id: str, owner: str) -> None:
        item = self.work_items.get(item_id)
        if item is None or owner not in self.launches:
            raise InteractiveControllerError("unknown work item or owner")
        if item.status in _TERMINAL_WORK:
            raise InteractiveControllerError("terminal work cannot be reassigned")
        updated = item.model_copy(update={"owner": owner})
        self.work_items[item_id] = updated
        self.archive.write_work_item(updated)

    def _unblock_work(self) -> None:
        for item_id, item in list(self.work_items.items()):
            if item.status is TeamTaskStatus.BLOCKED and all(
                self.work_items[blocker].status is TeamTaskStatus.COMPLETED
                for blocker in item.blocked_by
            ):
                updated = item.model_copy(update={"status": TeamTaskStatus.PENDING})
                self.work_items[item_id] = updated
                self.archive.write_work_item(updated)

    def _activate_proposal(self, proposal_id: str) -> None:
        proposal = self.proposals.get(proposal_id)
        if proposal is None or proposal.status is not CompletionProposalStatus.PENDING:
            raise InteractiveControllerError("completion proposal is missing or terminal")
        if self.record.phase is not InteractiveRunPhase.OPEN:
            raise InteractiveControllerError("completion can be proposed only while open")
        self._update_run(phase=InteractiveRunPhase.COMPLETION_PENDING)

    async def propose_completion(
        self,
        *,
        proposed_by: str,
        source_turn_id: str,
        summary: str,
        criteria: list[CompletionCriterionV1],
        work_items: list[str],
    ) -> ControlReceiptV1:
        if self.record.phase is not InteractiveRunPhase.OPEN:
            raise InteractiveControllerError("completion can be proposed only while open")
        if proposed_by != self.team.lead:
            raise InteractiveControllerError("only the Lead may propose completion")
        if source_turn_id not in self.record.turns:
            raise InteractiveControllerError("completion proposal source turn is unknown")
        source_turn = self.archive.load_turn(source_turn_id)
        if source_turn.member != proposed_by:
            raise InteractiveControllerError("completion proposal must originate from a Lead turn")
        if source_turn.status not in {
            TurnStatus.COMPLETED,
            TurnStatus.FAILED,
            TurnStatus.CANCELLED,
        }:
            raise InteractiveControllerError("completion proposal source turn is not committed")
        expected = self.request.done_when
        if [criterion.criterion for criterion in criteria] != expected:
            raise InteractiveControllerError("completion criteria must exactly cover done_when")
        if any(
            not criterion.evidence or any(not evidence.strip() for evidence in criterion.evidence)
            for criterion in criteria
        ):
            raise InteractiveControllerError(
                "completion criteria require non-empty evidence for every done_when item"
            )
        if set(work_items) - set(self.work_items):
            raise InteractiveControllerError("completion proposal references unknown work")
        proposal_id = _bounded_slug("proposal", len(self.proposals) + 1)
        proposal = CompletionProposalV1(
            schema_version=1,
            kind="completion-proposal",
            run_id=self.record.run_id,
            proposal_id=proposal_id,
            proposed_by=proposed_by,
            source_turn_id=source_turn_id,
            summary=summary,
            criteria=criteria,
            work_items=work_items,
            proposed_at=self.clock(),
        )
        self.proposals[proposal_id] = proposal
        self.archive.write_proposal(proposal)
        self._update_run(completion_proposals=[*self.record.completion_proposals, proposal_id])
        request = ControlRequestV1(
            schema_version=1,
            kind="control-request",
            request_id=_bounded_slug("control", len(self.proposals)),
            run_id=self.record.run_id,
            source_turn_id=source_turn_id,
            actor=ControlActor.LEAD,
            actor_member=proposed_by,
            action=ControlAction.COMPLETION_PROPOSE,
            completion_proposal=proposal_id,
        )
        terminal_sequence = self.archive.event_sequence("turn-terminal", source_turn_id)
        self.archive.append_event(
            self.record.run_id,
            "completion-proposal-persisted",
            correlation_id=proposal_id,
        )
        return await self.queue_control(
            request,
            committed_source_sequence=terminal_sequence,
        )

    async def decide_completion(self, *, accept: bool) -> InteractiveRunRecordV1:
        if self.record.phase is not InteractiveRunPhase.COMPLETION_PENDING:
            raise InteractiveControllerError("run has no pending completion proposal")
        pending = [
            proposal
            for proposal in self.proposals.values()
            if proposal.status is CompletionProposalStatus.PENDING
        ]
        if len(pending) != 1:
            raise InteractiveControllerError("run must have exactly one pending proposal")
        proposal = pending[0]
        status = CompletionProposalStatus.ACCEPTED if accept else CompletionProposalStatus.REJECTED
        decided = proposal.model_copy(update={"status": status, "decided_at": self.clock()})
        self.proposals[proposal.proposal_id] = decided
        self.archive.write_proposal(decided)
        self.archive.append_event(
            self.record.run_id,
            "completion-decided",
            correlation_id=proposal.proposal_id,
            data={"accepted": accept},
        )
        if not accept:
            self._update_run(phase=InteractiveRunPhase.OPEN)
            return self.record
        return await self.close(InteractiveRunOutcome.SUCCEEDED, reason="completion accepted")

    async def reset_member(self, member: str) -> MemberSessionV1:
        async with self._turn_lock:
            return await self._reset_member_unlocked(member)

    async def _reset_member_unlocked(self, member: str) -> MemberSessionV1:
        if member not in self.launches:
            raise InteractiveControllerError(f"unknown Member: {member}")
        if self.record.phase not in {
            InteractiveRunPhase.OPEN,
            InteractiveRunPhase.RECOVERY_REQUIRED,
            InteractiveRunPhase.CLOSE_FAILED,
        }:
            raise InteractiveControllerError(
                f"run does not allow reset in phase {self.record.phase.value}"
            )
        if self.active_turn is not None:
            raise InteractiveControllerError("cannot reset while a turn is active")
        old = self.session_records[member]
        if old.status is SessionStatus.CLOSED:
            assert old.close is not None
            facts = old.close
            closed_old = old
        else:
            provider_session = self.provider_sessions.get(member)
            if provider_session is None:
                try:
                    provider_session = await self._open_member(
                        member,
                        generation=old.generation,
                        summary=None,
                        resume_ref=old.provider_session_ref,
                    )
                except Exception:
                    provider_session = None
            if provider_session is not None:
                try:
                    facts = await self.launches[member].provider.close_member(
                        provider_session, "Member reset"
                    )
                except Exception:
                    facts = CloseFactsV1(
                        logical_session=CleanupFact.FAILED,
                        process=CleanupFact.UNKNOWN,
                        local_state=CleanupFact.UNKNOWN,
                        provider_history=CleanupFact.UNKNOWN,
                    )
                else:
                    self.provider_sessions.pop(member, None)
            else:
                state_dir = (
                    self.archive.root
                    / "runtime"
                    / self.launches[member].provider.describe().provider_id
                    / old.session_id
                )
                local = CleanupFact.CONFIRMED
                try:
                    shutil.rmtree(state_dir)
                except FileNotFoundError:
                    local = CleanupFact.NOT_APPLICABLE
                except OSError:
                    local = CleanupFact.FAILED
                facts = CloseFactsV1(
                    logical_session=CleanupFact.UNKNOWN,
                    process=CleanupFact.UNKNOWN,
                    local_state=local,
                    provider_history=CleanupFact.UNKNOWN,
                )
            old_status = (
                SessionStatus.CLOSED
                if _required_cleanup_terminal(facts)
                else SessionStatus.CLOSE_FAILED
            )
            closed_old = old.model_copy(
                update={"status": old_status, "closed_at": self.clock(), "close": facts}
            )
        self.session_records[member] = closed_old
        self.archive.write_session(closed_old)
        if not _required_cleanup_terminal(facts):
            self.session_records[member] = closed_old
            self._update_run(
                phase=InteractiveRunPhase.RECOVERY_REQUIRED,
                failure_reason=f"reset cleanup is incomplete for {member}",
            )
            self.archive.append_event(
                self.record.run_id,
                "member-reset-failed",
                data={"member": member},
            )
            raise InteractiveControllerError(
                f"cannot open a new generation until cleanup is terminal for {member}"
            )
        generation = old.generation + 1
        try:
            summary = self.run_state_summary(member=member, generation=generation)
            self.archive.write_state_summary(member, generation, summary)
        except Exception as error:
            failure = f"reset could not prepare generation {generation} for {member}: {error}"
            self._update_run(
                phase=InteractiveRunPhase.RECOVERY_REQUIRED,
                failure_reason=failure,
            )
            self.archive.append_event(
                self.record.run_id,
                "member-reset-summary-failed",
                data={"member": member, "generation": generation},
            )
            raise InteractiveControllerError(failure) from None
        try:
            session = await self._open_member(member, generation=generation, summary=summary)
        except Exception as error:
            failure = f"reset could not open generation {generation} for {member}: {error}"
            self._update_run(
                phase=InteractiveRunPhase.RECOVERY_REQUIRED,
                failure_reason=failure,
            )
            self.archive.append_event(
                self.record.run_id,
                "member-reset-open-failed",
                data={"member": member, "generation": generation},
            )
            raise InteractiveControllerError(
                f"reset closed the old generation but could not open generation "
                f"{generation} for {member}: {error}"
            ) from None
        current = next(item for item in self.record.members if item.name == member)
        replacement = current.model_copy(update={"session_id": session.session_id})
        members = [replacement if item.name == member else item for item in self.record.members]
        self._update_run(
            members=members,
            sessions=[item.session_id for item in members],
            phase=InteractiveRunPhase.OPEN,
            failure_reason=None,
        )
        self.archive.write_launch_record(
            member,
            self._launch_record_payload(
                self.launches[member],
                assistant_hash=replacement.assistant.content_hash,
                generation=generation,
            ),
        )
        self.archive.append_event(
            self.record.run_id,
            "member-reset",
            correlation_id=session.session_id,
            data={"member": member, "generation": generation},
        )
        return self.session_records[member]

    def run_state_summary(self, *, member: str, generation: int) -> str:
        payload = {
            "schema": "agentteam.run-state-summary.v1",
            "run_id": self.record.run_id,
            "member": member,
            "generation": generation,
            "goal": self.record.goal,
            "done_when": self.record.done_when,
            "workspace_checkpoint": checkpoint_workspace(
                Path(self.record.workspace), clock=self.clock
            ).model_dump(mode="json"),
            "work_items": [
                self.work_items[item_id].model_dump(mode="json")
                for item_id in self.record.work_items
            ],
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    async def detach(self) -> None:
        if self.active_turn is not None:
            await self.cancel_turn("controller detached")
        async with self._turn_lock:
            await self._detach_unlocked()

    async def _detach_unlocked(self) -> None:
        if self.record.phase in {
            InteractiveRunPhase.CLOSED,
            InteractiveRunPhase.CLOSING,
        }:
            self.lease.release()
            return
        prior_phase = self.record.phase
        suspension_failed = False
        for member, session in tuple(self.provider_sessions.items()):
            try:
                facts = await self.launches[member].provider.suspend_member(
                    session,
                    "controller detached or input ended",
                )
            except Exception:
                facts = ProviderSuspendFacts(
                    process=CleanupFact.FAILED,
                    local_state_retained=False,
                )
            terminal_process = facts.process in {
                CleanupFact.CONFIRMED,
                CleanupFact.NOT_APPLICABLE,
            }
            suspension_failed = (
                suspension_failed or not terminal_process or not facts.local_state_retained
            )
            self.archive.append_event(
                self.record.run_id,
                "member-suspended",
                correlation_id=session.session_id,
                data={
                    "member": member,
                    "generation": session.generation,
                    "process": facts.process.value,
                    "local-state-retained": facts.local_state_retained,
                },
            )
            self.provider_sessions.pop(member, None)
        phase: InteractiveRunPhase
        failure_reason: str | None
        if suspension_failed:
            phase = InteractiveRunPhase.RECOVERY_REQUIRED
            failure_reason = "provider suspension failed during detach"
        elif prior_phase in {
            InteractiveRunPhase.CLOSE_FAILED,
            InteractiveRunPhase.RECOVERY_REQUIRED,
        }:
            phase = prior_phase
            failure_reason = self.record.failure_reason
        else:
            phase = InteractiveRunPhase.INTERRUPTED
            failure_reason = "controller detached or input ended"
        self._update_run(phase=phase, failure_reason=failure_reason)
        self.archive.append_event(self.record.run_id, "run-interrupted")
        self.lease.release()

    async def close(
        self,
        outcome: InteractiveRunOutcome,
        *,
        reason: str,
    ) -> InteractiveRunRecordV1:
        if self.active_turn is not None:
            await self.cancel_turn("run closing")
        async with self._turn_lock:
            return await self._close_unlocked(outcome, reason=reason)

    async def _close_unlocked(
        self,
        outcome: InteractiveRunOutcome,
        *,
        reason: str,
    ) -> InteractiveRunRecordV1:
        if self.record.phase is InteractiveRunPhase.CLOSED:
            return self.record
        self._update_run(phase=InteractiveRunPhase.CLOSING, failure_reason=None)
        self.archive.append_event(
            self.record.run_id, "run-closing", data={"requested-outcome": outcome.value}
        )
        facts: list[CloseFactsV1] = []
        for member in [item.name for item in self.record.members]:
            session_record = self.session_records.get(member)
            if session_record is not None and session_record.status is SessionStatus.CLOSED:
                assert session_record.close is not None
                facts.append(session_record.close)
                continue
            session = self.provider_sessions.get(member)
            if session is None and session_record is not None:
                try:
                    session = await self._open_member(
                        member,
                        generation=session_record.generation,
                        summary=None,
                        resume_ref=session_record.provider_session_ref,
                    )
                except Exception:
                    session = None
            if session is None:
                close = CloseFactsV1(
                    logical_session=CleanupFact.UNKNOWN,
                    process=CleanupFact.UNKNOWN,
                    local_state=CleanupFact.UNKNOWN,
                    provider_history=CleanupFact.UNKNOWN,
                )
            else:
                try:
                    close = await self.launches[member].provider.close_member(session, reason)
                except Exception:
                    close = CloseFactsV1(
                        logical_session=CleanupFact.FAILED,
                        process=CleanupFact.UNKNOWN,
                        local_state=CleanupFact.UNKNOWN,
                        provider_history=CleanupFact.UNKNOWN,
                    )
                self.provider_sessions.pop(member, None)
            facts.append(close)
            if session_record is not None:
                status = (
                    SessionStatus.CLOSED
                    if _required_cleanup_terminal(close)
                    else SessionStatus.CLOSE_FAILED
                )
                updated = session_record.model_copy(
                    update={"status": status, "closed_at": self.clock(), "close": close}
                )
                self.session_records[member] = updated
                self.archive.write_session(updated)

        local_disposals: list[CleanupFact] = []
        seen: set[int] = set()
        for launch in self.launches.values():
            identity = id(launch.provider)
            if identity in seen:
                continue
            seen.add(identity)
            try:
                local_disposals.append(await launch.provider.dispose_run(self.record.run_id))
            except Exception:
                local_disposals.append(CleanupFact.FAILED)
        aggregate = _aggregate_close(facts, local_disposals)
        final_checkpoint = self._observe_final_workspace()
        self.archive.write_checkpoint("run", "final", final_checkpoint)
        if not _required_cleanup_terminal(aggregate):
            self._update_run(
                phase=InteractiveRunPhase.CLOSE_FAILED,
                cleanup=aggregate,
                final_checkpoint=final_checkpoint,
                failure_reason="required cleanup facts are not terminal",
            )
            self.archive.append_event(self.record.run_id, "run-close-failed")
            return self.record

        self._update_run(
            phase=InteractiveRunPhase.CLOSED,
            outcome=outcome,
            cleanup=aggregate,
            final_checkpoint=final_checkpoint,
            failure_reason=None,
        )
        self.archive.append_event(self.record.run_id, "run-closed", data={"outcome": outcome.value})
        try:
            self.archive.finalize_manifest()
        except Exception as error:
            aggregate = aggregate.model_copy(update={"local_state": CleanupFact.FAILED})
            self._update_run(
                phase=InteractiveRunPhase.CLOSE_FAILED,
                outcome=None,
                cleanup=aggregate,
                final_checkpoint=final_checkpoint,
                failure_reason=f"archive finalization failed: {error}",
            )
            self.archive.append_event(
                self.record.run_id,
                "run-close-failed",
                data={"stage": "manifest", "error": type(error).__name__},
            )
            return self.record

        try:
            self.reservation.release(Path(self.record.workspace), self.record.run_id)
        except Exception as error:
            aggregate = aggregate.model_copy(update={"local_state": CleanupFact.FAILED})
            self._update_run(
                phase=InteractiveRunPhase.CLOSE_FAILED,
                outcome=None,
                cleanup=aggregate,
                final_checkpoint=final_checkpoint,
                failure_reason=f"workspace reservation release failed: {error}",
            )
            self.archive.append_event(
                self.record.run_id,
                "run-close-failed",
                data={"stage": "reservation", "error": type(error).__name__},
            )
            try:
                self.archive.finalize_manifest()
            except Exception as manifest_error:
                self._update_run(
                    failure_reason=(
                        f"workspace reservation release failed: {error}; "
                        f"close-failure manifest update failed: {manifest_error}"
                    )
                )
            return self.record

        self.lease.release()
        return self.record

    def _observe_final_workspace(self) -> WorkspaceCheckpointV1:
        try:
            return checkpoint_workspace(Path(self.record.workspace), clock=self.clock)
        except Exception as error:
            self.archive.append_event(
                self.record.run_id,
                "workspace-observation-failed",
                data={"stage": "final", "error": type(error).__name__},
            )
            return self.last_checkpoint

    def _controls_from_event(
        self, event: ProviderEvent, *, member: str, turn_id: str
    ) -> list[ControlRequestV1]:
        raw = event.data.get("control_request")
        if raw is None:
            return []
        return self._validate_control_payload(raw, member=member, turn_id=turn_id)

    def _controls_from_text(
        self, text: str, *, member: str, turn_id: str
    ) -> list[ControlRequestV1]:
        controls: list[ControlRequestV1] = []
        for line in text.splitlines():
            if not line.startswith("{") or '"kind"' not in line:
                continue
            controls.extend(self._validate_control_payload(line, member=member, turn_id=turn_id))
        return controls

    def _validate_control_payload(
        self, raw: str, *, member: str, turn_id: str
    ) -> list[ControlRequestV1]:
        try:
            payload = json.loads(raw)
            if not isinstance(payload, dict) or payload.get("kind") != "control-request":
                return []
            request = ControlRequestV1.model_validate(payload)
        except (json.JSONDecodeError, ValueError):
            self.archive.append_event(
                self.record.run_id,
                "control-malformed",
                correlation_id=turn_id,
                data={"member": member},
            )
            return []
        if (
            request.run_id != self.record.run_id
            or request.source_turn_id != turn_id
            or request.actor_member != member
        ):
            self.archive.append_event(
                self.record.run_id,
                "control-identity-mismatch",
                correlation_id=turn_id,
                data={"member": member},
            )
            return []
        return [request]

    def _member_access(self, member: str, work_item_id: str | None) -> WorkspaceAccess:
        if work_item_id is not None:
            item = self.work_items.get(work_item_id)
            if item is None or item.owner != member:
                return WorkspaceAccess.READ_ONLY
            return item.workspace_access
        if any(
            item.owner == member
            and item.status not in _TERMINAL_WORK
            and item.workspace_access is WorkspaceAccess.WORKSPACE_WRITE
            for item in self.work_items.values()
        ):
            return WorkspaceAccess.WORKSPACE_WRITE
        return WorkspaceAccess.READ_ONLY

    def _updated_session(self, member: str, **updates: object) -> MemberSessionV1:
        session = self.session_records[member].model_copy(update=updates)
        self.session_records[member] = session
        return session

    def _update_run(self, **updates: object) -> None:
        updates["updated_at"] = self.clock()
        payload = self.record.model_dump(mode="python")
        payload.update(updates)
        self.record = InteractiveRunRecordV1.model_validate(payload)
        self.archive.write_run(self.record)


def _initial_work_items(
    run_id: str, request: InteractiveRunRequestV1, team: TeamTemplateV2
) -> dict[str, WorkItemV1]:
    items: dict[str, WorkItemV1] = {}
    for task in team.workflow_skeleton:
        items[task.id] = WorkItemV1(
            schema_version=1,
            kind="work-item",
            run_id=run_id,
            id=task.id,
            subject=task.subject.replace("{goal}", request.goal),
            owner=task.owner,
            status=TeamTaskStatus.BLOCKED if task.blocked_by else TeamTaskStatus.PENDING,
            blocked_by=task.blocked_by,
            workspace_access=task.workspace_access,
        )
    _validate_work_graph(items)
    return items


def _validate_work_graph(items: Mapping[str, WorkItemV1]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(item_id: str) -> None:
        if item_id in visiting:
            raise InteractiveControllerError("work-item graph must be acyclic")
        if item_id in visited:
            return
        visiting.add(item_id)
        for blocker in items[item_id].blocked_by:
            if blocker not in items:
                raise InteractiveControllerError(f"unknown work-item blocker: {blocker}")
            visit(blocker)
        visiting.remove(item_id)
        visited.add(item_id)

    for item_id in items:
        visit(item_id)


def _system_prompt(
    package: LoadedPackage,
    *,
    team: TeamTemplateV2,
    member: str,
    goal: str,
    done_when: list[str],
    summary: str | None,
) -> str:
    definition = package.definition
    parts = [
        "# AgentTeam portable Assistant",
        f"Assistant: {definition.id}@{definition.version}",
        f"Summary: {definition.summary}",
    ]
    for label, relative in (
        ("Persona", definition.persona),
        ("Principles", definition.principles),
        ("Methods", definition.methods),
    ):
        if relative is None:
            continue
        path = package.root / relative
        parts.extend((f"## {label}", path.read_text(encoding="utf-8").strip()))
    for artifact in definition.artifacts:
        if artifact.kind is not ArtifactKind.AGENT_SKILL:
            continue
        skill = package.root / artifact.source.vendored / "SKILL.md"
        if skill.is_file():
            level = "required" if artifact.level is RequirementLevel.REQUIRED else "optional"
            parts.extend(
                (
                    f"## Portable Skill {artifact.ref} ({level})",
                    skill.read_text(encoding="utf-8").strip(),
                )
            )
    member_record = next(item for item in team.members if item.name == member)
    parts.extend(
        (
            "# Bounded interactive run",
            f"Member: {member}",
            f"Lead: {team.lead}",
            f"Relationships: {json.dumps(member_record.relationships, sort_keys=True)}",
            f"Goal: {goal}",
            "Done when:\n" + "\n".join(f"- {item}" for item in done_when),
            "All Members share the supplied workspace and turns are serialized by AgentTeam.",
            "Do not create hidden workers or claim run completion. The Lead may only propose "
            "completion; the user accepts it.",
        )
    )
    if summary is not None:
        parts.extend(("# Deterministic RunStateSummary after reset", summary))
    return "\n\n".join(parts).strip() + "\n"


def _session_id(member: str, generation: int) -> str:
    return _bounded_slug(f"session-{member}-g", generation)


def _bounded_slug(prefix: str, sequence: int) -> str:
    candidate = f"{prefix}-{sequence}"
    if len(candidate) <= 64:
        return candidate
    digest = hashlib.sha256(candidate.encode("utf-8")).hexdigest()[:12]
    return f"{prefix[:48].rstrip('-')}-{digest}"


def _required_cleanup_terminal(facts: CloseFactsV1) -> bool:
    return all(
        value in {CleanupFact.CONFIRMED, CleanupFact.NOT_APPLICABLE}
        for value in (facts.logical_session, facts.process, facts.local_state)
    )


def _aggregate_close(facts: list[CloseFactsV1], local_disposals: list[CleanupFact]) -> CloseFactsV1:
    def combine(values: list[CleanupFact], *, optional: bool = False) -> CleanupFact:
        if not values:
            return CleanupFact.NOT_APPLICABLE
        if CleanupFact.FAILED in values:
            return CleanupFact.FAILED
        if CleanupFact.UNKNOWN in values:
            return CleanupFact.UNKNOWN
        if CleanupFact.UNSUPPORTED in values:
            return CleanupFact.UNSUPPORTED
        if all(value is CleanupFact.NOT_APPLICABLE for value in values):
            return CleanupFact.NOT_APPLICABLE
        if all(value in {CleanupFact.CONFIRMED, CleanupFact.NOT_APPLICABLE} for value in values):
            return CleanupFact.CONFIRMED
        return CleanupFact.UNKNOWN if optional else CleanupFact.FAILED

    local_state = (
        CleanupFact.CONFIRMED
        if local_disposals and all(item is CleanupFact.CONFIRMED for item in local_disposals)
        else combine([item.local_state for item in facts] + local_disposals)
    )
    return CloseFactsV1(
        logical_session=combine([item.logical_session for item in facts]),
        process=combine([item.process for item in facts]),
        local_state=local_state,
        provider_history=combine([item.provider_history for item in facts], optional=True),
    )


def _partition_controls(
    requests: list[ControlRequestV1],
) -> tuple[list[ControlRequestV1], list[ControlRequestV1]]:
    observed: dict[str, ControlRequestV1] = {}
    conflicts: set[str] = set()
    for request in requests:
        previous = observed.get(request.request_id)
        if previous is not None and previous != request:
            conflicts.add(request.request_id)
        else:
            observed[request.request_id] = request
    return (
        [request for key, request in observed.items() if key not in conflicts],
        [request for key, request in observed.items() if key in conflicts],
    )
