"""MemberExecutionProvider conformance for both deterministic ownership models."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from agentteam.domain.common import HarnessId
from agentteam.domain.interactive import CapabilityLevel, CleanupFact
from agentteam.execution import fakes
from agentteam.execution.fakes import (
    ExternalHostFakeProvider,
    FakeProviderError,
    OwnedProcessFakeProvider,
)
from agentteam.execution.protocol import (
    CancelDisposition,
    OpenMemberSpec,
    ProviderTurnStatus,
    TurnSpec,
)


def _spec(tmp_path: Path, *, session_id: str = "session-lead-1") -> OpenMemberSpec:
    workspace = tmp_path / "workspace"
    workspace.mkdir(exist_ok=True)
    return OpenMemberSpec(
        run_id="run-provider-1",
        member="lead",
        session_id=session_id,
        generation=1,
        workspace=workspace,
        state_dir=tmp_path / "runtime" / session_id,
        harness=HarnessId.CODEX,
        executable=("fake",),
    )


@pytest.mark.parametrize("provider_type", [OwnedProcessFakeProvider, ExternalHostFakeProvider])
async def test_fake_provider_retains_context_cancels_and_closes_truthfully(
    tmp_path: Path,
    provider_type: type[OwnedProcessFakeProvider] | type[ExternalHostFakeProvider],
) -> None:
    provider = provider_type()
    spec = _spec(tmp_path)
    session = await provider.open_member(spec)
    process = (
        provider.processes[session.session_id]
        if isinstance(provider, OwnedProcessFakeProvider)
        else None
    )
    descendant = (
        provider.descendant_pids[session.session_id]
        if isinstance(provider, OwnedProcessFakeProvider)
        else None
    )
    try:
        assert await provider.verify_continuity(session)
        first = await provider.start_turn(
            session, TurnSpec(turn_id="turn-1", request_id="request-1", text="remember-alpha")
        )
        first_events = [event async for event in first]
        first_result = await first.result()
        assert [event.event for event in first_events] == ["turn-started", "text"]
        assert first_result.status is ProviderTurnStatus.COMPLETED
        assert first_result.text == "turn-1:remember-alpha"

        second = await provider.start_turn(
            session, TurnSpec(turn_id="turn-2", request_id="request-2", text="recall")
        )
        assert (await second.result()).text == "turn-2:remember-alpha|recall"

        waiting = await provider.start_turn(
            session, TurnSpec(turn_id="turn-3", request_id="request-3", text="WAIT")
        )
        await asyncio.sleep(0.02)
        assert await provider.cancel_turn(session, "owner cancel") is CancelDisposition.RUNNING
        assert (await waiting.result()).status is ProviderTurnStatus.CANCELLED
        assert await provider.cancel_turn(session, "already done") is CancelDisposition.TERMINAL

        close = await provider.close_member(session, "test complete")
        assert close.logical_session is CleanupFact.CONFIRMED
        assert close.local_state is CleanupFact.CONFIRMED
        assert not session.state_dir.exists()
        if isinstance(provider, OwnedProcessFakeProvider):
            assert close.process is CleanupFact.CONFIRMED
            assert close.provider_history is CleanupFact.CONFIRMED
            assert process is not None and process.poll() is not None
            assert descendant is not None and not fakes._process_is_running(descendant)
        else:
            assert close.process is CleanupFact.NOT_APPLICABLE
            assert close.provider_history is CleanupFact.UNSUPPORTED
        assert await provider.dispose_run(session.run_id) is CleanupFact.CONFIRMED
    finally:
        if session.session_id in provider.sessions:
            await provider.close_member(session, "test cleanup")


@pytest.mark.parametrize("provider_type", [OwnedProcessFakeProvider, ExternalHostFakeProvider])
async def test_fake_provider_never_replaces_lost_context(
    tmp_path: Path,
    provider_type: type[OwnedProcessFakeProvider] | type[ExternalHostFakeProvider],
) -> None:
    provider = provider_type()
    session = await provider.open_member(_spec(tmp_path))
    provider.lose_session(session.session_id)
    assert not await provider.verify_continuity(session)
    with pytest.raises(FakeProviderError, match="unknown or replaced"):
        await provider.start_turn(
            session, TurnSpec(turn_id="turn-1", request_id="request-1", text="must-not-run")
        )
    if isinstance(provider, OwnedProcessFakeProvider):
        process = provider.processes.pop(session.session_id)
        process.kill()
        process.wait()


async def test_fake_strict_resume_mismatch_has_no_side_effect(tmp_path: Path) -> None:
    provider = ExternalHostFakeProvider()
    spec = _spec(tmp_path)
    mismatched = OpenMemberSpec(**{**spec.__dict__, "resume_session_ref": "different-session"})
    with pytest.raises(FakeProviderError, match="strict continuity mismatch"):
        await provider.open_member(mismatched)
    assert provider.sessions == {}
    assert not spec.state_dir.exists()


def test_fake_capabilities_expose_ownership_difference() -> None:
    owned = OwnedProcessFakeProvider().describe().capabilities
    external = ExternalHostFakeProvider().describe().capabilities
    assert owned.process_stop_observability is CapabilityLevel.SUPPORTED
    assert external.process_stop_observability is CapabilityLevel.UNSUPPORTED
    assert external.provider_history_deletion is CapabilityLevel.UNSUPPORTED
