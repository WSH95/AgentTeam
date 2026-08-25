"""Durable workspace reservation, controller lease, and observational checkpoints."""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import subprocess
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from agentteam.domain.interactive import WorkspaceCheckpointV1
from agentteam.resolution.profiles import ensure_owner_directory


class WorkspaceReservationError(RuntimeError):
    pass


class ControllerLeaseError(RuntimeError):
    pass


def canonical_workspace(path: Path) -> Path:
    candidate = Path(path).expanduser()
    if not candidate.is_dir():
        raise WorkspaceReservationError(f"workspace is not a directory: {candidate}")
    if candidate.is_symlink():
        raise WorkspaceReservationError(f"workspace root must not be a symlink: {candidate}")
    return candidate.resolve()


def _reservation_key(workspace: Path, *, platform: str) -> str:
    value = str(workspace)
    if platform == "win32":
        value = os.path.normcase(value)
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class WorkspaceReservation:
    """One crash-durable reservation for one canonical workspace path."""

    def __init__(self, root: Path, *, platform: str = sys.platform) -> None:
        self.root = Path(root)
        self.platform = platform

    def path_for(self, workspace: Path) -> Path:
        canonical = canonical_workspace(workspace)
        return self.root / f"{_reservation_key(canonical, platform=self.platform)}.json"

    def acquire(self, workspace: Path, run_id: str) -> Path:
        canonical = canonical_workspace(workspace)
        ensure_owner_directory(self.root, platform=self.platform)
        reservation = self.path_for(canonical)
        payload = (
            json.dumps(
                {"run_id": run_id, "workspace": str(canonical)},
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        created = False
        completed = False
        try:
            descriptor = os.open(reservation, flags, 0o600)
            created = True
        except FileExistsError:
            observed = self._read(reservation)
            if observed == {"run_id": run_id, "workspace": str(canonical)}:
                return reservation
            owner = observed.get("run_id", "unknown")
            raise WorkspaceReservationError(
                f"workspace is reserved by interactive run {owner}: {canonical}"
            ) from None
        try:
            with os.fdopen(descriptor, "wb") as handle:
                descriptor = -1
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
                completed = True
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            if created and not completed:
                with contextlib.suppress(OSError):
                    reservation.unlink()
        return reservation

    def release(self, workspace: Path, run_id: str) -> None:
        supplied = Path(workspace).expanduser()
        canonical = (
            Path(os.path.abspath(supplied))
            if supplied.is_absolute()
            else Path(os.path.abspath(supplied.resolve(strict=False)))
        )
        reservation = self.root / (f"{_reservation_key(canonical, platform=self.platform)}.json")
        observed = self._read(reservation)
        if observed != {"run_id": run_id, "workspace": str(canonical)}:
            raise WorkspaceReservationError(
                f"refusing to release reservation owned by {observed.get('run_id', 'unknown')}"
            )
        reservation.unlink()

    @staticmethod
    def _read(path: Path) -> dict[str, str]:
        if path.is_symlink() or not path.is_file():
            raise WorkspaceReservationError(f"unsafe or missing workspace reservation: {path}")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise WorkspaceReservationError(f"invalid workspace reservation: {error}") from None
        if not isinstance(payload, dict) or not all(
            isinstance(payload.get(name), str) for name in ("run_id", "workspace")
        ):
            raise WorkspaceReservationError("invalid workspace reservation shape")
        return {"run_id": payload["run_id"], "workspace": payload["workspace"]}


class ControllerLease:
    """An ephemeral OS lock; its file may survive, while the lock cannot."""

    def __init__(self, path: Path, *, platform: str = sys.platform) -> None:
        self.path = Path(path)
        self.platform = platform
        self.descriptor: int | None = None

    def acquire(self) -> None:
        if self.descriptor is not None:
            raise ControllerLeaseError("controller lease is already held")
        ensure_owner_directory(self.path.parent, platform=self.platform)
        flags = os.O_CREAT | os.O_RDWR
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(self.path, flags, 0o600)
        try:
            if self.platform == "win32":
                import msvcrt

                if os.fstat(descriptor).st_size == 0:
                    os.write(descriptor, b"0")
                os.lseek(descriptor, 0, os.SEEK_SET)
                msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)  # type: ignore[attr-defined]
            else:
                import fcntl

                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(descriptor)
            raise ControllerLeaseError(
                f"interactive run already has a controller: {self.path}"
            ) from None
        try:
            os.ftruncate(descriptor, 0)
            os.write(
                descriptor,
                (json.dumps({"pid": os.getpid()}, separators=(",", ":")) + "\n").encode(),
            )
            os.fsync(descriptor)
        except OSError:
            try:
                if self.platform == "win32":
                    import msvcrt

                    with contextlib.suppress(OSError):
                        os.lseek(descriptor, 0, os.SEEK_SET)
                        msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)  # type: ignore[attr-defined]
                else:
                    import fcntl

                    with contextlib.suppress(OSError):
                        fcntl.flock(descriptor, fcntl.LOCK_UN)
            finally:
                os.close(descriptor)
            raise
        self.descriptor = descriptor

    def release(self) -> None:
        descriptor, self.descriptor = self.descriptor, None
        if descriptor is None:
            return
        try:
            if self.platform == "win32":
                import msvcrt

                os.lseek(descriptor, 0, os.SEEK_SET)
                msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)  # type: ignore[attr-defined]
            else:
                import fcntl

                fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)

    def __enter__(self) -> ControllerLease:
        self.acquire()
        return self

    def __exit__(self, *_args: object) -> None:
        self.release()


