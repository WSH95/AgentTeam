"""Per-leg workspace copies and raw-bytes target hashing (plan sections 11-12).

This hasher is deliberately not the V1 portable-archive hasher: a user
workspace may contain binary files, CRLF text, or empty directories, and
mutation detection wants byte fidelity, not normalisation. The record layout
matches the package hasher — SHA-256 over ordered `(path NUL size NUL bytes)`
records — so an empty tree hashes to the empty-input digest.

Adapter-written injection files never count as target mutation (plan section
11): exclusions are derived from the render records, and a `skill:` write
excludes its whole channel-root subtree (which also covers the
`.agentteam-managed` marker and vendored skill extras).
"""

from __future__ import annotations

import contextlib
import hashlib
import shutil
import sys
from collections.abc import Iterable
from pathlib import Path

from agentteam.harness.types import FileWriteV1

_NUL = b"\x00"


class TargetError(ValueError):
    """A workspace tree violates the target contract (symlink, occupied copy)."""


def _scan(root: Path) -> list[tuple[str, Path]]:
    """All regular files as sorted (relative posix path, absolute path) pairs."""
    entries: list[tuple[str, Path]] = []
    stack = [root]
    while stack:
        directory = stack.pop()
        for child in directory.iterdir():
            relative = child.relative_to(root).as_posix()
            if child.is_symlink():
                raise TargetError(f"symlinks are not allowed in a target tree: {relative}")
            if child.is_dir():
                stack.append(child)
            elif child.is_file():
                entries.append((relative, child))
            else:
                raise TargetError(f"not a regular file or directory: {relative}")
    entries.sort(key=lambda item: item[0])
    return entries


def _is_excluded(relative: str, exclude: frozenset[str]) -> bool:
    return any(relative == entry or relative.startswith(entry + "/") for entry in exclude)


def hash_tree(root: Path, *, exclude: frozenset[str] = frozenset()) -> str:
    digest = hashlib.sha256()
    for relative, path in _scan(root):
        if _is_excluded(relative, exclude):
            continue
        data = path.read_bytes()
        digest.update(relative.encode("utf-8"))
        digest.update(_NUL)
        digest.update(str(len(data)).encode("ascii"))
        digest.update(_NUL)
        digest.update(data)
    return digest.hexdigest()


def exclusions_for(files_written: Iterable[FileWriteV1], workspace_root: Path) -> frozenset[str]:
    """Relative-path prefixes excluded from the after-hash of one leg's workspace."""
    excluded: set[str] = set()
    for write in files_written:
        try:
            relative = write.path.relative_to(workspace_root)
        except ValueError:
            continue
        if write.role.startswith("skill:"):
            # SKILL.md sits at <channel-root>/<ref>/SKILL.md; exclude the channel root.
            excluded.add(relative.parent.parent.as_posix())
        else:
            excluded.add(relative.as_posix())
    return frozenset(excluded)


def copy_workspace(src: Path, dst: Path, *, platform: str = sys.platform) -> None:
    """Copy the requested workspace into one leg's isolated, owner-only tree.

    `copytree` mirrors the source's modes (and can loosen an existing 0700
    destination via `copystat`), so the copy is re-tightened afterwards:
    dirs 0700, files 0600 (G6.R3); win32 relies on the profile ACL.
    """
    _scan(src)  # reject symlinks and irregular entries before writing anything
    if dst.exists() and any(dst.iterdir()):
        raise TargetError(f"leg workspace destination is not empty: {dst}")
    shutil.copytree(src, dst, symlinks=False, dirs_exist_ok=True)
    if platform == "win32":
        return
    with contextlib.suppress(OSError):
        dst.chmod(0o700)
    for path in dst.rglob("*"):
        if path.is_symlink():
            continue
        with contextlib.suppress(OSError):
            path.chmod(0o700 if path.is_dir() else 0o600)
