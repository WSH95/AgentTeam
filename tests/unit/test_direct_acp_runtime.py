"""Pinned direct-ACP packaging, installation boundary, and no-call doctor."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from agentteam.domain.common import HarnessId
from agentteam.domain.interactive import (
    CapabilityLevel,
    LiveEvidenceRefV1,
    LiveLifecycleProofsV1,
    ProviderLiveAttestationV1,
)
from agentteam.execution import direct_acp
from agentteam.interactive.archive import InteractiveArchive
from agentteam.resolution.profiles import seed_default_profiles


def test_packaged_lock_has_exact_pins_integrities_and_no_fallbacks() -> None:
    assert direct_acp.verify_packaged_lock() == []
    package = json.loads(direct_acp._resource_bytes("package.json"))
    lock = json.loads(direct_acp._resource_bytes("package-lock.json"))
    assert package["dependencies"] == direct_acp.EXPECTED_PINS
    assert lock["packages"][""]["dependencies"] == direct_acp.EXPECTED_PINS
    for name, version in direct_acp.EXPECTED_PINS.items():
        row = lock["packages"][f"node_modules/{name}"]
        assert row["version"] == version
        assert row["integrity"].startswith("sha512-")

    bridge = direct_acp._resource_bytes("bridge.mjs").decode("utf-8")
    assert 'from "acpx/runtime"' in bridge
    for forbidden in ("npx", "node-pty", "jsonrpc", "session/prompt", "session/load"):
        assert forbidden not in bridge


async def test_doctor_is_truthful_when_runtime_is_not_installed(tmp_path: Path) -> None:
    node = shutil.which("node")
    assert node is not None
    report = await direct_acp.doctor_direct_acp(
        environ={"AGENTTEAM_HOME": str(tmp_path), "PATH": "/usr/bin:/bin"}, node=node
    )
    assert report.model_calls == 0
    assert report.status == "unsupported"
    assert {check.name: check.status for check in report.checks} == {
        "packaged-lock": "pass",
        "node-version": "pass",
        "runtime-install": "unsupported",
    }


async def test_doctor_qualifies_exact_target_and_rejects_stale_cache(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    node = shutil.which("node")
    assert node is not None
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    target = direct_acp.DirectAcpQualificationTarget(
        harness=HarnessId.CODEX,
        runtime_path=runtime,
        command=(node, "fake-agent.mjs"),
        environment={"PATH": str(Path(node).parent)},
        native_version="codex-cli 1.2.3",
        expected_version="codex-cli 1.2.3",
        config_home_variable="CODEX_HOME",
        config_home=tmp_path / "codex-home",
        fingerprint="a" * 64,
    )

    monkeypatch.setattr(direct_acp, "_installed_runtime_problems", lambda _path: [])

    async def qualify(
        _target: direct_acp.DirectAcpQualificationTarget,
        *,
        node: str,
    ) -> direct_acp.DirectAcpQualificationResult:
        assert node
        return direct_acp.DirectAcpQualificationResult(
            runtime_controls=("session/status",),
            agent_capabilities=("loadSession",),
            empty_reconnect="strict-resume",
        )

    monkeypatch.setattr(direct_acp, "_qualify_direct_acp_target", qualify)
    environ = {
        "AGENTTEAM_HOME": str(tmp_path / "home"),
        "PATH": str(Path(node).parent),
    }
    report = await direct_acp.doctor_direct_acp(
        environ=environ,
        node=node,
        runtime_path=runtime,
        targets=(target,),
    )

    assert report.status == "pass"
    assert report.model_calls == 0
    assert report.capabilities.persistent_turns is CapabilityLevel.UNKNOWN
    assert report.capabilities.recovery is CapabilityLevel.UNKNOWN
    assert report.capabilities.permission_events is CapabilityLevel.SUPPORTED
    assert report.capabilities.native_spawn_control is CapabilityLevel.UNSUPPORTED
    cached, problems = direct_acp.load_direct_acp_qualification(
        target,
        environ=environ,
    )
    assert problems == []
    assert cached == report
    persisted = json.loads(
        direct_acp.qualification_path(HarnessId.CODEX, environ).read_text(encoding="utf-8")
    )
    assert persisted["format"] == direct_acp.QUALIFICATION_FORMAT
    assert persisted["empty_reconnect"] == "strict-resume"

    stale, problems = direct_acp.load_direct_acp_qualification(
        replace(target, fingerprint="b" * 64),
        environ=environ,
    )
    assert stale is None
    assert problems == ["qualification fingerprint is stale or mismatched"]

    persisted.pop("empty_reconnect")
    direct_acp.qualification_path(HarnessId.CODEX, environ).write_text(
        json.dumps(persisted),
        encoding="utf-8",
    )
    missing_disposition, problems = direct_acp.load_direct_acp_qualification(
        target,
        environ=environ,
    )
    assert missing_disposition is None
    assert problems == ["qualification empty reconnect disposition is invalid"]


def test_unqualified_provider_claims_no_runtime_capability(tmp_path: Path) -> None:
    provider = direct_acp.DirectAcpProvider(runtime_path=tmp_path)
    capabilities = provider.describe().capabilities
    assert all(
        getattr(capabilities, name) is CapabilityLevel.UNKNOWN
        for name in (
            "persistent_turns",
            "recovery",
            "permission_events",
            "workspace_enforcement",
            "process_stop_observability",
            "local_state_deletion",
        )
    )


def test_live_attestation_cache_is_exact_owner_only_and_failure_invalidates_pass(
    tmp_path: Path,
) -> None:
    target = direct_acp.DirectAcpQualificationTarget(
        harness=HarnessId.CODEX,
        runtime_path=tmp_path / "runtime",
        command=("node", "agent.mjs"),
        environment={},
        native_version="codex 1.2.3",
        expected_version="codex 1.2.3",
        config_home_variable="CODEX_HOME",
        config_home=tmp_path / "codex-home",
        fingerprint="a" * 64,
    )
    environ = {"AGENTTEAM_HOME": str(tmp_path / "home")}
    evidence: list[LiveEvidenceRefV1] = []
    evidence_roots: dict[str, Path] = {}
    for run_id in ("run-live-1", "run-live-2"):
        root = tmp_path / "home" / "runs" / run_id
        root.mkdir(parents=True)
        (root / "evidence.txt").write_text(run_id + "\n", encoding="utf-8")
        archive = InteractiveArchive(root)
        archive.finalize_manifest()
        manifest = root / "manifest.sha256.json"
        evidence.append(
            LiveEvidenceRefV1(
                run_id=run_id,
                manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
            )
        )
        evidence_roots[run_id] = root
    proofs = LiveLifecycleProofsV1(
        context_established=True,
        strict_post_turn_resume=True,
        recall=True,
        reset_isolation=True,
        new_run_isolation=True,
        continuity_close=True,
    )
    passing = ProviderLiveAttestationV1(
        schema_version=1,
        kind="provider-live-attestation",
        provider=direct_acp.RUNTIME_ID,
        harness=target.harness,
        target_fingerprint=target.fingerprint,
        runtime_lock_hash=direct_acp.runtime_lock_hash(),
        native_version=target.native_version,
        platform=sys.platform,
        status="pass",
        attempted_prompts=5,
        proofs=proofs,
        evidence=evidence,
        checked_at=datetime(2026, 8, 25, tzinfo=UTC),
    )

    path = direct_acp.write_direct_acp_live_attestation(
        target,
        passing,
        environ=environ,
    )
    if os.name != "nt":
        assert path.stat().st_mode & 0o077 == 0
    loaded, problems = direct_acp.load_direct_acp_live_attestation(
        target,
        environ=environ,
    )
    assert problems == []
    assert loaded == passing

    (evidence_roots["run-live-1"] / "evidence.txt").write_text(
        "tampered\n", encoding="utf-8"
    )
    loaded, problems = direct_acp.load_direct_acp_live_attestation(
        target,
        environ=environ,
    )
    assert loaded is None
    assert problems == ["live evidence run-live-1 manifest does not verify"]

    (evidence_roots["run-live-1"] / "manifest.sha256.json").write_text(
        "not-json\n", encoding="utf-8"
    )
    loaded, problems = direct_acp.load_direct_acp_live_attestation(
        target,
        environ=environ,
    )
    assert loaded is None
    assert problems == ["live evidence run-live-1 is invalid: InteractiveArchiveError"]

    stale, problems = direct_acp.load_direct_acp_live_attestation(
        replace(target, fingerprint="c" * 64),
        environ=environ,
    )
    assert stale is None
    assert problems == ["live attestation target_fingerprint is stale or mismatched"]

    failed = passing.model_copy(
        update={
            "status": "fail",
            "attempted_prompts": 2,
            "proofs": proofs.model_copy(update={"recall": False}),
            "evidence": [],
        }
    )
    direct_acp.write_direct_acp_live_attestation(target, failed, environ=environ)
    loaded, problems = direct_acp.load_direct_acp_live_attestation(
        target,
        environ=environ,
    )
    assert loaded is None
    assert problems == ["live attestation status is fail"]

    if os.name != "nt":
        path.chmod(0o644)
        loaded, problems = direct_acp.load_direct_acp_live_attestation(
            target,
            environ=environ,
        )
        assert loaded is None
        assert problems == ["live attestation is not owner-only: codex"]


def test_qualification_fingerprint_binds_child_environment_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile_path = tmp_path / "profiles.yaml"
    executable = tmp_path / "codex"
    executable.write_text("fake executable\n", encoding="utf-8")
    executable.chmod(0o700)
    config_home = tmp_path / "vendors" / "codex"
    config_home.mkdir(parents=True)
    profile = next(
        item for item in seed_default_profiles().profiles if item.harness is HarnessId.CODEX
    ).model_copy(
        update={
            "executable": str(executable),
            "config_home": str(config_home),
            "expected_version": "codex 1.2.3",
        }
    )
    monkeypatch.setattr(direct_acp, "capture_version", lambda *_args, **_kwargs: "codex 1.2.3")
    monkeypatch.setattr(
        direct_acp,
        "resolve_acp_agent_command",
        lambda *_args, **_kwargs: ("node", "pinned-agent.mjs"),
    )
    common = {
        "HOME": str(tmp_path),
        "PATH": str(tmp_path),
        "HTTP_PROXY": "http://proxy-one.invalid",
    }
    first = direct_acp.build_direct_acp_qualification_target(
        profile,
        profile_path=profile_path,
        runtime_path=tmp_path / "runtime",
        node="node",
        environ=common,
        runtime_tree_hash="d" * 64,
    )
    second = direct_acp.build_direct_acp_qualification_target(
        profile,
        profile_path=profile_path,
        runtime_path=tmp_path / "runtime",
        node="node",
        environ={**common, "HTTP_PROXY": "http://proxy-two.invalid"},
        runtime_tree_hash="d" * 64,
    )
    assert first.fingerprint != second.fingerprint


@pytest.mark.skipif(os.name == "nt", reason="symlink creation needs privilege on Windows")
def test_qualification_accepts_a_stable_cli_symlink_and_binds_its_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile_path = tmp_path / "profiles.yaml"
    first_executable = tmp_path / "codex-v1"
    second_executable = tmp_path / "codex-v2"
    for executable in (first_executable, second_executable):
        executable.write_text("fake executable\n", encoding="utf-8")
        executable.chmod(0o700)
    launcher = tmp_path / "codex"
    launcher.symlink_to(first_executable)
    config_home = tmp_path / "vendors" / "codex"
    config_home.mkdir(parents=True)
    profile = next(
        item for item in seed_default_profiles().profiles if item.harness is HarnessId.CODEX
    ).model_copy(
        update={
            "executable": str(launcher),
            "config_home": str(config_home),
            "expected_version": "codex 1.2.3",
        }
    )
    monkeypatch.setattr(direct_acp, "capture_version", lambda *_args, **_kwargs: "codex 1.2.3")
    monkeypatch.setattr(
        direct_acp,
        "resolve_acp_agent_command",
        lambda *_args, **_kwargs: ("node", "pinned-agent.mjs"),
    )
    environ = {"HOME": str(tmp_path), "PATH": str(tmp_path)}

    first = direct_acp.build_direct_acp_qualification_target(
        profile,
        profile_path=profile_path,
        runtime_path=tmp_path / "runtime",
        node="node",
        environ=environ,
        runtime_tree_hash="d" * 64,
    )
    launcher.unlink()
    launcher.symlink_to(second_executable)
    second = direct_acp.build_direct_acp_qualification_target(
        profile,
        profile_path=profile_path,
        runtime_path=tmp_path / "runtime",
        node="node",
        environ=environ,
        runtime_tree_hash="d" * 64,
    )

    assert first.fingerprint != second.fingerprint
    assert first.environment["PATH"].split(os.pathsep)[0] == str(tmp_path)


def test_bridge_event_preserves_structured_control_for_controller_validation() -> None:
    control = {
        "schema_version": 1,
        "kind": "control-request",
        "request_id": "control-1",
        "run_id": "run-1",
        "source_turn_id": "turn-1",
        "actor": "lead",
        "actor_member": "lead",
        "action": "work-update",
        "work_item_id": "implement",
        "status": "running",
    }
    event = direct_acp._provider_event_from_bridge(
        {
            "type": "tool_call",
            "toolCallId": "tool-1",
            "kind": "edit",
            "rawInput": {"control_request": control},
        }
    )
    assert event.event == "tool_call"
    assert json.loads(event.data["control_request"]) == control
    assert json.loads(event.data["rawInput"]) == {"control_request": control}


def test_installer_uses_only_npm_ci_and_publishes_atomically(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []

    def fake_run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        calls.append(argv)
        cwd = Path(str(kwargs["cwd"]))
        for name, version in direct_acp.EXPECTED_PINS.items():
            package_dir = cwd / "node_modules" / name
            package_dir.mkdir(parents=True)
            (package_dir / "package.json").write_text(
                json.dumps({"name": name, "version": version}), encoding="utf-8"
            )
        return subprocess.CompletedProcess(argv, 0, b"", b"")

    monkeypatch.setattr("agentteam.execution.direct_acp.subprocess.run", fake_run)
    environ = {"AGENTTEAM_HOME": str(tmp_path), "PATH": "/usr/bin:/bin"}
    installed = direct_acp.install_direct_acp(environ=environ)
    assert installed == direct_acp.installed_runtime_path(environ)
    assert calls == [["npm", "ci", "--ignore-scripts", "--omit=dev", "--no-audit", "--no-fund"]]
    assert direct_acp._installed_runtime_problems(installed) == []
    assert direct_acp.install_direct_acp(environ=environ) == installed
    assert len(calls) == 1

    package_file = installed / "node_modules" / "acpx" / "package.json"
    package_file.write_text(
        json.dumps({"name": "acpx", "version": direct_acp.EXPECTED_PINS["acpx"]}, indent=2),
        encoding="utf-8",
    )
    assert "installed runtime tree hash mismatch" in direct_acp._installed_runtime_problems(
        installed
    )


@pytest.mark.skipif(os.name == "nt", reason="POSIX mode assertion")
async def test_qualification_cache_must_remain_owner_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    node = shutil.which("node")
    assert node is not None
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    target = direct_acp.DirectAcpQualificationTarget(
        harness=HarnessId.CODEX,
        runtime_path=runtime,
        command=(node, "fake-agent.mjs"),
        environment={"PATH": str(Path(node).parent)},
        native_version="codex-cli 1.2.3",
        expected_version="codex-cli 1.2.3",
        config_home_variable="CODEX_HOME",
        config_home=tmp_path / "codex-home",
        fingerprint="c" * 64,
    )
    monkeypatch.setattr(direct_acp, "_installed_runtime_problems", lambda _path: [])

    async def qualify(
        _target: direct_acp.DirectAcpQualificationTarget,
        *,
        node: str,
    ) -> direct_acp.DirectAcpQualificationResult:
        assert node
        return direct_acp.DirectAcpQualificationResult((), (), "fresh-recreate")

    monkeypatch.setattr(direct_acp, "_qualify_direct_acp_target", qualify)
    environ = {"AGENTTEAM_HOME": str(tmp_path / "home"), "PATH": str(Path(node).parent)}
    report = await direct_acp.doctor_direct_acp(
        environ=environ,
        node=node,
        runtime_path=runtime,
        targets=(target,),
    )
    assert report.status == "pass"
    cache = direct_acp.qualification_path(HarnessId.CODEX, environ)
    cache.chmod(0o644)
    loaded, problems = direct_acp.load_direct_acp_qualification(target, environ=environ)
    assert loaded is None
    assert problems == ["qualification record is not owner-only: codex"]