def checkpoint_workspace(
    workspace: Path,
    *,
    clock: Callable[[], datetime] | None = None,
) -> WorkspaceCheckpointV1:
    root = canonical_workspace(workspace)
    head, status = _git_observation(root)
    return WorkspaceCheckpointV1(
        canonical_path=str(root),
        git_head=head,
        git_status_sha256=hashlib.sha256(status).hexdigest(),
        tree_sha256=_hash_observed_tree(root),
        observed_at=(clock or (lambda: datetime.now(tz=UTC)))(),
    )


def _git_observation(root: Path) -> tuple[str | None, bytes]:
    environment = dict(os.environ)
    environment.update({"GIT_OPTIONAL_LOCKS": "0", "LC_ALL": "C"})

    def run(*arguments: str) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            ["git", "-C", str(root), *arguments],
            env=environment,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
            timeout=10,
        )

    try:
        inside = run("rev-parse", "--is-inside-work-tree")
    except (OSError, subprocess.TimeoutExpired):
        return None, b""
    if inside.returncode != 0 or inside.stdout.strip() != b"true":
        return None, b""
    head_result = run("rev-parse", "--verify", "HEAD")
    head = head_result.stdout.decode("ascii", errors="replace").strip() or None
    status = run("status", "--porcelain=v2", "-z", "--untracked-files=all", "--ignored=no")
    if status.returncode != 0:
        return head, b""
    return head, status.stdout


def _hash_observed_tree(root: Path) -> str:
    digest = hashlib.sha256()
    stack = [root]
    while stack:
        directory = stack.pop()
        try:
            children = sorted(os.scandir(directory), key=lambda entry: entry.name)
        except OSError as error:
            digest.update(b"directory-race\0")
            digest.update(str(error.errno).encode("ascii"))
            continue
        for child in children:
            relative = Path(child.path).relative_to(root).as_posix()
            if relative == ".git" or relative.startswith(".git/"):
                continue
            digest.update(relative.encode("utf-8"))
            digest.update(b"\0")
            try:
                if child.is_symlink():
                    digest.update(b"link\0")
                    digest.update(os.readlink(child.path).encode("utf-8", errors="surrogateescape"))
                elif child.is_dir(follow_symlinks=False):
                    digest.update(b"dir\0")
                    stack.append(Path(child.path))
                elif child.is_file(follow_symlinks=False):
                    flags = os.O_RDONLY
                    if hasattr(os, "O_NOFOLLOW"):
                        flags |= os.O_NOFOLLOW
                    descriptor = os.open(child.path, flags)
                    digest.update(b"file\0")
                    try:
                        digest.update(str(os.fstat(descriptor).st_size).encode("ascii"))
                        digest.update(b"\0")
                        with os.fdopen(descriptor, "rb") as handle:
                            descriptor = -1
                            while chunk := handle.read(1024 * 1024):
                                digest.update(chunk)
                    finally:
                        if descriptor >= 0:
                            os.close(descriptor)
                else:
                    digest.update(b"other\0")
            except OSError as error:
                digest.update(b"entry-race\0")
                digest.update(str(error.errno).encode("ascii"))
    return digest.hexdigest()


def best_effort_release(lease: ControllerLease | None) -> None:
    if lease is not None:
        with contextlib.suppress(OSError):
            lease.release()
