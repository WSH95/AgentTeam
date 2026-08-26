"""Deterministic orchestration tests for the attended five-call live qualifier."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from agentteam.domain.common import HarnessId
from agentteam.domain.interactive import DoctorCheckV1, ProviderDoctorV1
from agentteam.execution import direct_acp
from agentteam.execution.fakes import ExternalHostFakeProvider
from agentteam.execution.protocol import ActiveTurn, ProviderSession, TurnSpec
from agentteam.interactive.archive import InteractiveArchive
from agentteam.interactive.live_qualification import qualify_live_direct_acp


class _ScriptedLiveProvider(ExternalHostFakeProvider):
    provider_id = direct_acp.RUNTIME_ID

    def __init__(self, responses: dict[int, str], calls: list[int]) -> None:
        super().__init__()
        self.responses = responses
        self.calls = calls

    async def start_turn(self, session: ProviderSession, spec: TurnSpec) -> ActiveTurn:
        number = int(spec.text.partition("probe ")[2].partition("/")[0])
        self.calls.append(number)
        scripted = self.responses[number]
        return await super().start_turn(session, replace(spec, text="EMIT:" + scripted))


def _target(tmp_path: Path) -> direct_acp.DirectAcpQualificationTarget:
    config_home = tmp_path / "config-home"
    config_home.mkdir(exist_ok=True)
    return direct_acp.DirectAcpQualificationTarget(
        harness=HarnessId.CODEX,
        runtime_path=tmp_path / "runtime",
        command=("node", "fake-agent.mjs"),
        environment={},
        native_version="codex 1.2.3",
        expected_version="codex 1.2.3",
        config_home_variable="CODEX_HOME",
        config_home=config_home,
        fingerprint="a" * 64,
    )


def _qualification() -> ProviderDoctorV1:
    return ProviderDoctorV1(
        schema_version=1,
        kind="provider-doctor",
        provider=direct_acp.RUNTIME_ID,
        checked_at=datetime(2026, 8, 25, tzinfo=UTC),
        status="pass",
        capabilities=direct_acp._direct_capabilities(qualified=True),
        checks=[DoctorCheckV1(name="codex-acp-lifecycle", status="pass")],
        model_calls=0,
    )


async def test_live_qualifier_proves_five_calls_and_writes_exact_evidence(
    tmp_path: Path,
) -> None:
    token = "deterministic-success"
    nonce = hashlib.sha256(("direct-acp-live:" + token).encode()).hexdigest()[:24]
    responses = {
        1: f"STORED {nonce}",
        2: f"RECALLED {nonce}",
        3: "RESET_ISOLATED",
        4: "NEW_RUN_ISOLATED",
        5: "CONTINUITY_READY",
    }
    calls: list[int] = []
    environ = {"AGENTTEAM_HOME": str(tmp_path / "home")}
    target = _target(tmp_path)

    result = await qualify_live_direct_acp(
        target,
        _qualification(),
        environ=environ,
        token_factory=lambda: token,
        _provider_factory=lambda: _ScriptedLiveProvider(responses, calls),
    )

    assert result.attestation.status == "pass"
    assert result.attestation.attempted_prompts == 5
    assert all(result.attestation.proofs.model_dump().values())
    assert calls == [1, 2, 3, 4, 5]
    assert len(result.attestation.evidence) == 2
    loaded, problems = direct_acp.load_direct_acp_live_attestation(
        target,
        environ=environ,
    )
    assert problems == []
    assert loaded == result.attestation
    for item in result.attestation.evidence:
        archive = InteractiveArchive(tmp_path / "home" / "runs" / item.run_id)
        assert archive.verify_manifest() == []
        manifest = archive.root / "manifest.sha256.json"
        assert hashlib.sha256(manifest.read_bytes()).hexdigest() == item.manifest_sha256


async def test_failed_live_qualifier_stops_without_retry_and_invalidates_pass(
    tmp_path: Path,
) -> None:
    token = "deterministic-failure"
    nonce = hashlib.sha256(("direct-acp-live:" + token).encode()).hexdigest()[:24]
    responses = {
        1: f"STORED {nonce}",
        2: "WRONG",
    }
    calls: list[int] = []
    environ = {"AGENTTEAM_HOME": str(tmp_path / "home")}
    target = _target(tmp_path)

    result = await qualify_live_direct_acp(
        target,
        _qualification(),
        environ=environ,
        token_factory=lambda: token,
        _provider_factory=lambda: _ScriptedLiveProvider(responses, calls),
    )

    assert result.attestation.status == "fail"
    assert result.attestation.attempted_prompts == 2
    assert result.attestation.proofs.context_established
    assert result.attestation.proofs.strict_post_turn_resume
    assert not result.attestation.proofs.recall
    assert calls == [1, 2]
    assert result.detail == "lifecycle probe 2 response did not match the exact contract"
    loaded, problems = direct_acp.load_direct_acp_live_attestation(
        target,
        environ=environ,
    )
    assert loaded is None
    assert problems == ["live attestation status is fail"]
