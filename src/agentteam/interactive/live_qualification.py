"""Attended, bounded live lifecycle qualification for one exact direct-ACP target."""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
import os
import secrets
import shutil
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from agentteam.domain.interactive import (
    AssistantCatalogRefV1,
    CapabilityLevel,
    CatalogKind,
    CatalogRefV1,
    DynamicMemberPolicyDisabledV1,
    InteractiveRunOutcome,
    InteractiveRunPhase,
    InteractiveRunRequestV1,
    LiveEvidenceRefV1,
    LiveLifecycleProofsV1,
    ProviderDoctorV1,
    ProviderLiveAttestationV1,
    SessionStatus,
    TeamMemberV2,
    TeamPreferencesV2,
    TeamTemplateV2,
    WorkspaceLayout,
)
from agentteam.domain.team import HandoffRulesV1
from agentteam.execution.direct_acp import (
    RUNTIME_ID,
    DirectAcpError,
    DirectAcpProvider,
    DirectAcpQualificationTarget,
    default_runtime_base,
    runtime_lock_hash,
    write_direct_acp_live_attestation,
)
from agentteam.execution.protocol import MemberExecutionProvider, ProviderEvent
from agentteam.interactive.archive import InteractiveArchive
from agentteam.interactive.controller import (
    InteractiveController,
    MemberLaunch,
)
from agentteam.interactive.resolution import default_interactive_roots
from agentteam.resolution.archive import hash_package
from agentteam.resolution.package import LoadedPackage, load_package
from agentteam.resolution.profiles import atomic_write_text, ensure_owner_directory

MAX_LIVE_PROMPTS = 5
_MEMBER = "verifier"


@dataclass(frozen=True)
class DirectAcpLiveQualificationResult:
    attestation: ProviderLiveAttestationV1
    path: Path
    detail: str | None = None
    interrupted: bool = False


class _LiveQualificationFailure(RuntimeError):
    pass


def _proofs(values: Mapping[str, bool]) -> LiveLifecycleProofsV1:
    return LiveLifecycleProofsV1(
        context_established=values["context_established"],
        strict_post_turn_resume=values["strict_post_turn_resume"],
        recall=values["recall"],
        reset_isolation=values["reset_isolation"],
        new_run_isolation=values["new_run_isolation"],
        continuity_close=values["continuity_close"],
    )


def _qualification_package(root: Path, *, platform: str) -> LoadedPackage:
    ensure_owner_directory(root, platform=platform)
    definition = {
        "schema_version": 1,
        "kind": "assistant-definition",
        "id": "direct-acp-lifecycle-verifier",
        "version": 1,
        "summary": "Executes a bounded, exact-response lifecycle qualification.",
        "persona": "persona.md",
        "purpose": ["respond exactly to each numbered lifecycle probe"],
        "principles": "principles.md",
        "permissions": {
            "filesystem": "read-only",
            "network": "deny",
            "shell": "deny",
        },
    }
    atomic_write_text(
        root / "assistant.json",
        json.dumps(definition, indent=2, sort_keys=True) + "\n",
        platform=platform,
    )
    atomic_write_text(
        root / "persona.md",
        "You are a lifecycle verifier. Follow each probe's exact response format. "
        "Do not use tools, markdown, explanations, or extra punctuation.\n",
        platform=platform,
    )
    atomic_write_text(
        root / "principles.md",
        "Retain a probe nonce only through the current conversation. Never infer a "
        "nonce that is absent from the current conversation.\n",
        platform=platform,
    )
    return load_package(root)


