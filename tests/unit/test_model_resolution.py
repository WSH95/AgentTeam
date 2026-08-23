"""Model/effort precedence (plan section 11): CLI > request > hint mapping > profile default."""

from __future__ import annotations

from agentteam.domain.assistant import ModelHintsV1
from agentteam.domain.common import HarnessId
from agentteam.domain.profile import (
    EffortMappingV1,
    EnvironmentNamesV1,
    HarnessProfileV1,
    ModelDefaultsV1,
    ModelMappingV1,
)
from agentteam.resolution.models import resolve_model_effort


def _profile() -> HarnessProfileV1:
    return HarnessProfileV1(
        harness=HarnessId.CODEX,
        executable="codex",
        config_home="vendors/codex",
        environment=EnvironmentNamesV1(config_home_variable="CODEX_HOME"),
        model_defaults=ModelDefaultsV1(model="default-model", effort="medium"),
        model_mappings=[ModelMappingV1(tier="strong", model="mapped-strong")],
        effort_mappings=[EffortMappingV1(reasoning="high", effort="xhigh")],
    )


def test_cli_override_beats_everything() -> None:
    requested = resolve_model_effort(
        harness=HarnessId.CODEX,
        cli_model="cli-model",
        cli_effort="cli-effort",
        request_model="req-model",
        request_effort="req-effort",
        profile=_profile(),
        hints=ModelHintsV1(tier="strong", reasoning="high"),
    )
    assert (requested.model, requested.effort) == ("cli-model", "cli-effort")


def test_request_override_beats_mapping_and_default() -> None:
    requested = resolve_model_effort(
        harness=HarnessId.CODEX,
        cli_model=None,
        cli_effort=None,
        request_model="req-model",
        request_effort=None,
        profile=_profile(),
        hints=ModelHintsV1(tier="strong", reasoning="high"),
    )
    assert requested.model == "req-model"
    assert requested.effort == "xhigh"  # reasoning hint mapped by the profile


def test_hint_mapping_beats_profile_default() -> None:
    requested = resolve_model_effort(
        harness=HarnessId.CODEX,
        cli_model=None,
        cli_effort=None,
        request_model=None,
        request_effort=None,
        profile=_profile(),
        hints=ModelHintsV1(tier="strong", reasoning=None),
    )
    assert requested.model == "mapped-strong"
    assert requested.effort == "medium"  # profile default fills the gap


def test_unmapped_hint_falls_through_to_profile_default() -> None:
    requested = resolve_model_effort(
        harness=HarnessId.CODEX,
        cli_model=None,
        cli_effort=None,
        request_model=None,
        request_effort=None,
        profile=_profile(),
        hints=ModelHintsV1(tier="fast", reasoning=None),  # no fast mapping
    )
    assert requested.model == "default-model"


def test_unspecified_stays_unspecified_without_profile_data() -> None:
    profile = _profile()
    profile = profile.model_copy(
        update={"model_defaults": ModelDefaultsV1(), "model_mappings": [], "effort_mappings": []}
    )
    requested = resolve_model_effort(
        harness=HarnessId.CODEX,
        cli_model=None,
        cli_effort=None,
        request_model=None,
        request_effort=None,
        profile=profile,
        hints=ModelHintsV1(),
    )
    assert requested.model is None and requested.effort is None
    assert requested.harness is HarnessId.CODEX
