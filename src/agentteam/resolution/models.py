"""Concrete model/effort precedence (plan section 11).

CLI override > RunRequest override > local profile mapping from a portable
hint > local profile default > vendor default (stays unspecified). An
unspecified value stays unspecified unless local profile data supplies it.
"""

from __future__ import annotations

from agentteam.domain.assistant import ModelHintsV1
from agentteam.domain.common import HarnessId
from agentteam.domain.profile import HarnessProfileV1
from agentteam.domain.run import RequestedV1


def resolve_model_effort(
    *,
    harness: HarnessId,
    cli_model: str | None,
    cli_effort: str | None,
    request_model: str | None,
    request_effort: str | None,
    profile: HarnessProfileV1,
    hints: ModelHintsV1,
) -> RequestedV1:
    model = cli_model or request_model
    if model is None and hints.tier is not None:
        for mapping in profile.model_mappings:
            if mapping.tier == hints.tier:
                model = mapping.model
                break
    if model is None:
        model = profile.model_defaults.model

    effort = cli_effort or request_effort
    if effort is None and hints.reasoning is not None:
        for effort_mapping in profile.effort_mappings:
            if effort_mapping.reasoning == hints.reasoning:
                effort = effort_mapping.effort
                break
    if effort is None:
        effort = profile.model_defaults.effort

    return RequestedV1(harness=harness, model=model, effort=effort)
