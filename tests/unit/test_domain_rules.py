"""Model-level rules the plan pins down beyond the JSON Schema (sections 7-9, 11-12)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import ValidationError

from agentteam.domain.assistant import (
    AssistantDefinitionV1,
    HarnessPolicyV1,
    ProhibitedContentCheck,
)
from agentteam.domain.bundle import AssistantRefV1, BundleManifestV1
from agentteam.domain.common import HarnessId, RunStatus
from agentteam.domain.profile import (
    CapabilityRecordV1,
    EnvironmentNamesV1,
    HarnessProfileSetV1,
    HarnessProfileV1,
    TimeoutsV1,
)
from agentteam.domain.request import LimitsV1, RunRequestV1
from agentteam.domain.run import (
    CostSource,
    EnsembleRecordV1,
    ExecutionBindingV1,
    ExecutionKind,
    HarnessInvocationV1,
    MemberRecordV1,
    RunRecordV1,
    SynthesisLinkV1,
    TimingV1,
    UsageV1,
)

H64 = "a" * 64
NOW = datetime(2026, 8, 23, tzinfo=UTC)


def _definition(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "schema_version": 1,
        "kind": "assistant-definition",
        "id": "code-reviewer",
        "version": 1,
        "summary": "Reviews code.",
        "persona": "persona.md",
        "purpose": ["review"],
        "principles": "principles.md",
    }
    base.update(overrides)
    return base


def _member() -> MemberRecordV1:
    return MemberRecordV1(
        name="reviewer",
        assistant=AssistantRefV1(id="code-reviewer", version=1, package_hash=H64),
        effective_definition_hash=H64,
        execution=ExecutionBindingV1(kind=ExecutionKind.INVOCATION, ref="inv-1"),
    )


# --- assistant definition ------------------------------------------------------


def test_harness_policy_rejects_a_harness_that_is_both_forbidden_and_allowed() -> None:
    with pytest.raises(ValidationError, match="forbidden"):
        HarnessPolicyV1(preferred=[HarnessId.CODEX], forbidden=[HarnessId.CODEX])


def test_definition_rejects_duplicate_artifact_refs() -> None:
    artifact = {
        "ref": "code-review",
        "kind": "agent-skill",
        "source": {"vendored": "skills/code-review"},
    }
    with pytest.raises(ValidationError, match="unique"):
        AssistantDefinitionV1.model_validate(_definition(artifacts=[artifact, artifact]))


def test_definition_rejects_paths_that_escape_the_package() -> None:
    for bad in ("../persona.md", "/abs/persona.md", "dir\\persona.md", "dir/", "a//b", "."):
        with pytest.raises(ValidationError):
            AssistantDefinitionV1.model_validate(_definition(persona=bad))


def test_definition_accepts_legitimate_relative_paths() -> None:
    for good in ("persona.md", "docs/persona.md", ".hidden.md", "..notes.md"):
        AssistantDefinitionV1.model_validate(_definition(persona=good))


def test_definition_defaults_enable_every_prohibited_content_check() -> None:
    definition = AssistantDefinitionV1.model_validate(_definition())
    assert definition.prohibited_content == list(ProhibitedContentCheck)


# --- run request ---------------------------------------------------------------


def test_run_request_rejects_duplicate_harnesses() -> None:
    with pytest.raises(ValidationError, match="unique"):
        RunRequestV1(
            schema_version=1,
            kind="run-request",
            assistant="examples/assistants/code-reviewer",
            workspace="fixtures/review-target",
            task_file="task.md",
            mode="direct",
            harnesses=[HarnessId.CODEX, HarnessId.CODEX],
        )


def test_run_request_rejects_duplicate_override_harnesses() -> None:
    payload: dict[str, Any] = {
        "schema_version": 1,
        "kind": "run-request",
        "assistant": "examples/assistants/code-reviewer",
        "workspace": "fixtures/review-target",
        "task_file": "task.md",
        "mode": "direct",
        "model_overrides": [
            {"harness": "codex", "value": "model-a"},
            {"harness": "codex", "value": "model-b"},
        ],
    }
    with pytest.raises(ValidationError, match="unique"):
        RunRequestV1.model_validate(payload)


def test_request_limits_never_exceed_the_section_9_caps() -> None:
    LimitsV1(attempt_seconds=60, transient_retries=0)
    with pytest.raises(ValidationError):
        LimitsV1(attempt_seconds=15 * 60 + 1)
    with pytest.raises(ValidationError):
        LimitsV1(transient_retries=2)
    with pytest.raises(ValidationError):
        TimeoutsV1(attempt_seconds=15 * 60 + 1)


# --- profiles ------------------------------------------------------------------


def _profile(harness: HarnessId = HarnessId.CODEX) -> HarnessProfileV1:
    return HarnessProfileV1(
        harness=harness,
        executable=harness.value,
        config_home=f"~/.agentteam/vendors/{harness.value}",
        environment=EnvironmentNamesV1(config_home_variable=f"{harness.value.upper()}_HOME"),
    )


def test_profile_set_allows_at_most_one_profile_per_harness() -> None:
    with pytest.raises(ValidationError, match="one profile per harness"):
        HarnessProfileSetV1(
            schema_version=1,
            kind="harness-profile-set",
            profiles=[_profile(), _profile()],
        )


def test_profile_set_default_harness_must_name_a_listed_profile() -> None:
    HarnessProfileSetV1(
        schema_version=1,
        kind="harness-profile-set",
        profiles=[_profile()],
        default_harness=HarnessId.CODEX,
    )
    with pytest.raises(ValidationError, match="default_harness"):
        HarnessProfileSetV1(
            schema_version=1,
            kind="harness-profile-set",
            profiles=[_profile()],
            default_harness=HarnessId.GROK,
        )


def test_profile_rejects_duplicate_capability_rows() -> None:
    with pytest.raises(ValidationError, match="capability names must be unique"):
        HarnessProfileV1(
            harness=HarnessId.GROK,
            executable="grok",
            config_home="~/.agentteam/vendors/grok",
            environment=EnvironmentNamesV1(config_home_variable="GROK_HOME"),
            capabilities=[CapabilityRecordV1(name="headless"), CapabilityRecordV1(name="headless")],
        )


def test_profile_rejects_duplicate_hint_mappings() -> None:
    with pytest.raises(ValidationError, match="unique"):
        HarnessProfileV1.model_validate(
            {
                "harness": "codex",
                "executable": "codex",
                "config_home": "~/.agentteam/vendors/codex",
                "environment": {"config_home_variable": "CODEX_HOME"},
                "effort_mappings": [
                    {"reasoning": "high", "effort": "xhigh"},
                    {"reasoning": "high", "effort": "high"},
                ],
            }
        )


# --- archive records -----------------------------------------------------------


def test_usage_never_carries_a_fabricated_or_currencyless_cost() -> None:
    UsageV1(cost_amount=0.5, cost_currency="USD", cost_source=CostSource.VENDOR)
    with pytest.raises(ValidationError, match="cost_source=vendor"):
        UsageV1(cost_amount=0.5, cost_currency="USD", cost_source=CostSource.UNAVAILABLE)
    with pytest.raises(ValidationError, match="cost_currency"):
        UsageV1(cost_amount=0.5, cost_source=CostSource.VENDOR)


def test_execution_binding_ref_must_match_its_kind() -> None:
    ExecutionBindingV1(kind=ExecutionKind.INVOCATION, ref="inv-1")
    ExecutionBindingV1(kind=ExecutionKind.ENSEMBLE, ref="ens-1")
    with pytest.raises(ValidationError, match="ref"):
        ExecutionBindingV1(kind=ExecutionKind.ENSEMBLE, ref="inv-1")
    with pytest.raises(ValidationError, match="ref"):
        ExecutionBindingV1(kind=ExecutionKind.INVOCATION, ref="ens-1")


def test_run_record_requires_aware_timestamps() -> None:
    with pytest.raises(ValidationError):
        RunRecordV1(
            schema_version=1,
            kind="run-record",
            run_id="run-1",
            mode="direct",
            member=_member(),
            timing=TimingV1(started_at=datetime(2026, 8, 23)),  # naive
            status=RunStatus.PENDING,
        )


def test_terminal_status_requires_finished_at(payloads: dict[str, dict[str, Any]]) -> None:
    record = RunRecordV1(
        schema_version=1,
        kind="run-record",
        run_id="run-1",
        mode="direct",
        member=_member(),
        timing=TimingV1(started_at=NOW),
        status=RunStatus.PENDING,
    )
    assert record.status is RunStatus.PENDING
    with pytest.raises(ValidationError, match="finished_at"):
        RunRecordV1(
            schema_version=1,
            kind="run-record",
            run_id="run-1",
            mode="direct",
            member=_member(),
            timing=TimingV1(started_at=NOW),
            status=RunStatus.SUCCEEDED,
        )
    invocation = payloads["harness-invocation-v1.schema.json"]
    terminal = {**invocation, "status": "failed"}
    with pytest.raises(ValidationError, match="finished_at"):
        HarnessInvocationV1.model_validate(terminal)


def test_bundle_manifest_enforces_the_archive_contract_invariants() -> None:
    def manifest(paths: list[str]) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "bundle-manifest",
            "assistant": {"id": "x", "version": 1, "package_hash": H64},
            "effective_definition_hash": H64,
            "files": [{"path": p, "size": 1, "sha256": H64} for p in paths],
            "created_at": "2026-08-23T12:00:00Z",
        }

    BundleManifestV1.model_validate(manifest(["A.md", "a.txt/x", "b.md"]))
    with pytest.raises(ValidationError, match="unique"):
        BundleManifestV1.model_validate(manifest(["a.md", "a.md"]))
    with pytest.raises(ValidationError, match="sorted"):
        BundleManifestV1.model_validate(manifest(["b.md", "a.md"]))
    with pytest.raises(ValidationError, match="case"):
        BundleManifestV1.model_validate(manifest(["README.md", "readme.md"]))
    with pytest.raises(ValidationError, match="NFC"):
        BundleManifestV1.model_validate(manifest(["cafe\u0301.md"]))  # NFD: e + combining acute


def test_ensemble_legs_are_unique_and_non_empty() -> None:
    synthesis = SynthesisLinkV1(instruction_hash=H64)
    with pytest.raises(ValidationError):
        EnsembleRecordV1(
            schema_version=1,
            kind="ensemble-record",
            ensemble_id="ens-1",
            run_id="run-1",
            legs=[],
            synthesis=synthesis,
            status=RunStatus.PENDING,
        )
    with pytest.raises(ValidationError, match="unique"):
        EnsembleRecordV1(
            schema_version=1,
            kind="ensemble-record",
            ensemble_id="ens-1",
            run_id="run-1",
            legs=["inv-1", "inv-1"],
            synthesis=synthesis,
            status=RunStatus.PENDING,
        )
