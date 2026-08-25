"""TeamRunRequestV1 user-layer and goal validation (M1b G1)."""

from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError

from agentteam.domain.team import TeamRunRequestV1, TeamTemplateV1
from agentteam.resolution.team import check_team_request


def _request(payloads: dict[str, dict[str, object]]) -> dict[str, object]:
    return deepcopy(payloads["team-run-request-v1.schema.json"])


@pytest.mark.parametrize("goal", ["", "   ", "line\ntwo", "x\x00y", "x" * 201])
def test_goal_is_bounded_single_line(goal: str, payloads: dict[str, dict[str, object]]) -> None:
    payload = _request(payloads)
    payload["goal"] = goal
    with pytest.raises(ValidationError):
        TeamRunRequestV1.model_validate(payload)


def test_member_model_and_effort_require_same_object_harness(
    payloads: dict[str, dict[str, object]],
) -> None:
    for override in ({"model": "gpt-5"}, {"effort": "high"}):
        payload = _request(payloads)
        payload["members"] = {"implementer": override}
        with pytest.raises(ValidationError, match="requires harness"):
            TeamRunRequestV1.model_validate(payload)

    payload = _request(payloads)
    payload["members"] = {"implementer": {"harness": "codex", "model": "gpt-5", "effort": "high"}}
    request = TeamRunRequestV1.model_validate(payload)
    harness = request.members["implementer"].harness
    assert harness is not None and harness.value == "codex"


def test_member_override_keys_are_checked_against_template_roster(
    payloads: dict[str, dict[str, object]],
) -> None:
    request_payload = _request(payloads)
    request_payload["members"] = {"outsider": {"harness": "codex"}}
    request = TeamRunRequestV1.model_validate(request_payload)
    template = TeamTemplateV1.model_validate(payloads["team-template-v1.schema.json"])
    assert check_team_request(request, template) == [
        "member overrides name unknown members: outsider"
    ]


def test_substrate_and_reserved_overlays_fail_closed(
    payloads: dict[str, dict[str, object]],
) -> None:
    bad_substrate = _request(payloads)
    bad_substrate["substrate"] = "unknown"
    with pytest.raises(ValidationError):
        TeamRunRequestV1.model_validate(bad_substrate)

    overlay = _request(payloads)
    overlay["overlay_refs"] = ["later"]
    with pytest.raises(ValidationError):
        TeamRunRequestV1.model_validate(overlay)


def test_request_is_closed_and_has_no_synthesis_or_per_member_lists(
    payloads: dict[str, dict[str, object]],
) -> None:
    payload = _request(payloads)
    for field in ("synthesis", "harnesses", "visibility"):
        with pytest.raises(ValidationError):
            TeamRunRequestV1.model_validate({**payload, field: True})
