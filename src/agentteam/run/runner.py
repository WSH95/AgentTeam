"""The direct ensemble state machine (plan section 12, steps 4-12).

Preflight already validated and resolved everything (steps 1-3). Here: the
pending archive exists before any harness side effect; every leg gets an
isolated workspace copy whose hash is re-verified; all renders happen before
any launch; legs run concurrently; a failed attempt is retried once, same
harness, transient causes only; synthesis sees only the labelled leg reports;
finalization evaluates the acceptance tiers, re-hashes the package, writes the
manifest, and returns the stable exit code (0/1/2/3; 130 via cancellation).
"""

from __future__ import annotations

import asyncio
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from agentteam.domain.bundle import AssistantRefV1, BundleManifestV1
from agentteam.domain.common import RunStatus
from agentteam.domain.review import NormalizedReviewV1, SynthesisReportV1
from agentteam.domain.run import (
    AcceptanceV1,
    Attendance,
    AttributionV1,
    EnsembleRecordV1,
    ExecutionBindingV1,
    ExecutionKind,
    ExitV1,
    HarnessInvocationV1,
    InvocationAuthMode,
    MemberRecordV1,
    ObservedV1,
    RetryClassification,
    RetryV1,
    RunRecordV1,
    SchemaOutcome,
    SynthesisLinkV1,
    TargetHashesV1,
    TimingV1,
    UsageV1,
)
from agentteam.harness import get_adapter
from agentteam.harness.capabilities import CLAUDE_SKILL_LADDER, select_verified
from agentteam.harness.environment import EnvironmentConflictError
from agentteam.harness.process import classify_failure
from agentteam.harness.protocol import HarnessAdapter, StructuredExtractor
from agentteam.harness.rendering import RenderError
from agentteam.harness.skills import ManagedSkillsLease
from agentteam.harness.types import (
    RawInvocationV1,
    RenderContext,
    RenderedInvocationV1,
    SynthesisRenderV1,
)
from agentteam.resolution.archive import build_bundle_manifest, hash_package
from agentteam.run.acceptance import (
    MechanicalInputs,
    SemanticInputs,
    evaluate_mechanical,
    evaluate_semantic,
    load_oracle,
)
from agentteam.run.archive import RunArchive
from agentteam.run.events import EventLog
from agentteam.run.ids import ENSEMBLE_ID, SYNTHESIS_INVOCATION_ID, leg_invocation_id, new_run_id
from agentteam.run.preflight import LegPlan, PreflightError, ResolvedRun
from agentteam.run.synthesis import (
    INSTRUCTIONS_FILE,
    SynthesisValidationError,
    build_synthesis_task,
    instruction_hash,
    validate_synthesis,
)
from agentteam.run.workspace import TargetError, copy_workspace, exclusions_for, hash_tree


@dataclass(frozen=True)
class RunOutcome:
    exit_code: int
    run_id: str
    archive_root: Path
    summary: dict[str, Any]
    human: str


def default_archive_root(environ: Mapping[str, str]) -> Path:
    home = environ.get("AGENTTEAM_HOME")
    base = Path(home) if home else Path.home() / ".agentteam"
    return base / "runs"


def finalize_cancelled(
    archive: RunArchive,
    *,
    run_record: RunRecordV1,
    invocations: list[HarnessInvocationV1],
    events: EventLog,
) -> None:
    """Synchronous cancellation finalizer: every started record reaches a terminal state."""
    now = datetime.now(tz=UTC)
    from agentteam.domain.common import TERMINAL_STATUSES

    for record in invocations:
        if record.status in TERMINAL_STATUSES:
            continue
        archive.write_invocation(
            record.model_copy(
                update={
                    "status": RunStatus.CANCELLED,
                    "timing": record.timing.model_copy(update={"finished_at": now}),
                }
            )
        )
    if run_record.status not in TERMINAL_STATUSES:
        archive.write_run_record(
            run_record.model_copy(
                update={
                    "status": RunStatus.CANCELLED,
                    "failure_reason": "cancelled by the owner",
                    "timing": run_record.timing.model_copy(update={"finished_at": now}),
                }
            )
        )
    events.emit("run-cancelled")
    archive.finalize_manifest()


@dataclass
class _LegOutcome:
    plan: LegPlan
    invocation_id: str
    record: HarnessInvocationV1
    review: NormalizedReviewV1 | None


