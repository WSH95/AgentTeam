"""M1c versioned contracts and V1 byte-compatibility guarantees."""

from __future__ import annotations

import hashlib
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from agentteam.domain.interactive import (
    ControlRequestV1,
    InteractiveRunRecordV1,
    InteractiveRunRequestV1,
    MemberSessionV1,
    ProviderLiveAttestationV1,
    TeamTemplateV2,
    TurnRecordV1,
)
from agentteam.domain.team import TeamTemplateV1
from agentteam.schema import record_model, validate_record

REPO_ROOT = Path(__file__).resolve().parents[2]

V1_SCHEMA_HASHES = {
    "assistant-definition-v1.schema.json": (
        "12cad3a0b4d90d6d2cd33e591e22de50c1098bb9fb66b0e034ff79cef4548067"
    ),
    "bundle-manifest-v1.schema.json": (
        "3a0eb3f1f59b9e052d941cd11e3f2d3b51d9582b4101b2028c90e1e5883c44f3"
    ),
    "ensemble-record-v1.schema.json": (
        "02011ef1739ad3bb9808a72183a5557611342047b1a33dd61c4f158496c4f882"
    ),
    "harness-invocation-v1.schema.json": (
        "dfa07ecd0f0ddbb1fc53ebfb5519503f44f480f1982e8b19d2c5593733bea033"
    ),
    "harness-profile-set-v1.schema.json": (
        "642db8cd5af656064c4916c3984b2cb32670abf849cbf6b3dbea56b3b593f690"
    ),
    "member-result-v1.schema.json": (
        "adb86778e2801b224542d7d39514b8a5f07228dbdff97637d4b60b0619010b96"
    ),
    "normalized-review-v1.schema.json": (
        "9debc6ee51dbefe6b9373bd7aa7950d879af7277b4290fb30f870f19d59b8c98"
    ),
    "run-record-v1.schema.json": (
        "fb0e9206e986f2d186afb16e189a4bf50a105236a9992afdf9579a333fa41a43"
    ),
    "run-request-v1.schema.json": (
        "605a4ec703b3bac1cee230764066f3c14f59ba9c2e629b88e0a1012cd508700d"
    ),
    "synthesis-report-v1.schema.json": (
        "dbfc9163cc9be677d3fa12163f19f6b78e2e99908243f30a2aba4c4132677d20"
    ),
    "team-run-request-v1.schema.json": (
        "068f2e2bdd847d1af3cc464e7ea984b634e8d0f597a78f3df0179362d28378de"
    ),
    "team-template-v1.schema.json": (
        "5d4857eded858c1ccce12b9b981c21e6d8c7f2f43bf349f7901b44e151fbc57e"
    ),
}


def test_original_v1_schema_bytes_are_pinned() -> None:
    for name, expected in V1_SCHEMA_HASHES.items():
        actual = hashlib.sha256((REPO_ROOT / "schemas" / name).read_bytes()).hexdigest()
        assert actual == expected, name


def test_registry_dispatches_team_kind_by_version(
    payloads: dict[str, dict[str, Any]],
) -> None:
    assert record_model("team-template", 1) is TeamTemplateV1
    assert record_model("team-template", 2) is TeamTemplateV2
    assert isinstance(validate_record(payloads["team-template-v1.schema.json"]), TeamTemplateV1)
    assert isinstance(validate_record(payloads["team-template-v2.schema.json"]), TeamTemplateV2)
    with pytest.raises(ValueError, match="unsupported schema identity"):
        record_model("team-template", 3)
    with pytest.raises(ValueError, match="requires string kind"):
        validate_record({"kind": "team-template", "schema_version": True})


def test_v2_workflow_allows_zero_or_multiple_tasks_per_member(
    payloads: dict[str, dict[str, Any]],
) -> None:
    payload = deepcopy(payloads["team-template-v2.schema.json"])
    assert TeamTemplateV2.model_validate(payload).workflow_skeleton == []
    payload["workflow_skeleton"] = [
        {"id": "plan", "subject": "Plan {goal}", "owner": "lead"},
        {
            "id": "review",
            "subject": "Review {goal}",
            "owner": "lead",
            "blocked_by": ["plan"],
        },
    ]
    assert len(TeamTemplateV2.model_validate(payload).workflow_skeleton) == 2


def test_v2_workflow_and_disabled_dynamic_policy_fail_closed(
    payloads: dict[str, dict[str, Any]],
) -> None:
    unknown_owner = deepcopy(payloads["team-template-v2.schema.json"])
    unknown_owner["workflow_skeleton"] = [{"id": "work", "subject": "Work", "owner": "outsider"}]
    with pytest.raises(ValidationError, match="unknown owner"):
        TeamTemplateV2.model_validate(unknown_owner)

    cycle = deepcopy(payloads["team-template-v2.schema.json"])
    cycle["workflow_skeleton"] = [
        {"id": "one", "subject": "One", "owner": "lead", "blocked_by": ["two"]},
        {"id": "two", "subject": "Two", "owner": "lead", "blocked_by": ["one"]},
    ]
    with pytest.raises(ValidationError, match="acyclic"):
        TeamTemplateV2.model_validate(cycle)

    enabled = deepcopy(payloads["team-template-v2.schema.json"])
    enabled["dynamic_members"] = {"enabled": True}
    with pytest.raises(ValidationError):
        TeamTemplateV2.model_validate(enabled)


