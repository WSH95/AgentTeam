"""Skill rendering into a harness discovery channel (plan section 11).

Skills are required parts: a channel that cannot deliver one fails the render
before any launch. The channel root is always AgentTeam-managed: a marker file
is written on first use and a pre-existing unmarked directory is refused so an
owner's own skills are never touched.
"""

from __future__ import annotations

import contextlib
import os
import shutil
import sys
from pathlib import Path
from types import TracebackType

from agentteam.domain.assistant import ArtifactKind, RequirementLevel
from agentteam.domain.run import DegradedPartV1
from agentteam.harness.rendering import RenderError
from agentteam.harness.types import FileWriteV1, RenderContext

MARKER = ".agentteam-managed"
LOCK_FILE = ".agentteam-skills.lock"


class ManagedSkillsLease:
    """Exclusive cross-process lease for one persistent Claude Skill root."""

    def __init__(self, config_home: Path, *, platform: str = sys.platform) -> None:
        self.config_home = config_home
        self.channel_root = config_home / "skills"
        self.platform = platform
        self._fd: int | None = None

    def acquire(self) -> ManagedSkillsLease:
        if self.config_home.is_symlink() or self.channel_root.is_symlink():
            raise RenderError(f"refusing symlinked Claude Skill home: {self.channel_root}")
        self.config_home.mkdir(parents=True, exist_ok=True)
        if self.platform != "win32":
            with contextlib.suppress(OSError):
                self.config_home.chmod(0o700)
        flags = os.O_CREAT | os.O_RDWR
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        lock_path = self.config_home / LOCK_FILE
        fd: int | None = None
        try:
            fd = os.open(lock_path, flags, 0o600)
            if self.platform == "win32":
                import msvcrt

                if os.fstat(fd).st_size == 0:
                    os.write(fd, b"0")
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_LOCK, 1)  # type: ignore[attr-defined]
            else:
                import fcntl

                fcntl.flock(fd, fcntl.LOCK_EX)
            self._fd = fd
        except OSError as error:
            if fd is not None:
                with contextlib.suppress(OSError):
                    os.close(fd)
            raise RenderError(f"cannot acquire Claude Skill lease: {error}") from None
        try:
            _require_managed_or_empty(self.channel_root)
            _mark_managed(self.channel_root, platform=self.platform)
        except BaseException:
            self.close()
            raise
        return self

    def close(self) -> None:
        if self._fd is None:
            return
        try:
            _clean_managed(self.channel_root)
        finally:
            fd, self._fd = self._fd, None
            try:
                if self.platform == "win32":
                    import msvcrt

                    os.lseek(fd, 0, os.SEEK_SET)
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)  # type: ignore[attr-defined]
                else:
                    import fcntl

                    fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)

    def __enter__(self) -> ManagedSkillsLease:
        return self.acquire()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()


def _require_managed_or_empty(channel_root: Path) -> None:
    marker = channel_root / MARKER
    marked = marker.is_file() and not marker.is_symlink()
    if channel_root.exists() and not marked:
        try:
            occupied = any(channel_root.iterdir())
        except OSError as error:
            raise RenderError(f"cannot inspect Claude Skill directory: {error}") from None
        if occupied:
            raise RenderError(
                f"refusing to write skills into an unmanaged existing directory: {channel_root}"
            )


def _mark_managed(channel_root: Path, *, platform: str) -> None:
    channel_root.mkdir(parents=True, exist_ok=True)
    if platform != "win32":
        with contextlib.suppress(OSError):
            channel_root.chmod(0o700)
    marker = channel_root / MARKER
    if marker.is_file() and not marker.is_symlink():
        return
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(marker, flags, 0o600)
    try:
        os.write(fd, b"written by agentteam; safe to delete\n")
        os.fsync(fd)
        if platform != "win32":
            os.fchmod(fd, 0o600)
    finally:
        os.close(fd)


def _clean_managed(channel_root: Path) -> None:
    """Remove only content beneath a directory carrying our ownership marker."""
    marker = channel_root / MARKER
    if not channel_root.is_dir() or not marker.is_file() or marker.is_symlink():
        return
    for child in channel_root.iterdir():
        if child.name == MARKER:
            continue
        if child.is_symlink() or child.is_file():
            child.unlink()
        elif child.is_dir():
            shutil.rmtree(child)


def write_skills(ctx: RenderContext, channel_root: Path, channel: str) -> list[FileWriteV1]:
    skill_artifacts = [
        artifact
        for artifact in ctx.definition.artifacts
        if artifact.kind is ArtifactKind.AGENT_SKILL
    ]
    # A Skill-free Assistant has nothing to publish into this discovery
    # channel. Avoid creating an ownership marker that would otherwise become
    # an undeclared renderer write inside a member's target workspace.
    if not skill_artifacts:
        return []
    if channel_root.is_symlink():
        raise RenderError(f"refusing symlinked Skill directory: {channel_root}")
    _require_managed_or_empty(channel_root)
    channel_root.mkdir(parents=True, exist_ok=True)
    (channel_root / MARKER).write_text("written by agentteam; safe to delete\n", encoding="utf-8")

    writes: list[FileWriteV1] = []
    undeliverable: list[DegradedPartV1] = []
    for artifact in skill_artifacts:
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
            if destination.is_symlink() or destination.is_file():
                destination.unlink()
            else:
                shutil.rmtree(destination)
        shutil.copytree(source, destination)
        writes.append(FileWriteV1(path=destination / "SKILL.md", role=part, channel=channel))
    if ctx.platform != "win32":
        # Owner-only at write time (G6.R3): the config-home channel lives in
        # the persistent profile home, outside any archive finalize sweep.
        with contextlib.suppress(OSError):
            channel_root.chmod(0o700)
        for path in channel_root.rglob("*"):
            if path.is_symlink():
                continue
            with contextlib.suppress(OSError):
                path.chmod(0o700 if path.is_dir() else 0o600)
    if undeliverable:
        raise RenderError(
            "required Skills cannot be delivered: "
            + ", ".join(item.part for item in undeliverable),
            undeliverable_required_parts=undeliverable,
        )
    return writes