class _Runner:
    def __init__(
        self,
        resolved: ResolvedRun,
        *,
        environ: Mapping[str, str],
        platform: str,
        home: Path | None,
    ) -> None:
        self.resolved = resolved
        self.environ = dict(environ)
        self.platform = platform
        self.home = home
        self.run_id = new_run_id()
        self.ensemble_mode = len(resolved.legs) > 1 or resolved.synthesis_planned
        self.archive: RunArchive
        self.events: EventLog
        self.bundle: BundleManifestV1
        self.run_record: RunRecordV1
        self.records: dict[str, HarnessInvocationV1] = {}
        self.redaction_problems: list[str] = []

    # -- setup ---------------------------------------------------------------

    def _assistant_ref(self) -> AssistantRefV1:
        definition = self.resolved.package.definition
        return AssistantRefV1(
            id=definition.id,
            version=definition.version,
            package_hash=self.resolved.digest.package_hash,
        )

    def create_archive(self) -> None:
        request = self.resolved.request
        root = (
            Path(request.output_dir)
            if request.output_dir is not None
            else default_archive_root(self.environ) / self.run_id
        )
        now = datetime.now(tz=UTC)
        self.bundle = build_bundle_manifest(
            assistant=self._assistant_ref(),
            digest=self.resolved.digest,
            created_at=now,
        )
        binding = (
            ExecutionBindingV1(kind=ExecutionKind.ENSEMBLE, ref=ENSEMBLE_ID)
            if self.ensemble_mode
            else ExecutionBindingV1(
                kind=ExecutionKind.INVOCATION,
                ref=leg_invocation_id(self.resolved.legs[0].harness),
            )
        )
        self.run_record = RunRecordV1(
            schema_version=1,
            kind="run-record",
            run_id=self.run_id,
            mode="direct",
            member=MemberRecordV1(
                name=self.resolved.package.definition.id,
                assistant=self._assistant_ref(),
                effective_definition_hash=self.bundle.effective_definition_hash,
                execution=binding,
            ),
            timing=TimingV1(started_at=now),
            status=RunStatus.PENDING,
        )
        try:
            self.archive, warnings = RunArchive.create(
                root,
                run_record=self.run_record,
                resolved_request=request,
                bundle=self.bundle,
                retain_raw_streams=request.evidence.retain_raw_streams,
                platform=self.platform,
                home=self.home,
            )
        except ValueError as error:
            raise PreflightError(str(error)) from None
        self.events = EventLog(self.archive.events_path, run_id=self.run_id)
        self.events.emit("run-created")
        for _ in warnings:
            self.events.emit("archive-warning", detail="archive root outside the user profile")

    # -- rendering -----------------------------------------------------------

    def _render_context(
        self,
        plan: LegPlan,
        invocation_id: str,
        *,
        workspace: Path,
        config_root: Path,
        scratch: Path,
        task_file: Path,
        synthesis: SynthesisRenderV1 | None,
    ) -> RenderContext:
        return RenderContext(
            profile=plan.profile,
            definition=self.resolved.package.definition,
            package_root=self.resolved.package.root,
            bundle=self.bundle,
            selection=self.resolved.selection.selection,
            requested=plan.requested,
            task_file=task_file,
            workspace=workspace,
            workspace_root=workspace,
            config_root=config_root,
            scratch_dir=scratch,
            parent_env=self.environ,
            platform=self.platform,
            run_id=self.run_id,
            invocation_id=invocation_id,
            timeout_seconds=min(
                self.resolved.timeout_seconds, plan.profile.timeouts.attempt_seconds
            ),
            cli_version=plan.cli_version,
            profile_file=self.resolved.profile_path,
            synthesis=synthesis,
        )

    def _pending_record(
        self,
        plan: LegPlan,
        invocation_id: str,
        rendered: RenderedInvocationV1,
        before: str,
    ) -> HarnessInvocationV1:
        record = HarnessInvocationV1(
            schema_version=1,
            kind="harness-invocation",
            invocation_id=invocation_id,
            run_id=self.run_id,
            ensemble_id=ENSEMBLE_ID if self.ensemble_mode else None,
            requested=plan.requested,
            selection=self.resolved.selection.selection,
            effective_definition_hash=self.bundle.effective_definition_hash,
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
        self.records[invocation_id] = record
        self.archive.write_invocation(record)
        return record

    def _write_rendered(self, invocation_id: str, rendered: RenderedInvocationV1) -> None:
        self.archive.write_rendered(invocation_id, rendered)
        text = (self.archive.leg_dir(invocation_id) / "invocation.render.json").read_text(
            encoding="utf-8"
        )
        if '"env_values"' in text:
            self.redaction_problems.append(
                f"{invocation_id} rendered record serialised environment values"
            )

    # -- execution -----------------------------------------------------------

    async def _attempt_loop(
        self, adapter: HarnessAdapter, invocation_id: str, rendered: RenderedInvocationV1
    ) -> tuple[RawInvocationV1, int, RetryClassification]:
        attempt = 1
        max_attempts = 1 + self.resolved.transient_retries
        retried_for = RetryClassification.NONE
        while True:
            self.events.emit(
                "leg-started", invocation_id=invocation_id, detail=f"attempt {attempt}"
            )
            raw = await adapter.invoke(rendered)
            if raw.exit_code == 0 and not raw.timed_out:
                # a successful second attempt keeps the classification that caused it
                return raw, attempt, retried_for
            classification = classify_failure(raw)
            if classification is RetryClassification.TRANSIENT and attempt < max_attempts:
                retried_for = classification
                attempt += 1
                self.events.emit("leg-retry", invocation_id=invocation_id, detail="transient")
                continue
            return raw, attempt, classification

    async def _execute_leg(
        self,
        plan: LegPlan,
        invocation_id: str,
        rendered: RenderedInvocationV1,
        record: HarnessInvocationV1,
        workspace_dir: Path,
    ) -> _LegOutcome:
        adapter = get_adapter(plan.harness)
        raw, attempt, classification = await self._attempt_loop(adapter, invocation_id, rendered)
        refs = self.archive.write_raw_streams(invocation_id, raw)
        review: NormalizedReviewV1 | None = None
        schema_outcome = SchemaOutcome.NOT_REQUESTED
        usage = UsageV1()
        observed = ObservedV1()
        problems: list[str] = []
        if raw.exit_code == 0 and not raw.timed_out:
            parsed = adapter.parse(raw)
            review = parsed.review
            schema_outcome = parsed.schema_outcome
            usage = parsed.usage
            observed = parsed.observed
            problems = parsed.problems
            if review is not None:
                refs.append(self.archive.write_review(invocation_id, review))
            status = (
                RunStatus.SUCCEEDED
                if review is not None and schema_outcome is SchemaOutcome.VALID
                else RunStatus.FAILED
            )
        elif raw.timed_out:
            status = RunStatus.TIMED_OUT
        else:
            status = RunStatus.FAILED
        after = hash_tree(
            workspace_dir, exclude=exclusions_for(rendered.files_written, workspace_dir)
        )
        finished = raw.finished_at or datetime.now(tz=UTC)
        started = record.timing.started_at
        final = record.model_copy(
            update={
                "observed": observed,
                "usage": usage,
                "target": record.target.model_copy(update={"after": after}),
                "retry": RetryV1(
                    classification=classification,
                    attempt=attempt,
                    max_attempts=1 + self.resolved.transient_retries,
                ),
                "exit": ExitV1(code=raw.exit_code, signal=raw.signal),
                "schema_outcome": schema_outcome,
                "problems": problems,
                "artifacts": refs,
                "timing": TimingV1(
                    started_at=started,
                    finished_at=finished,
                    duration_ms=max(0, int((finished - started).total_seconds() * 1000)),
                ),
                "status": status,
            }
        )
        self.records[invocation_id] = final
        self.archive.write_invocation(final)
        self.events.emit("leg-finished", invocation_id=invocation_id, detail=status.value)
        return _LegOutcome(plan=plan, invocation_id=invocation_id, record=final, review=review)

    # -- finalization --------------------------------------------------------

    def _artifact_problems(self) -> list[str]:
        problems: list[str] = []
        for record in self.records.values():
            for ref in record.artifacts:
                path = self.archive.root / ref.path
                if not path.is_file():
                    problems.append(f"artifact missing: {ref.path}")
                elif sha256(path.read_bytes()).hexdigest() != ref.sha256:
                    problems.append(f"artifact changed: {ref.path}")
        return problems

    def _finalize_run(
        self, *, status: RunStatus, exit_code: int, failure_reason: str | None
    ) -> RunOutcome:
        now = datetime.now(tz=UTC)
        record = self.run_record.model_copy(
            update={
                "status": status,
                "failure_reason": failure_reason,
                "timing": self.run_record.timing.model_copy(
                    update={
                        "finished_at": now,
                        "duration_ms": max(
                            0,
                            int((now - self.run_record.timing.started_at).total_seconds() * 1000),
                        ),
                    }
                ),
            }
        )
        self.run_record = record
        self.archive.write_run_record(record)
        self.events.emit("run-finished", detail=f"exit {exit_code}")
        self.archive.finalize_manifest()
        leg_statuses = {
            invocation_id: rec.status.value for invocation_id, rec in self.records.items()
        }
        summary = {
            "run_id": self.run_id,
            "status": status.value,
            "exit_code": exit_code,
            "archive": str(self.archive.root),
            "decided_by": self.resolved.selection.selection.decided_by.value,
            "legs": leg_statuses,
            "failure_reason": failure_reason,
        }
        human = f"run {self.run_id} {status.value} (exit {exit_code}); archive: {self.archive.root}"
        if failure_reason:
            human += f"; reason: {failure_reason}"
        return RunOutcome(
            exit_code=exit_code,
            run_id=self.run_id,
            archive_root=self.archive.root,
            summary=summary,
            human=human,
        )


async def execute_run(
    resolved: ResolvedRun,
    *,
    environ: Mapping[str, str],
    platform: str = sys.platform,
    home: Path | None = None,
) -> RunOutcome:
    if not resolved.live_ready:
        raise PreflightError(
            "execute_run requires live readiness checks; call preflight(..., live=True)"
        )
    guarded_plans = [*resolved.legs]
    if resolved.synthesis_leg is not None:
        guarded_plans.append(resolved.synthesis_leg)
    if any(plan.cli_version is None for plan in guarded_plans):
        raise PreflightError("execute_run requires observed CLI versions from live preflight")
    runner = _Runner(resolved, environ=environ, platform=platform, home=home)
    runner.create_archive()
    try:
        return await _run_body(runner)
    except asyncio.CancelledError:
        finalize_cancelled(
            runner.archive,
            run_record=runner.run_record,
            invocations=list(runner.records.values()),
            events=runner.events,
        )
        raise


async def _run_body(runner: _Runner) -> RunOutcome:
    resolved = runner.resolved
    request = resolved.request

    # step 5: one isolated workspace copy per leg, hashes verified
    try:
        source_hash = hash_tree(Path(request.workspace))
    except TargetError as error:
        return runner._finalize_run(status=RunStatus.FAILED, exit_code=2, failure_reason=str(error))

    prepared: list[tuple[LegPlan, str, RenderedInvocationV1, HarnessInvocationV1, Path]] = []
    skill_leases: list[ManagedSkillsLease] = []
    try:
        try:
            for plan in resolved.legs:
                invocation_id = leg_invocation_id(plan.harness)
                workspace_dir, _synthetic_config_home, scratch = runner.archive.working_dirs(
                    invocation_id
                )
                copy_workspace(Path(request.workspace), workspace_dir)
                if hash_tree(workspace_dir) != source_hash:
                    return runner._finalize_run(
                        status=RunStatus.FAILED,
                        exit_code=1,
                        failure_reason=(
                            f"workspace copy for {invocation_id} does not match the source"
                        ),
                    )
                if (
                    plan.harness.value == "claude-code"
                    and select_verified(
                        plan.profile,
                        CLAUDE_SKILL_LADDER,
                        cli_version=plan.cli_version,
                    )
                    == "skills-config-home"
                ):
                    lease = ManagedSkillsLease(
                        Path(plan.profile.config_home), platform=runner.platform
                    ).acquire()
                    skill_leases.append(lease)
                context = runner._render_context(
                    plan,
                    invocation_id,
                    workspace=workspace_dir,
                    config_root=Path(plan.profile.config_home),
                    scratch=scratch,
                    task_file=Path(request.task_file),
                    synthesis=None,
                )
                rendered = get_adapter(plan.harness).render(context)  # step 6, before any launch
                runner._write_rendered(invocation_id, rendered)
                record = runner._pending_record(plan, invocation_id, rendered, source_hash)
                prepared.append((plan, invocation_id, rendered, record, workspace_dir))
        except (RenderError, EnvironmentConflictError, TargetError) as error:
            return runner._finalize_run(
                status=RunStatus.FAILED, exit_code=2, failure_reason=str(error)
            )

        # step 7: all requested legs, concurrently, fresh sessions
        leg_outcomes = list(
            await asyncio.gather(
                *(
                    runner._execute_leg(plan, invocation_id, rendered, record, workspace_dir)
                    for plan, invocation_id, rendered, record, workspace_dir in prepared
                )
            )
        )
    finally:
        for lease in reversed(skill_leases):
            lease.close()
    legs_ok = all(outcome.record.status is RunStatus.SUCCEEDED for outcome in leg_outcomes)
    failed_legs = [
        outcome.invocation_id
        for outcome in leg_outcomes
        if outcome.record.status is not RunStatus.SUCCEEDED
    ]

    # steps 10-11: synthesis over the labelled reports only
    synthesis_record: HarnessInvocationV1 | None = None
    synthesis_report: SynthesisReportV1 | None = None
    attribution: list[AttributionV1] = []
    attribution_valid: bool | None = None
    synthesis_failure: str | None = None
    if resolved.synthesis_planned and legs_ok and resolved.synthesis_leg is not None:
        (
            synthesis_record,
            synthesis_report,
            attribution,
            attribution_valid,
            synthesis_failure,
        ) = await _run_synthesis(runner, leg_outcomes)

    # step 12: validation, acceptance, re-hash, finalize, stable exit code
    package_rehash = hash_package(resolved.package.root).package_hash
    mechanical = None
    semantic = None
    if runner.ensemble_mode:
        mechanical = evaluate_mechanical(
            MechanicalInputs(
                legs=[outcome.record for outcome in leg_outcomes],
                bundle_hash=runner.bundle.effective_definition_hash,
                package_rehash=package_rehash,
                manifest_problems=runner._artifact_problems(),
                redaction_problems=runner.redaction_problems,
            )
        )
        reviews = {
            outcome.invocation_id: outcome.review
            for outcome in leg_outcomes
            if outcome.review is not None
        }
        if len(reviews) == len(leg_outcomes):
            semantic = evaluate_semantic(
                SemanticInputs(
                    oracle=(
                        load_oracle(resolved.oracle_path)
                        if resolved.oracle_path is not None
                        else None
                    ),
                    leg_reviews=reviews,
                    synthesis_report=synthesis_report,
                    attribution_valid=attribution_valid,
                )
            )
        else:
            semantic = evaluate_semantic(
                SemanticInputs(
                    oracle=None, leg_reviews={}, synthesis_report=None, attribution_valid=None
                )
            )
        synthesis_ok = (not resolved.synthesis_planned) or (
            synthesis_record is not None
            and synthesis_record.status is RunStatus.SUCCEEDED
            and synthesis_failure is None
        )
        ensemble_status = RunStatus.SUCCEEDED if legs_ok and synthesis_ok else RunStatus.FAILED
        runner.archive.write_ensemble(
            EnsembleRecordV1(
                schema_version=1,
                kind="ensemble-record",
                ensemble_id=ENSEMBLE_ID,
                run_id=runner.run_id,
                legs=[outcome.invocation_id for outcome in leg_outcomes],
                synthesis=SynthesisLinkV1(
                    invocation_id=(
                        synthesis_record.invocation_id if synthesis_record is not None else None
                    ),
                    inputs=(
                        [outcome.invocation_id for outcome in leg_outcomes]
                        if synthesis_record is not None
                        else []
                    ),
                    instruction_hash=instruction_hash(),
                ),
                attribution=attribution,
                status=ensemble_status,
                acceptance=AcceptanceV1(mechanical=mechanical, semantic=semantic),
            )
        )

    if not legs_ok:
        return runner._finalize_run(
            status=RunStatus.FAILED,
            exit_code=1,
            failure_reason="failed legs: " + ", ".join(failed_legs),
        )
    if synthesis_failure is not None or (
        resolved.synthesis_planned
        and (synthesis_record is None or synthesis_record.status is not RunStatus.SUCCEEDED)
    ):
        return runner._finalize_run(
            status=RunStatus.FAILED,
            exit_code=1,
            failure_reason=synthesis_failure or "synthesis invocation failed",
        )
    if mechanical is not None and mechanical.passed is False:
        details = "; ".join(
            condition.detail or condition.id
            for condition in mechanical.conditions
            if condition.passed is False
        )
        return runner._finalize_run(
            status=RunStatus.FAILED, exit_code=1, failure_reason=f"mechanical: {details}"
        )
    if semantic is not None and semantic.passed is False:
        return runner._finalize_run(status=RunStatus.SUCCEEDED, exit_code=3, failure_reason=None)
    return runner._finalize_run(status=RunStatus.SUCCEEDED, exit_code=0, failure_reason=None)


async def _run_synthesis(
    runner: _Runner, leg_outcomes: list[_LegOutcome]
) -> tuple[
    HarnessInvocationV1 | None,
    SynthesisReportV1 | None,
    list[AttributionV1],
    bool | None,
    str | None,
]:
    resolved = runner.resolved
    plan = resolved.synthesis_leg
    assert plan is not None
    invocation_id = SYNTHESIS_INVOCATION_ID
    document = build_synthesis_task(
        [
            (outcome.invocation_id, outcome.plan.harness.value, outcome.review)
            for outcome in leg_outcomes
            if outcome.review is not None
        ]
    )
    task_ref = runner.archive.write_leg_text(invocation_id, "task.md", document, role="task")
    workspace_dir, _synthetic_config_home, scratch = runner.archive.working_dirs(invocation_id)
    before = hash_tree(workspace_dir)
    context = runner._render_context(
        plan,
        invocation_id,
        workspace=workspace_dir,
        config_root=Path(plan.profile.config_home),
        scratch=scratch,
        task_file=runner.archive.leg_dir(invocation_id) / "task.md",
        synthesis=SynthesisRenderV1(instructions_file=INSTRUCTIONS_FILE),
    )
    adapter = get_adapter(plan.harness)
    try:
        rendered = adapter.render(context)
    except (RenderError, EnvironmentConflictError) as error:
        return None, None, [], None, f"synthesis render failed: {error}"
    runner._write_rendered(invocation_id, rendered)
    record = runner._pending_record(plan, invocation_id, rendered, before)
    raw, attempt, classification = await runner._attempt_loop(adapter, invocation_id, rendered)
    refs = runner.archive.write_raw_streams(invocation_id, raw)
    refs.append(task_ref)

    report: SynthesisReportV1 | None = None
    attribution: list[AttributionV1] = []
    attribution_valid: bool | None = None
    failure: str | None = None
    schema_outcome = SchemaOutcome.NOT_REQUESTED
    usage = UsageV1()
    observed = ObservedV1()
    problems: list[str] = []
    if raw.exit_code == 0 and not raw.timed_out:
        assert isinstance(adapter, StructuredExtractor)
        extracted = adapter.extract_structured(raw)
        usage = extracted.usage
        observed = extracted.observed
        problems = extracted.problems
        try:
            report = SynthesisReportV1.model_validate(extracted.candidate)
            schema_outcome = SchemaOutcome.VALID
        except ValidationError as error:
            schema_outcome = (
                SchemaOutcome.MISSING if extracted.candidate is None else SchemaOutcome.INVALID
            )
            failure = f"synthesis output failed validation: {error.error_count()} error(s)"
        if report is not None:
            reviews = {
                outcome.invocation_id: outcome.review
                for outcome in leg_outcomes
                if outcome.review is not None
            }
            try:
                attribution = validate_synthesis(report, reviews)
                attribution_valid = True
            except SynthesisValidationError as error:
                attribution_valid = False
                failure = f"synthesis attribution invalid: {error}"
            runner.archive.write_synthesis_report(report)
        status = RunStatus.SUCCEEDED if failure is None else RunStatus.FAILED
    elif raw.timed_out:
        status = RunStatus.TIMED_OUT
        failure = "synthesis timed out"
    else:
        status = RunStatus.FAILED
        failure = "synthesis invocation failed"

    after = hash_tree(workspace_dir, exclude=exclusions_for(rendered.files_written, workspace_dir))
    finished = raw.finished_at or datetime.now(tz=UTC)
    final = record.model_copy(
        update={
            "observed": observed,
            "usage": usage,
            "target": record.target.model_copy(update={"after": after}),
            "retry": RetryV1(
                classification=classification,
                attempt=attempt,
                max_attempts=1 + resolved.transient_retries,
            ),
            "exit": ExitV1(code=raw.exit_code, signal=raw.signal),
            "schema_outcome": schema_outcome,
            "problems": problems,
            "artifacts": refs,
            "timing": TimingV1(
                started_at=record.timing.started_at,
                finished_at=finished,
                duration_ms=max(
                    0, int((finished - record.timing.started_at).total_seconds() * 1000)
                ),
            ),
            "status": status,
        }
    )
    runner.records[invocation_id] = final
    runner.archive.write_invocation(final)
    runner.events.emit("leg-finished", invocation_id=invocation_id, detail=status.value)
    return final, report, attribution, attribution_valid, failure