def _qualification_team(
    package: LoadedPackage,
) -> tuple[TeamTemplateV2, bytes, CatalogRefV1]:
    package_hash = hash_package(package.root).package_hash
    assistant = AssistantCatalogRefV1(
        id=package.definition.id,
        version=package.definition.version,
        content_hash=package_hash,
    )
    team = TeamTemplateV2(
        schema_version=2,
        kind="team-template",
        id="direct-acp-live-qualification",
        version=1,
        summary="One-member attended direct-ACP lifecycle qualification.",
        members=[TeamMemberV2(name=_MEMBER, assistant=assistant)],
        lead=_MEMBER,
        handoff=HandoffRulesV1(required_fields=[], acks=[]),
        independence=[],
        preferences=TeamPreferencesV2(),
        workflow_skeleton=[],
        workspace_layout=WorkspaceLayout.SHARED_SUPPLIED,
        dynamic_members=DynamicMemberPolicyDisabledV1(),
    )
    source = (json.dumps(team.model_dump(mode="json"), indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    target = CatalogRefV1(
        kind=CatalogKind.ASSISTANT,
        id=assistant.id,
        version=assistant.version,
        content_hash=assistant.content_hash,
    )
    return team, source, target


def _manifest_evidence(controller: InteractiveController) -> LiveEvidenceRefV1 | None:
    if controller.record.phase is not InteractiveRunPhase.CLOSED:
        return None
    if controller.archive.verify_manifest():
        return None
    manifest = controller.archive.root / "manifest.sha256.json"
    if manifest.is_symlink() or not manifest.is_file():
        return None
    return LiveEvidenceRefV1(
        run_id=controller.record.run_id,
        manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
    )


def _attestation(
    target: DirectAcpQualificationTarget,
    *,
    platform: str,
    status: Literal["pass", "fail"],
    attempted_prompts: int,
    proof_values: Mapping[str, bool],
    evidence: list[LiveEvidenceRefV1],
    checked_at: datetime,
) -> ProviderLiveAttestationV1:
    return ProviderLiveAttestationV1(
        schema_version=1,
        kind="provider-live-attestation",
        provider=RUNTIME_ID,
        harness=target.harness,
        target_fingerprint=target.fingerprint,
        runtime_lock_hash=runtime_lock_hash(),
        native_version=target.native_version,
        platform=platform,
        status=status,
        attempted_prompts=attempted_prompts,
        proofs=_proofs(proof_values),
        evidence=evidence,
        checked_at=checked_at,
    )


async def _close_failed_attempt(
    controller: InteractiveController,
) -> LiveEvidenceRefV1 | None:
    try:
        await controller.close(
            InteractiveRunOutcome.FAILED,
            reason="direct-ACP live qualification failed",
        )
    except BaseException:
        with contextlib.suppress(BaseException):
            await controller.detach()
    if controller.record.phase is not InteractiveRunPhase.CLOSED:
        with contextlib.suppress(BaseException):
            await controller.detach()
    return _manifest_evidence(controller)


async def qualify_live_direct_acp(
    target: DirectAcpQualificationTarget,
    qualification: ProviderDoctorV1,
    *,
    environ: Mapping[str, str] | None = None,
    platform: str = sys.platform,
    node: str = "node",
    clock: Callable[[], datetime] | None = None,
    token_factory: Callable[[], str] | None = None,
    _provider_factory: Callable[[], MemberExecutionProvider] | None = None,
) -> DirectAcpLiveQualificationResult:
    """Attempt exactly one five-prompt lifecycle, without retries.

    This function is the only production bypass of the normal live-attestation
    gate. Callers must perform the attended confirmation before entering it.
    """
    if platform == "win32":
        raise DirectAcpError("live direct-ACP qualification is paused on Windows")
    if (
        qualification.provider != RUNTIME_ID
        or qualification.status != "pass"
        or qualification.model_calls != 0
        or qualification.capabilities.persistent_turns is not CapabilityLevel.UNKNOWN
        or qualification.capabilities.recovery is not CapabilityLevel.UNKNOWN
    ):
        raise DirectAcpError("live qualification requires an exact staged no-call report")

    now = clock or (lambda: datetime.now(tz=UTC))
    env = dict(os.environ if environ is None else environ)
    token = (token_factory or (lambda: secrets.token_hex(16)))()
    if not token:
        raise DirectAcpError("live qualification token factory returned an empty value")
    attempt_id = hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]
    nonce = hashlib.sha256(("direct-acp-live:" + token).encode("utf-8")).hexdigest()[:24]
    attempts_root = default_runtime_base(env) / "live-attempts"
    ensure_owner_directory(attempts_root, platform=platform)
    attempt_root = attempts_root / attempt_id
    try:
        attempt_root.mkdir(mode=0o700)
    except FileExistsError:
        raise DirectAcpError("live qualification attempt identity already exists") from None
    workspace = attempt_root / "workspace"
    workspace.mkdir(mode=0o700)
    package = _qualification_package(attempt_root / "assistant", platform=platform)
    team, team_source, catalog_target = _qualification_team(package)
    runs_root, reservations_root = default_interactive_roots(env)
    ensure_owner_directory(runs_root, platform=platform)
    ensure_owner_directory(reservations_root, platform=platform)
    request = InteractiveRunRequestV1(
        schema_version=1,
        kind="interactive-run-request",
        target=catalog_target,
        workspace=str(workspace),
        goal="Prove the exact bounded persistent-session lifecycle.",
        done_when=["all five lifecycle probes and final cleanup pass"],
    )
    effective_capabilities = qualification.capabilities.model_copy(
        update={
            "persistent_turns": CapabilityLevel.SUPPORTED,
            "recovery": CapabilityLevel.SUPPORTED,
        }
    )
    effective_report = qualification.model_copy(update={"capabilities": effective_capabilities})

    def new_provider() -> MemberExecutionProvider:
        if _provider_factory is not None:
            return _provider_factory()
        return DirectAcpProvider(
            runtime_path=target.runtime_path,
            environment=target.environment,
            node=node,
            capabilities=effective_capabilities,
            doctor_report=effective_report,
            platform=platform,
        )

    def launch(provider: MemberExecutionProvider) -> dict[str, MemberLaunch]:
        descriptor = provider.describe()
        if descriptor.provider_id != RUNTIME_ID:
            raise DirectAcpError("live qualifier provider identity is not direct-acp")
        return {
            _MEMBER: MemberLaunch(
                member=_MEMBER,
                assistant=package,
                provider=provider,
                harness=target.harness,
                executable=target.command,
                environment=target.environment,
                config_home_variable=target.config_home_variable,
                config_home=target.config_home,
            )
        }

    proof_values = {
        "context_established": False,
        "strict_post_turn_resume": False,
        "recall": False,
        "reset_isolation": False,
        "new_run_isolation": False,
        "continuity_close": False,
    }
    evidence: list[LiveEvidenceRefV1] = []
    attempted_prompts = 0
    current: InteractiveController | None = None
    all_runs_closed = False

    async def probe(
        controller: InteractiveController,
        number: int,
        prompt: str,
        expected: str,
    ) -> None:
        nonlocal attempted_prompts
        if attempted_prompts >= MAX_LIVE_PROMPTS:
            raise _LiveQualificationFailure("live prompt ceiling would be exceeded")
        attempted_prompts += 1
        tool_activity = False

        async def observe(event: ProviderEvent) -> None:
            nonlocal tool_activity
            normalized = event.event.lower().replace("-", "_")
            if normalized == "permission_request" or "tool" in normalized:
                tool_activity = True

        outcome = await controller.dispatch(_MEMBER, prompt, event_sink=observe)
        if outcome.result.status.value != "completed":
            raise _LiveQualificationFailure(
                f"lifecycle probe {number} did not complete successfully"
            )
        if tool_activity:
            raise _LiveQualificationFailure(
                f"lifecycle probe {number} attempted unexpected tool activity"
            )
        if outcome.text != expected:
            raise _LiveQualificationFailure(
                f"lifecycle probe {number} response did not match the exact contract"
            )

    try:
        first_provider = new_provider()
        current = await InteractiveController.create(
            request=request,
            team=team,
            team_source=team_source,
            launches=launch(first_provider),
            runs_root=runs_root,
            reservations_root=reservations_root,
            platform=platform,
        )
        await probe(
            current,
            1,
            "Lifecycle probe 1/5. Memorize this nonce exactly: "
            f"{nonce}. Reply with exactly: STORED {nonce}",
            f"STORED {nonce}",
        )
        proof_values["context_established"] = True
        before_restart = current.session_records[_MEMBER]
        await current.detach()
        if current.record.phase is not InteractiveRunPhase.INTERRUPTED:
            raise _LiveQualificationFailure("provider suspension was not fully proven")
        current = None

        resumed_provider = new_provider()
        if resumed_provider is first_provider:
            raise _LiveQualificationFailure("live qualifier did not create a fresh provider")
        archive = InteractiveArchive(runs_root / before_restart.run_id, platform=platform)
        current = InteractiveController.attach(
            archive=archive,
            team=team,
            launches=launch(resumed_provider),
            reservations_root=reservations_root,
            platform=platform,
        )
        recovered = await current.recover()
        after_restart = current.session_records[_MEMBER]
        if recovered != {_MEMBER: True} or (
            after_restart.session_id,
            after_restart.generation,
            after_restart.provider_session_ref,
        ) != (
            before_restart.session_id,
            before_restart.generation,
            before_restart.provider_session_ref,
        ):
            raise _LiveQualificationFailure("exact post-turn session resume was not proven")
        proof_values["strict_post_turn_resume"] = True
        await probe(
            current,
            2,
            "Lifecycle probe 2/5. Without a nonce in this prompt, reply with exactly "
            "RECALLED followed by one space and the nonce from probe 1.",
            f"RECALLED {nonce}",
        )
        proof_values["recall"] = True

        reset = await current.reset_member(_MEMBER)
        if reset.generation != before_restart.generation + 1:
            raise _LiveQualificationFailure("Member reset did not advance the generation")
        await probe(
            current,
            3,
            "Lifecycle probe 3/5. If any earlier probe nonce is present in this "
            "conversation, reply LEAKED. Otherwise reply exactly: RESET_ISOLATED",
            "RESET_ISOLATED",
        )
        proof_values["reset_isolation"] = True
        closed_first = await current.close(
            InteractiveRunOutcome.CANCELLED,
            reason="first live qualification run complete",
        )
        if closed_first.phase is not InteractiveRunPhase.CLOSED:
            raise _LiveQualificationFailure("first qualification run did not close cleanly")
        first_evidence = _manifest_evidence(current)
        if first_evidence is None:
            raise _LiveQualificationFailure("first qualification evidence is incomplete")
        evidence.append(first_evidence)
        current = None

        second_provider = new_provider()
        current = await InteractiveController.create(
            request=request,
            team=team,
            team_source=team_source,
            launches=launch(second_provider),
            runs_root=runs_root,
            reservations_root=reservations_root,
            platform=platform,
        )
        await probe(
            current,
            4,
            "Lifecycle probe 4/5. If any nonce from another run is present in this "
            "conversation, reply LEAKED. Otherwise reply exactly: NEW_RUN_ISOLATED",
            "NEW_RUN_ISOLATED",
        )
        proof_values["new_run_isolation"] = True
        await probe(
            current,
            5,
            "Lifecycle probe 5/5. Reply exactly: CONTINUITY_READY",
            "CONTINUITY_READY",
        )
        session = current.provider_sessions[_MEMBER]
        continuity = await current.launches[_MEMBER].provider.verify_continuity(session)
        if (
            not continuity
            or current.record.phase is not InteractiveRunPhase.OPEN
            or current.session_records[_MEMBER].status is not SessionStatus.OPEN
        ):
            raise _LiveQualificationFailure("final provider continuity was not proven")
        closed_second = await current.close(
            InteractiveRunOutcome.SUCCEEDED,
            reason="direct-ACP live qualification passed",
        )
        if closed_second.phase is not InteractiveRunPhase.CLOSED:
            raise _LiveQualificationFailure("final qualification close was incomplete")
        second_evidence = _manifest_evidence(current)
        if second_evidence is None:
            raise _LiveQualificationFailure("final qualification evidence is incomplete")
        evidence.append(second_evidence)
        current = None
        all_runs_closed = True
        proof_values["continuity_close"] = True
        passing = _attestation(
            target,
            platform=platform,
            status="pass",
            attempted_prompts=attempted_prompts,
            proof_values=proof_values,
            evidence=evidence,
            checked_at=now(),
        )
        path = write_direct_acp_live_attestation(
            target,
            passing,
            environ=env,
            platform=platform,
        )
        shutil.rmtree(attempt_root)
        return DirectAcpLiveQualificationResult(attestation=passing, path=path)
    except (Exception, asyncio.CancelledError, KeyboardInterrupt) as error:
        proof_values["continuity_close"] = False
        if current is not None:
            failed_evidence = await _close_failed_attempt(current)
            if failed_evidence is not None and all(
                item.run_id != failed_evidence.run_id for item in evidence
            ):
                evidence.append(failed_evidence)
            all_runs_closed = current.record.phase is InteractiveRunPhase.CLOSED
        failed = _attestation(
            target,
            platform=platform,
            status="fail",
            attempted_prompts=attempted_prompts,
            proof_values=proof_values,
            evidence=evidence,
            checked_at=now(),
        )
        path = write_direct_acp_live_attestation(
            target,
            failed,
            environ=env,
            platform=platform,
        )
        if all_runs_closed:
            shutil.rmtree(attempt_root, ignore_errors=True)
        return DirectAcpLiveQualificationResult(
            attestation=failed,
            path=path,
            detail=str(error) or type(error).__name__,
            interrupted=isinstance(error, (asyncio.CancelledError, KeyboardInterrupt)),
        )
