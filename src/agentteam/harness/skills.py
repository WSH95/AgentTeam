"""Skill rendering into a harness discovery channel (plan section 11).

Skills are required parts: a channel that cannot deliver one fails the render
before any launch. The channel root is always AgentTeam-managed: a marker file
is written on first use and a pre-existing unmarked directory is refused so an
owner's own skills are never touched.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from agentteam.domain.assistant import ArtifactKind, RequirementLevel
from agentteam.domain.run import DegradedPartV1
from agentteam.harness.rendering import RenderError
from agentteam.harness.types import FileWriteV1, RenderContext

MARKER = ".agentteam-managed"


def write_skills(ctx: RenderContext, channel_root: Path, channel: str) -> list[FileWriteV1]:
    if (
        channel_root.exists()
        and not (channel_root / MARKER).exists()
        and any(channel_root.iterdir())
    ):
        raise RenderError(
            f"refusing to write skills into an unmanaged existing directory: {channel_root}"
        )
    channel_root.mkdir(parents=True, exist_ok=True)
    (channel_root / MARKER).write_text("written by agentteam; safe to delete\n", encoding="utf-8")

    writes: list[FileWriteV1] = []
    undeliverable: list[DegradedPartV1] = []
    for artifact in ctx.definition.artifacts:
        if artifact.kind is not ArtifactKind.AGENT_SKILL:
            continue
        source = ctx.package_root / artifact.source.vendored
        part = f"skill:{artifact.ref}"
        if not (source / "SKILL.md").is_file():
            if artifact.level is RequirementLevel.REQUIRED:
                undeliverable.append(
                    DegradedPartV1(part=part, reason="vendored skill has no SKILL.md")
                )
            continue
        destination = channel_root / artifact.ref
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source, destination)
        writes.append(FileWriteV1(path=destination / "SKILL.md", role=part, channel=channel))
    if undeliverable:
        raise RenderError(
            "required Skills cannot be delivered: "
            + ", ".join(item.part for item in undeliverable),
            undeliverable_required_parts=undeliverable,
        )
    return writes
