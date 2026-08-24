"""Harness selection: plan section 11 steps 1-6, `decided_by`, hard failures."""

from __future__ import annotations

import pytest

from agentteam.domain.assistant import HarnessPolicyV1
from agentteam.domain.common import HarnessId
from agentteam.domain.profile import (
    CapabilityRecordV1,
    EnvironmentNamesV1,
    HarnessProfileSetV1,
    HarnessProfileV1,
    Verification,
)
from agentteam.domain.run import DecidedBy
from agentteam.resolution.selection import SelectionError, select_harnesses

CLAUDE, CODEX, GROK = HarnessId.CLAUDE_CODE, HarnessId.CODEX, HarnessId.GROK


def _profile(harness: HarnessId, capabilities: list[str] | None = None) -> HarnessProfileV1:
    return HarnessProfileV1(
        harness=harness,
        executable=harness.value,
        config_home=f"vendors/{harness.value}",
        environment=EnvironmentNamesV1(config_home_variable=f"{harness.value.upper()}_HOME"),
        capabilities=[
            CapabilityRecordV1(name=c, verification=Verification.VERIFIED)
            for c in (capabilities or [])
        ],
    )


def _profiles(*harnesses: HarnessId, default: HarnessId | None = None) -> HarnessProfileSetV1:
    return HarnessProfileSetV1(
        schema_version=1,
        kind="harness-profile-set",
        profiles=[_profile(h) for h in harnesses],
        default_harness=default,
    )


ALL_INSTALLED = lambda profile: True  # noqa: E731


def test_user_request_wins_and_records_decided_by_user() -> None:
    outcome = select_harnesses(
        requested=[CODEX, GROK],
        policy=HarnessPolicyV1(),
        profiles=_profiles(CLAUDE, CODEX, GROK),
        installed=ALL_INSTALLED,
    )
    assert outcome.chosen == [CODEX, GROK]
    assert outcome.selection.decided_by is DecidedBy.USER
    assert set(outcome.selection.candidates) == {CLAUDE, CODEX, GROK}


def test_user_requested_harness_without_profile_fails_hard() -> None:
    with pytest.raises(SelectionError, match="grok"):
        select_harnesses(
            requested=[GROK],
            policy=HarnessPolicyV1(),
            profiles=_profiles(CLAUDE, CODEX),
            installed=ALL_INSTALLED,
        )


def test_user_requested_harness_not_installed_fails_hard() -> None:
    with pytest.raises(SelectionError, match="not installed"):
        select_harnesses(
            requested=[CODEX],
            policy=HarnessPolicyV1(),
            profiles=_profiles(CLAUDE, CODEX),
            installed=lambda p: p.harness is CLAUDE,
        )


def test_user_requested_forbidden_harness_fails_hard() -> None:
    with pytest.raises(SelectionError, match="forbidden"):
        select_harnesses(
            requested=[CODEX],
            policy=HarnessPolicyV1(forbidden=[CODEX]),
            profiles=_profiles(CLAUDE, CODEX),
            installed=ALL_INSTALLED,
        )


def test_user_requested_harness_outside_allowed_list_fails_hard() -> None:
    with pytest.raises(SelectionError, match="allowed"):
        select_harnesses(
            requested=[GROK],
            policy=HarnessPolicyV1(allowed=[CLAUDE, CODEX]),
            profiles=_profiles(CLAUDE, CODEX, GROK),
            installed=ALL_INSTALLED,
        )


def test_empty_allowed_means_no_restriction_beyond_forbidden() -> None:
    outcome = select_harnesses(
        requested=[GROK],
        policy=HarnessPolicyV1(allowed=[]),
        profiles=_profiles(GROK),
        installed=ALL_INSTALLED,
    )
    assert outcome.chosen == [GROK]


def test_required_capability_gates_a_user_request() -> None:
    profiles = HarnessProfileSetV1(
        schema_version=1,
        kind="harness-profile-set",
        profiles=[_profile(CLAUDE, ["structured-output"]), _profile(CODEX)],
    )
    policy = HarnessPolicyV1(required_capabilities=["structured-output"])
    with pytest.raises(SelectionError, match="structured-output"):
        select_harnesses(
            requested=[CODEX], policy=policy, profiles=profiles, installed=ALL_INSTALLED
        )
    ok = select_harnesses(
        requested=[CLAUDE], policy=policy, profiles=profiles, installed=ALL_INSTALLED
    )
    assert ok.chosen == [CLAUDE]


def test_observed_or_unverified_capability_does_not_satisfy_assistant_policy() -> None:
    profile = _profile(CODEX, ["structured-output"])
    row = profile.capabilities[0].model_copy(update={"verification": Verification.OBSERVED})
    profiles = HarnessProfileSetV1(
        schema_version=1,
        kind="harness-profile-set",
        profiles=[profile.model_copy(update={"capabilities": [row]})],
    )
    with pytest.raises(SelectionError, match="structured-output"):
        select_harnesses(
            requested=[CODEX],
            policy=HarnessPolicyV1(required_capabilities=["structured-output"]),
            profiles=profiles,
            installed=ALL_INSTALLED,
        )


def test_assistant_preference_picks_first_eligible_and_is_solo() -> None:
    outcome = select_harnesses(
        requested=[],
        policy=HarnessPolicyV1(preferred=[GROK, CODEX]),
        profiles=_profiles(CLAUDE, CODEX),  # grok has no profile
        installed=ALL_INSTALLED,
    )
    assert outcome.chosen == [CODEX]
    assert outcome.selection.decided_by is DecidedBy.ASSISTANT


def test_profile_default_used_when_assistant_has_no_preference() -> None:
    outcome = select_harnesses(
        requested=[],
        policy=HarnessPolicyV1(),
        profiles=_profiles(CLAUDE, CODEX, default=CODEX),
        installed=ALL_INSTALLED,
    )
    assert outcome.chosen == [CODEX]
    assert outcome.selection.decided_by is DecidedBy.DEFAULT


def test_nothing_eligible_fails_with_per_harness_reasons() -> None:
    with pytest.raises(SelectionError) as excinfo:
        select_harnesses(
            requested=[],
            policy=HarnessPolicyV1(forbidden=[CLAUDE]),
            profiles=_profiles(CLAUDE),
            installed=ALL_INSTALLED,
        )
    assert "claude-code" in str(excinfo.value)
    assert excinfo.value.exit_code == 2
