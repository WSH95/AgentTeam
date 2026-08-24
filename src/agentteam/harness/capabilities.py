"""Probe-backed capability names and fixed adapter selection ladders.

Capability rows are profile data, but their meanings and the order in which
adapters may use alternative delivery channels are part of the runner
contract. A live channel is selectable only after a G5 probe marked it
verified for the CLI version observed by preflight. Render-only callers pass
no observed version and consume synthetic verified rows without making a live
readiness claim.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from agentteam.domain.common import HarnessId
from agentteam.domain.profile import CapabilityRecordV1, HarnessProfileV1, Verification

CLAUDE_INSTRUCTION_LADDER = (
    "append-system-prompt-file",
    "append-system-prompt",
)
CLAUDE_SKILL_LADDER = (
    "skills-config-home",
    "skills-plugin-dir",
    "skills-workspace",
)

CODEX_INSTRUCTION_LADDER = (
    "instructions-model-instructions-file",
    "instructions-developer-instructions",
    "instructions-workspace-agents-md",
)
CODEX_SKILL_LADDER = ("skills-workspace",)

GROK_INSTRUCTION_LADDER = (
    "instructions-rules",
    "instructions-system-prompt-override",
)
GROK_SKILL_LADDER = (
    "skills-workspace-grok",
    "skills-workspace-agents",
)
GROK_OUTPUT_LADDER = (
    "structured-output-field",
    "structured-output-text",
)


@dataclass(frozen=True)
class ReadinessRequirements:
    """Capabilities every live invocation needs, plus alternative ladders."""

    required: tuple[str, ...]
    one_of: tuple[tuple[str, ...], ...]


def capability_is_verified(
    profile: HarnessProfileV1,
    name: str,
    *,
    cli_version: str | None,
) -> bool:
    for row in profile.capabilities:
        if row.name != name or row.verification is not Verification.VERIFIED:
            continue
        if cli_version is None:
            return True
        return row.cli_version == cli_version and row.verified_at is not None
    return False


def select_verified(
    profile: HarnessProfileV1,
    ladder: Iterable[str],
    *,
    cli_version: str | None,
) -> str | None:
    """Return the first current-verified channel in immutable preference order."""
    return next(
        (name for name in ladder if capability_is_verified(profile, name, cli_version=cli_version)),
        None,
    )


def readiness_requirements(harness: HarnessId, *, needs_skills: bool) -> ReadinessRequirements:
    if harness is HarnessId.CLAUDE_CODE:
        claude_groups: list[tuple[str, ...]] = [CLAUDE_INSTRUCTION_LADDER]
        if needs_skills:
            claude_groups.append(CLAUDE_SKILL_LADDER)
        return ReadinessRequirements(
            required=("headless-json", "structured-output", "native-auth"),
            one_of=tuple(claude_groups),
        )
    if harness is HarnessId.CODEX:
        codex_groups: list[tuple[str, ...]] = [CODEX_INSTRUCTION_LADDER]
        if needs_skills:
            codex_groups.append(CODEX_SKILL_LADDER)
        return ReadinessRequirements(
            required=(
                "headless-jsonl",
                "structured-output",
                "output-last-message",
                "native-auth",
            ),
            one_of=tuple(codex_groups),
        )
    grok_groups: list[tuple[str, ...]] = [GROK_INSTRUCTION_LADDER, GROK_OUTPUT_LADDER]
    if needs_skills:
        grok_groups.append(GROK_SKILL_LADDER)
    return ReadinessRequirements(
        required=("headless-json", "structured-output", "prompt-file", "native-auth"),
        one_of=tuple(grok_groups),
    )


def readiness_problems(
    profile: HarnessProfileV1,
    *,
    cli_version: str | None,
    needs_skills: bool,
) -> list[str]:
    """Explain incomplete or version-stale live readiness without changing data."""
    requirements = readiness_requirements(profile.harness, needs_skills=needs_skills)
    by_name = {row.name: row for row in profile.capabilities}
    problems: list[str] = []

    def current(name: str) -> bool:
        row = by_name.get(name)
        if row is None:
            return False
        if row.verification is not Verification.VERIFIED:
            return False
        if row.cli_version is None or row.verified_at is None:
            return False
        return cli_version is not None and row.cli_version == cli_version

    for name in requirements.required:
        if not current(name):
            problems.append(_row_problem(name, by_name.get(name), cli_version))
    for ladder in requirements.one_of:
        if not any(current(name) for name in ladder):
            details = ", ".join(ladder)
            problems.append(f"no current verified channel in [{details}]")
    return problems


def _row_problem(name: str, row: CapabilityRecordV1 | None, cli_version: str | None) -> str:
    if row is None:
        return f"missing capability row {name}"
    verification = row.verification
    recorded_version = row.cli_version
    verified_at = row.verified_at
    if verification is not Verification.VERIFIED:
        return f"capability {name} is {verification.value}"
    if recorded_version is None or verified_at is None:
        return f"capability {name} has never been fully assessed"
    if cli_version is None:
        return f"capability {name} cannot be matched because --version failed"
    return f"capability {name} is stale ({recorded_version!r} != {cli_version!r})"