def test_interactive_request_mechanically_requires_shared_supplied(
    payloads: dict[str, dict[str, Any]],
) -> None:
    payload = deepcopy(payloads["interactive-run-request-v1.schema.json"])
    payload["workspace_layout"] = "per-member-worktree"
    with pytest.raises(ValidationError):
        InteractiveRunRequestV1.model_validate(payload)


def test_live_attestation_requires_exact_bounded_lifecycle_proof(
    payloads: dict[str, dict[str, Any]],
) -> None:
    passing = deepcopy(payloads["provider-live-attestation-v1.schema.json"])
    assert ProviderLiveAttestationV1.model_validate(passing).status == "pass"

    four_prompts = deepcopy(passing)
    four_prompts["attempted_prompts"] = 4
    with pytest.raises(ValidationError, match="five prompts"):
        ProviderLiveAttestationV1.model_validate(four_prompts)

    incomplete = deepcopy(passing)
    incomplete["proofs"]["recall"] = False
    with pytest.raises(ValidationError, match="all proofs"):
        ProviderLiveAttestationV1.model_validate(incomplete)

    one_run = deepcopy(passing)
    one_run["evidence"] = one_run["evidence"][:1]
    with pytest.raises(ValidationError, match="two evidence runs"):
        ProviderLiveAttestationV1.model_validate(one_run)

    false_success = deepcopy(passing)
    false_success["status"] = "fail"
    with pytest.raises(ValidationError, match="must name an unproved"):
        ProviderLiveAttestationV1.model_validate(false_success)

    bounded_failure = deepcopy(false_success)
    bounded_failure["attempted_prompts"] = 2
    bounded_failure["proofs"]["strict_post_turn_resume"] = False
    assert ProviderLiveAttestationV1.model_validate(bounded_failure).status == "fail"

    duplicate_evidence = deepcopy(passing)
    duplicate_evidence["evidence"][1]["run_id"] = duplicate_evidence["evidence"][0]["run_id"]
    with pytest.raises(ValidationError, match="run ids must be unique"):
        ProviderLiveAttestationV1.model_validate(duplicate_evidence)


def test_interactive_run_keeps_phase_outcome_and_cleanup_distinct(
    payloads: dict[str, dict[str, Any]],
) -> None:
    payload = deepcopy(payloads["interactive-run-record-v1.schema.json"])
    payload["outcome"] = "succeeded"
    with pytest.raises(ValidationError, match="only when phase is closed"):
        InteractiveRunRecordV1.model_validate(payload)

    payload["phase"] = "closed"
    with pytest.raises(ValidationError, match="requires outcome, cleanup, and final"):
        InteractiveRunRecordV1.model_validate(payload)

    payload["final_checkpoint"] = payload["initial_checkpoint"]
    payload["cleanup"] = {
        "logical_session": "confirmed",
        "process": "confirmed",
        "local_state": "confirmed",
        "provider_history": "unsupported",
    }
    record = InteractiveRunRecordV1.model_validate(payload)
    assert record.kind == "interactive-run-record"


def test_control_request_has_one_closed_action_payload(
    payloads: dict[str, dict[str, Any]],
) -> None:
    payload = deepcopy(payloads["control-request-v1.schema.json"])
    payload["owner"] = "lead"
    with pytest.raises(ValidationError, match="requires exactly"):
        ControlRequestV1.model_validate(payload)

    member_actor = deepcopy(payloads["control-request-v1.schema.json"])
    member_actor["actor"] = "member"
    with pytest.raises(ValidationError, match="requires actor_member"):
        ControlRequestV1.model_validate(member_actor)


def test_terminal_session_and_turn_records_require_terminal_facts(
    payloads: dict[str, dict[str, Any]],
) -> None:
    session = deepcopy(payloads["member-session-v1.schema.json"])
    session["status"] = "close-failed"
    with pytest.raises(ValidationError, match="requires closed_at and close facts"):
        MemberSessionV1.model_validate(session)

    session = deepcopy(payloads["member-session-v1.schema.json"])
    session["closed_at"] = "2026-08-25T12:01:00Z"
    session["close"] = {
        "logical_session": "confirmed",
        "process": "confirmed",
        "local_state": "confirmed",
        "provider_history": "unknown",
    }
    with pytest.raises(ValidationError, match="nonterminal session"):
        MemberSessionV1.model_validate(session)

    turn = deepcopy(payloads["turn-record-v1.schema.json"])
    turn.update({"status": "completed", "finished_at": "2026-08-25T12:01:00Z"})
    with pytest.raises(ValidationError, match="result_sha256"):
        TurnRecordV1.model_validate(turn)


def test_close_failed_run_requires_durable_failure_facts(
    payloads: dict[str, dict[str, Any]],
) -> None:
    payload = deepcopy(payloads["interactive-run-record-v1.schema.json"])
    payload["phase"] = "close-failed"
    with pytest.raises(ValidationError, match="requires no outcome plus cleanup"):
        InteractiveRunRecordV1.model_validate(payload)
