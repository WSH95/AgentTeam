"""Shared rendering machinery for the three adapters (plan sections 9 and 11)."""

from __future__ import annotations

from pathlib import Path

from agentteam.domain.assistant import ArtifactKind, RequirementLevel
from agentteam.domain.profile import HarnessProfileV1
from agentteam.domain.run import (
    CommandV1,
    DegradedPartV1,
    LauncherPolicy,
    PlaceholderV1,
    RenderedPartV1,
)
from agentteam.harness.launcher import resolve_launcher
from agentteam.harness.types import RenderContext

# Windows CreateProcess command lines cap at 32767 chars; stay safely below.
MAX_ARGV_CHARS = 30_000


class RenderError(ValueError):
    """Rendering failed before any launch (exit 2)."""

    def __init__(
        self,
        message: str,
        *,
        undeliverable_required_parts: list[DegradedPartV1] | None = None,
    ) -> None:
        super().__init__(message)
        self.undeliverable_required_parts = undeliverable_required_parts or []


def read_instruction_text(ctx: RenderContext) -> str:
    """Persona + principles + methods in definition order — or, in synthesis
    mode, the committed synthesis instructions (a required part)."""
    if ctx.synthesis is not None:
        path = ctx.synthesis.instructions_file
        if not path.is_file():
            raise RenderError(
                f"synthesis instructions file is missing: {path}",
                undeliverable_required_parts=[
                    DegradedPartV1(part="synthesis-instructions", reason="missing instruction file")
                ],
            )
        return path.read_text(encoding="utf-8")
    parts: list[str] = []
    for rel in [ctx.definition.persona, ctx.definition.principles, ctx.definition.methods]:
        if rel is None:
            continue
        path = ctx.package_root / rel
        if not path.is_file():
            raise RenderError(
                f"required instruction file is missing: {rel}",
                undeliverable_required_parts=[
                    DegradedPartV1(part=rel, reason="missing instruction file")
                ],
            )
        parts.append(path.read_text(encoding="utf-8").strip() + "\n")
    return "\n".join(parts)


def instruction_parts(ctx: RenderContext, channel: str) -> list[RenderedPartV1]:
    """The injection-record rows for the instruction channel of one render."""
    if ctx.synthesis is not None:
        return [RenderedPartV1(part="synthesis-instructions", channel=channel)]
    parts = [
        RenderedPartV1(part="persona", channel=channel),
        RenderedPartV1(part="principles", channel=channel),
    ]
    if ctx.definition.methods is not None:
        parts.append(RenderedPartV1(part="methods", channel=channel))
    return parts


def schema_name_for(ctx: RenderContext) -> str:
    return (
        ctx.synthesis.schema_name
        if ctx.synthesis is not None
        else "normalized-review-v1.schema.json"
    )


def read_task_text(ctx: RenderContext) -> str:
    if not ctx.task_file.is_file():
        raise RenderError(f"task file does not exist: {ctx.task_file}")
    return ctx.task_file.read_text(encoding="utf-8")


def guard_argv_length(argv: list[str]) -> None:
    total = sum(len(element) + 1 for element in argv)
    if total > MAX_ARGV_CHARS:
        raise RenderError(
            f"rendered argv length {total} exceeds the {MAX_ARGV_CHARS}-char guard; "
            "shorten the definition's instruction files or use a file channel"
        )


def agent_skill_names(ctx: RenderContext) -> list[str]:
    return [
        artifact.ref
        for artifact in ctx.definition.artifacts
        if artifact.kind is ArtifactKind.AGENT_SKILL and artifact.level is RequirementLevel.REQUIRED
    ]


def build_command_record(
    *,
    ctx: RenderContext,
    profile: HarnessProfileV1,
    argv: list[str],
    policy: LauncherPolicy,
    substitutions: dict[str, str],
) -> tuple[CommandV1, list[PlaceholderV1]]:
    """Redact concrete paths/content out of argv with typed placeholders."""
    ordered = sorted(substitutions.items(), key=lambda kv: len(kv[0]), reverse=True)
    redacted: list[str] = []
    for element in argv:
        replaced = element
        for concrete, token in ordered:
            if concrete and concrete in replaced:
                replaced = replaced.replace(concrete, token)
        redacted.append(replaced)
    placeholders = [
        PlaceholderV1(token=token, role=token.strip("<>").lower().replace("_", "-"))
        for token in dict.fromkeys(substitutions.values())
    ]
    command = CommandV1(
        argv_redacted=redacted,
        launcher=f"<{profile.harness.value.upper().replace('-', '_')}>",
        launcher_policy=policy,
        cwd="<WORKSPACE>",
    )
    return command, placeholders


def resolve_for_render(
    ctx: RenderContext, argv_rest: list[str]
) -> tuple[list[str], LauncherPolicy]:
    """Resolve the launcher at render time so the policy branch is recorded."""
    from agentteam.resolution.profiles import resolve_profile_path

    executable = Path(ctx.profile.executable)
    if not executable.is_absolute() and ctx.profile_file is not None:
        executable = resolve_profile_path(ctx.profile_file, ctx.profile.executable)
    resolved = resolve_launcher(executable, argv_rest, platform=ctx.platform)
    if resolved.policy is LauncherPolicy.REFUSED:
        raise RenderError(f"launcher refused: {resolved.reason}")
    return resolved.argv, resolved.policy
