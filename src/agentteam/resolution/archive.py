"""V1 portable-archive contract (plan section 7).

A package is a tree of regular files only; every file must be valid UTF-8
text; paths are relative, `/`-separated, NFC-normalised, and sorted by code
point; two paths that differ only by case are rejected; file modes are
excluded; CRLF and lone CR are normalised to LF; the hash is SHA-256 over the
ordered sequence of ``(path, NUL, size, NUL, bytes)`` records. The same
package therefore hashes identically on every operating system, and every
rejection names the offending path.
"""

from __future__ import annotations

import hashlib
import os
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from agentteam.domain.bundle import AssistantRefV1, BundleManifestV1, FileEntryV1


class ArchiveContractError(ValueError):
    """A package violates the V1 archive contract; the message names the path."""


@dataclass(frozen=True)
class PackageDigest:
    """Canonical hash of a package plus the per-file entries it covers."""

    package_hash: str
    files: list[FileEntryV1]


def _normalise_newlines(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _canonical_rel_path(root: Path, path: Path) -> str:
    rel = path.relative_to(root).as_posix()
    if "\\" in rel:
        raise ArchiveContractError(f"file name contains a backslash: {rel!r}")
    return unicodedata.normalize("NFC", rel)


def hash_package(root: Path) -> PackageDigest:
    """Hash a package tree under the V1 archive contract."""
    root = Path(root)
    if not root.is_dir() or root.is_symlink():
        raise ArchiveContractError(f"package root is not a directory: {root}")

    entries: list[tuple[str, int, str, bytes]] = []  # (path, size, sha256, normalised bytes)
    for current, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        for name in dirnames:
            child = current_path / name
            if child.is_symlink():
                rel = child.relative_to(root).as_posix()
                raise ArchiveContractError(f"symlink is not allowed in a package: {rel}")
        if not dirnames and not filenames:
            rel = current_path.relative_to(root).as_posix()
            raise ArchiveContractError(f"empty directory is not allowed in a package: {rel}")
        for name in sorted(filenames):
            child = current_path / name
            rel = _canonical_rel_path(root, child)
            if child.is_symlink() or not child.is_file():
                raise ArchiveContractError(f"not a regular file: {rel}")
            raw = child.read_bytes()
            try:
                raw.decode("utf-8")
            except UnicodeDecodeError as error:
                raise ArchiveContractError(f"not valid UTF-8 text: {rel} ({error})") from None
            if b"\x00" in raw:
                raise ArchiveContractError(f"binary content is outside V1: {rel}")
            normalised = _normalise_newlines(raw)
            sha = hashlib.sha256(normalised).hexdigest()
            entries.append((rel, len(normalised), sha, normalised))

    if not entries:
        raise ArchiveContractError(f"package contains no files: {root}")

    entries.sort(key=lambda item: item[0])
    seen: dict[str, str] = {}
    folded: dict[str, str] = {}
    for rel, _, _, _ in entries:
        if rel in seen:
            raise ArchiveContractError(f"duplicate path after NFC normalisation: {rel}")
        seen[rel] = rel
        low = rel.casefold()
        if low in folded:
            raise ArchiveContractError(f"paths differ only by case: {folded[low]!r} vs {rel!r}")
        folded[low] = rel

    digest = hashlib.sha256()
    files: list[FileEntryV1] = []
    for rel, size, sha, normalised in entries:
        digest.update(rel.encode("utf-8"))
        digest.update(b"\x00")
        digest.update(str(size).encode("ascii"))
        digest.update(b"\x00")
        digest.update(normalised)
        files.append(FileEntryV1(path=rel, size=size, sha256=sha))
    return PackageDigest(package_hash=digest.hexdigest(), files=files)


def build_bundle_manifest(
    assistant: AssistantRefV1, digest: PackageDigest, created_at: datetime
) -> BundleManifestV1:
    """The M1a bundle manifest: effective hash equals the Base package hash."""
    return BundleManifestV1(
        schema_version=1,
        kind="bundle-manifest",
        assistant=assistant,
        overlay_refs=[],
        effective_definition_hash=digest.package_hash,
        files=digest.files,
        created_at=created_at,
    )
