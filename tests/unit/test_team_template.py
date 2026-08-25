"""TeamTemplateV1 composition, portability, and hashing rules (M1b G1)."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from agentteam.domain.team import TeamTemplateV1, WorkspaceAccess
from agentteam.resolution.team import (
    LoadedTeamTemplate,
    check_team_template,
    hash_team_template,
    load_team_template,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = REPO_ROOT / "examples" / "teams" / "development.yaml"


def _template(payloads: dict[str, dict[str, object]]) -> dict[str, object]:
    return deepcopy(payloads["team-template-v1.schema.json"])


def test_committed_template_resolves_every_reference_and_hashes() -> None:
    loaded = load_team_template(EXAMPLE)
    assert loaded.definition.id == "development"
    assert [member.name for member in loaded.definition.members] == [
        "lead",
        "implementer",
        "reviewer",
    ]
    assert check_team_template(loaded) == []
    assert len(hash_team_template(loaded)) == 64


def test_workspace_access_defaults_read_only_and_forward_references_are_legal(
    payloads: dict[str, dict[str, object]],
) -> None:
    payload = _template(payloads)
    tasks = payload["workflow_skeleton"]
    assert isinstance(tasks, list)
    payload["workflow_skeleton"] = [tasks[1], tasks[0]]
    template = TeamTemplateV1.model_validate(payload)
    by_id = {task.id: task for task in template.workflow_skeleton}
    assert by_id["plan"].workspace_access is WorkspaceAccess.READ_ONLY
    assert by_id["implement"].blocked_by == ["plan"]


@pytest.mark.parametrize("blockers", [["unknown"], ["implement"]])
def test_unknown_or_self_blocker_fails(
    blockers: list[str], payloads: dict[str, dict[str, object]]
) -> None:
    payload = _template(payloads)
    tasks = payload["workflow_skeleton"]
    assert isinstance(tasks, list) and isinstance(tasks[1], dict)
    tasks[1]["blocked_by"] = blockers
    with pytest.raises(ValidationError, match=r"unknown blockers|cannot block itself"):
        TeamTemplateV1.model_validate(payload)


def test_cycle_and_owner_bijection_fail(payloads: dict[str, dict[str, object]]) -> None:
    cyclic = _template(payloads)
    tasks = cyclic["workflow_skeleton"]
    assert isinstance(tasks, list) and isinstance(tasks[0], dict)
    tasks[0]["blocked_by"] = ["implement"]
    with pytest.raises(ValidationError, match="acyclic"):
        TeamTemplateV1.model_validate(cyclic)

    duplicate_owner = _template(payloads)
    tasks = duplicate_owner["workflow_skeleton"]
    assert isinstance(tasks, list) and isinstance(tasks[1], dict)
    tasks[1]["owner"] = "lead"
    with pytest.raises(ValidationError, match="bijection"):
        TeamTemplateV1.model_validate(duplicate_owner)


@pytest.mark.parametrize("subject", ["Use {project}", "Use {goal", "Use goal}", "line\ntwo"])
def test_placeholder_and_single_line_grammar_fail(
    subject: str, payloads: dict[str, dict[str, object]]
) -> None:
    payload = _template(payloads)
    tasks = payload["workflow_skeleton"]
    assert isinstance(tasks, list) and isinstance(tasks[0], dict)
    tasks[0]["subject"] = subject
    with pytest.raises(ValidationError, match=r"placeholder|single-line"):
        TeamTemplateV1.model_validate(payload)


def test_handoff_vocabulary_and_reserved_features_fail_closed(
    payloads: dict[str, dict[str, object]],
) -> None:
    for field, value in (
        ("required_fields", ["task_id", "transcript"]),
        ("acks", ["ACK", "MAYBE"]),
    ):
        payload = _template(payloads)
        handoff = payload["handoff"]
        assert isinstance(handoff, dict)
        handoff[field] = value
        with pytest.raises(ValidationError):
            TeamTemplateV1.model_validate(payload)

    reserved_cases: list[tuple[str, object]] = [
        ("dynamic_members", [{}]),
        ("constraints", ["bound"]),
    ]
    for reserved_field, reserved_value in reserved_cases:
        payload = _template(payloads)
        payload[reserved_field] = reserved_value
        with pytest.raises(ValidationError):
            TeamTemplateV1.model_validate(payload)


def test_reserved_member_visibility_name_and_mechanical_independence_fail(
    payloads: dict[str, dict[str, object]],
) -> None:
    hidden = _template(payloads)
    members = hidden["members"]
    assert isinstance(members, list) and isinstance(members[0], dict)
    members[0]["visibility"] = "hidden"
    with pytest.raises(ValidationError):
        TeamTemplateV1.model_validate(hidden)

    reserved = _template(payloads)
    members = reserved["members"]
    tasks = reserved["workflow_skeleton"]
    assert isinstance(members, list) and isinstance(members[1], dict)
    assert isinstance(tasks, list) and isinstance(tasks[1], dict)
    members[1]["name"] = "synthesis"
    tasks[1]["owner"] = "synthesis"
    with pytest.raises(ValidationError, match="reserved"):
        TeamTemplateV1.model_validate(reserved)

    mechanical = _template(payloads)
    mechanical["independence"] = [
        {"between": ["lead", "implementer"], "declared": "mechanical", "means": []}
    ]
    with pytest.raises(ValidationError, match="not enforceable"):
        TeamTemplateV1.model_validate(mechanical)


def test_relationship_and_preference_keys_must_name_roster_members(
    payloads: dict[str, dict[str, object]],
) -> None:
    relationship = _template(payloads)
    members = relationship["members"]
    assert isinstance(members, list) and isinstance(members[0], dict)
    members[0]["relationships"] = {"coordinates": ["outsider"]}
    with pytest.raises(ValidationError, match="unknown members"):
        TeamTemplateV1.model_validate(relationship)

    preference = _template(payloads)
    preference["preferences"] = {"harness_preferences": {"outsider": ["codex"]}}
    with pytest.raises(ValidationError, match="unknown members"):
        TeamTemplateV1.model_validate(preference)


def test_template_content_checks_reject_prohibited_material(
    payloads: dict[str, dict[str, object]],
) -> None:
    definition = TeamTemplateV1.model_validate(_template(payloads))
    loaded = LoadedTeamTemplate(
        definition=definition,
        path=EXAMPLE,
        source="credential = sk-abcdefghijklmnopqrstuvwx\n",
    )
    assert any("secrets" in problem for problem in check_team_template(loaded))


def test_template_hash_normalizes_newlines_and_changes_with_content(
    tmp_path: Path, payloads: dict[str, dict[str, object]]
) -> None:
    text = yaml.safe_dump(_template(payloads), sort_keys=False)
    lf = tmp_path / "lf.yaml"
    crlf = tmp_path / "crlf.yaml"
    changed = tmp_path / "changed.yaml"
    lf.write_text(text, encoding="utf-8")
    crlf.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
    changed.write_text(text.replace("bounded goal", "different goal"), encoding="utf-8")
    lf_hash = hash_team_template(load_team_template(lf))
    assert hash_team_template(load_team_template(crlf)) == lf_hash
    assert hash_team_template(load_team_template(changed)) != lf_hash
