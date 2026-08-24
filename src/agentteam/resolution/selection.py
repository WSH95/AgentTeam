"""Harness selection (plan section 11, steps 1-6).

Precedence: CLI/RunRequest harnesses (user) > Assistant `harness_policy`
(assistant) > local profile default (default). A user-requested harness that
is not a candidate, not allowed, or not capability-eligible fails the run hard
before anything is launched (exit 2); there is no implicit force mode in M1a.
A `team` layer is reserved for M1b.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from agentteam.domain.assistant import HarnessPolicyV1
from agentteam.domain.common import HarnessId
from agentteam.domain.profile import HarnessProfileSetV1, HarnessProfileV1, Verification
from agentteam.domain.run import DecidedBy, SelectionV1


class SelectionError(ValueError):
    """No valid selection; `exit_code` is the stable CLI code (2 = invalid input)."""

    def __init__(self, message: str, *, exit_code: int = 2) -> None:
        super().__init__(message)
        self.exit_code = exit_code


@dataclass(frozen=True)
class SelectionOutcome:
    chosen: list[HarnessId]
    selection: SelectionV1


def _capability_names(profile: HarnessProfileV1) -> set[str]:
    # Assistant capability requirements are semantic promises.  Merely seeing
    # a flag in --help is not evidence that the channel works end to end.
    return {row.name for row in profile.capabilities if row.verification is Verification.VERIFIED}


def select_harnesses(
    *,
    requested: list[HarnessId],
    policy: HarnessPolicyV1,
    profiles: HarnessProfileSetV1,
    installed: Callable[[HarnessProfileV1], bool],
    user_forbidden: frozenset[HarnessId] = frozenset(),
) -> SelectionOutcome:
    by_id = {profile.harness: profile for profile in profiles.profiles}

    # (1) candidates: a local profile with an installed executable
    candidates = [h for h, p in by_id.items() if installed(p)]
    # (2) remove harnesses forbidden by the user request or the Assistant
    forbidden = set(policy.forbidden) | set(user_forbidden)
    eligible = [h for h in candidates if h not in forbidden]

    required = set(policy.required_capabilities)

    def missing_capabilities(harness: HarnessId) -> set[str]:
        return required - _capability_names(by_id[harness])

    def eliminate_reason(harness: HarnessId) -> str:
        if harness not in by_id:
            return "no local profile"
        if not installed(by_id[harness]):
            return "not installed"
        if harness in forbidden:
            return "forbidden by policy"
        missing = missing_capabilities(harness)
        if missing:
            return f"missing required capabilities: {', '.join(sorted(missing))}"
        return "eligible"

    # (3) explicit user request: all-or-nothing, no force mode
    if requested:
        problems = [
            f"{h.value}: {eliminate_reason(h)}"
            for h in requested
            if h not in eligible or missing_capabilities(h)
        ]
        # a requested harness outside a non-empty allowed list is a hard failure
        if policy.allowed:
            allowed = set(policy.allowed)
            problems.extend(
                f"{h.value}: not in the Assistant's allowed list"
                for h in requested
                if h not in allowed
            )
        if problems:
            raise SelectionError(
                "requested harness selection is invalid: " + "; ".join(sorted(set(problems)))
            )
        return SelectionOutcome(
            chosen=list(requested),
            selection=SelectionV1(decided_by=DecidedBy.USER, candidates=sorted(candidates)),
        )

    def first_eligible(order: list[HarnessId]) -> HarnessId | None:
        for harness in order:
            if harness in eligible and not missing_capabilities(harness):
                return harness
        return None

    # (4) Assistant preference -> solo
    preferred = first_eligible(list(policy.preferred))
    if preferred is not None:
        return SelectionOutcome(
            chosen=[preferred],
            selection=SelectionV1(decided_by=DecidedBy.ASSISTANT, candidates=sorted(candidates)),
        )

    # (5) profile default -> solo
    if profiles.default_harness is not None:
        default = first_eligible([profiles.default_harness])
        if default is not None:
            return SelectionOutcome(
                chosen=[default],
                selection=SelectionV1(decided_by=DecidedBy.DEFAULT, candidates=sorted(candidates)),
            )

    # (6) nothing eligible: fail with per-harness reasons
    known = sorted(set(by_id) | set(requested), key=lambda h: h.value)
    reasons = "; ".join(f"{h.value}: {eliminate_reason(h)}" for h in known) or "no profiles"
    raise SelectionError(f"no eligible harness: {reasons}")
