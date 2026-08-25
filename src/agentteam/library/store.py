"""Locked, atomic library for exact Assistant and Team revisions (M1c G1)."""

from __future__ import annotations

import contextlib
import hashlib
import os
import shutil
import sys
import tempfile
from collections.abc import Callable, Iterator, Mapping
from datetime import UTC, datetime
from pathlib import Path

from pydantic import ValidationError

from agentteam.domain.interactive import (
    CatalogEntryV1,
    CatalogIndexV1,
    CatalogKind,
)
from agentteam.resolution.archive import ArchiveContractError, hash_package
from agentteam.resolution.interactive import LoadedTeamTemplateV2, load_team_template_v2
from agentteam.resolution.package import PackageError, check_package, load_package
from agentteam.resolution.profiles import atomic_write_text, ensure_owner_directory


class LibraryError(ValueError):
    """A library operation failed before publishing a partial catalog change."""


def default_library_root(environ: Mapping[str, str] | None = None) -> Path:
    env = os.environ if environ is None else environ
    configured = env.get("AGENTTEAM_HOME")
    home = Path(configured).expanduser() if configured else Path.home() / ".agentteam"
    return home / "library"


class _LibraryLock:
    def __init__(self, root: Path, *, platform: str) -> None:
        self.root = root
        self.platform = platform
        self.fd: int | None = None

    def __enter__(self) -> _LibraryLock:
        if self.root.is_symlink():
            raise LibraryError(f"refusing symlinked library root: {self.root}")
        ensure_owner_directory(self.root, platform=self.platform)
        flags = os.O_CREAT | os.O_RDWR
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd: int | None = None
        try:
            fd = os.open(self.root / ".catalog.lock", flags, 0o600)
            if self.platform == "win32":
                import msvcrt

                if os.fstat(fd).st_size == 0:
                    os.write(fd, b"0")
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_LOCK, 1)  # type: ignore[attr-defined]
            else:
                import fcntl

                fcntl.flock(fd, fcntl.LOCK_EX)
            self.fd = fd
            return self
        except OSError as error:
            if fd is not None:
                os.close(fd)
            raise LibraryError(f"cannot acquire library lock: {error}") from None

    def __exit__(self, *_args: object) -> None:
        if self.fd is None:
            return
        fd, self.fd = self.fd, None
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


class LibraryStore:
    def __init__(
        self,
        root: Path,
        *,
        platform: str = sys.platform,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.root = Path(root).expanduser().absolute()
        self.platform = platform
        self.clock = clock or (lambda: datetime.now(tz=UTC))

    @property
    def index_path(self) -> Path:
        return self.root / "catalog.json"

    def import_assistant(self, source: Path) -> CatalogEntryV1:
        source = Path(source)
        try:
            package = load_package(source)
            digest = hash_package(source)
        except (PackageError, ArchiveContractError) as error:
            raise LibraryError(str(error)) from None
        problems = check_package(package, strict_content=True)
        if problems:
            raise LibraryError("invalid Assistant package: " + "; ".join(problems))

        entry = CatalogEntryV1(
            kind=CatalogKind.ASSISTANT,
            id=package.definition.id,
            version=package.definition.version,
            content_hash=digest.package_hash,
            object_path=f"objects/assistant-definition/{digest.package_hash}",
            active=True,
        )
        with self._lock():
            index = self._load_index()
            existing = self._coordinate(index, entry)
            if existing is not None:
                self._require_same(existing, entry)
                self._validate_assistant_object(existing)
                return existing
            destination = self.root / entry.object_path
            self._publish_directory(source, destination, expected=entry)
            self._publish_index(self._with_entry(index, entry))
        return entry

    def import_team(self, source: Path) -> CatalogEntryV1:
        try:
            loaded = load_team_template_v2(source)
        except (ValueError, OSError) as error:
            raise LibraryError(str(error)) from None
        content_hash = hashlib.sha256(loaded.source.encode("utf-8")).hexdigest()
        entry = CatalogEntryV1(
            kind=CatalogKind.TEAM,
            id=loaded.definition.id,
            version=loaded.definition.version,
            content_hash=content_hash,
            object_path=f"objects/team-template/{content_hash}/team.yaml",
            active=True,
        )
        with self._lock():
            index = self._load_index()
            self._require_team_refs(index, loaded)
            existing = self._coordinate(index, entry)
            if existing is not None:
                self._require_same(existing, entry)
                self._validate_team_object(existing)
                return existing
            destination = self.root / entry.object_path
            self._publish_text(loaded.source, destination, expected=entry)
            self._publish_index(self._with_entry(index, entry))
        return entry

    def entries(self, *, kind: CatalogKind | None = None) -> list[CatalogEntryV1]:
        with self._lock():
            entries = self._load_index().entries
        return [entry for entry in entries if kind is None or entry.kind is kind]

    def get(self, kind: CatalogKind, item_id: str, version: int) -> CatalogEntryV1:
        with self._lock():
            index = self._load_index()
        for entry in index.entries:
            if entry.kind is kind and entry.id == item_id and entry.version == version:
                return entry
        raise LibraryError(f"catalog entry not found: {kind.value}:{item_id}@{version}")

    def resolve(
        self,
        kind: CatalogKind,
        item_id: str,
        version: int,
        content_hash: str,
    ) -> Path:
        with self._lock():
            index = self._load_index()
            entry = next(
                (
                    candidate
                    for candidate in index.entries
                    if candidate.kind is kind
                    and candidate.id == item_id
                    and candidate.version == version
                ),
                None,
            )
            if entry is None:
                raise LibraryError(f"catalog entry not found: {kind.value}:{item_id}@{version}")
            if entry.content_hash != content_hash:
                raise LibraryError(
                    f"catalog hash mismatch for {kind.value}:{item_id}@{version}: "
                    f"expected {content_hash}, found {entry.content_hash}"
                )
            if kind is CatalogKind.ASSISTANT:
                self._validate_assistant_object(entry)
            else:
                self._validate_team_object(entry)
            return self.root / entry.object_path

    @contextlib.contextmanager
    def locked_index(self) -> Iterator[CatalogIndexV1]:
        """Hold the catalog lock for multi-step exact-byte revalidation."""
        with self._lock():
            yield self._load_index()

    def _lock(self) -> _LibraryLock:
        return _LibraryLock(self.root, platform=self.platform)

    def _load_index(self) -> CatalogIndexV1:
        if not self.index_path.exists():
            return CatalogIndexV1(
                schema_version=1,
                kind="catalog-index",
                generation=0,
                entries=[],
                updated_at=self.clock(),
            )
        if self.index_path.is_symlink() or not self.index_path.is_file():
            raise LibraryError(f"unsafe catalog index: {self.index_path}")
        try:
            return CatalogIndexV1.model_validate_json(self.index_path.read_bytes())
        except (OSError, ValidationError) as error:
            raise LibraryError(f"invalid catalog index: {error}") from None

    @staticmethod
    def _coordinate(index: CatalogIndexV1, candidate: CatalogEntryV1) -> CatalogEntryV1 | None:
        for entry in index.entries:
            if (
                entry.kind is candidate.kind
                and entry.id == candidate.id
                and entry.version == candidate.version
            ):
                return entry
        return None

    @staticmethod
    def _require_same(existing: CatalogEntryV1, candidate: CatalogEntryV1) -> None:
        if existing.content_hash != candidate.content_hash:
            raise LibraryError(
                f"immutable catalog collision at {candidate.kind.value}:"
                f"{candidate.id}@{candidate.version}: {existing.content_hash} != "
                f"{candidate.content_hash}"
            )

    def _require_team_refs(self, index: CatalogIndexV1, loaded: LoadedTeamTemplateV2) -> None:
        available = {
            (entry.id, entry.version, entry.content_hash): entry
            for entry in index.entries
            if entry.kind is CatalogKind.ASSISTANT
        }
        missing: list[str] = []
        for member in loaded.definition.members:
            coordinate = (
                member.assistant.id,
                member.assistant.version,
                member.assistant.content_hash,
            )
            entry = available.get(coordinate)
            if entry is None:
                missing.append(
                    f"{member.assistant.id}@{member.assistant.version}#"
                    f"{member.assistant.content_hash}"
                )
                continue
            self._validate_assistant_object(entry)
        if missing:
            raise LibraryError("unresolved exact Assistant references: " + ", ".join(missing))

    def _with_entry(self, index: CatalogIndexV1, candidate: CatalogEntryV1) -> CatalogIndexV1:
        entries = [
            entry.model_copy(update={"active": False})
            if entry.kind is candidate.kind and entry.id == candidate.id
            else entry
            for entry in index.entries
        ]
        entries.append(candidate)
        entries.sort(key=lambda item: (item.kind.value, item.id, item.version))
        return CatalogIndexV1(
            schema_version=1,
            kind="catalog-index",
            generation=index.generation + 1,
            entries=entries,
            updated_at=self.clock(),
        )

    def _publish_index(self, index: CatalogIndexV1) -> None:
        atomic_write_text(
            self.index_path,
            index.model_dump_json(indent=2) + "\n",
            platform=self.platform,
        )

    def _publish_directory(
        self,
        source: Path,
        destination: Path,
        *,
        expected: CatalogEntryV1,
    ) -> None:
        ensure_owner_directory(destination.parent, platform=self.platform)
        if destination.exists() or destination.is_symlink():
            self._validate_assistant_object(expected)
            return
        staging = Path(tempfile.mkdtemp(prefix=".import-", dir=destination.parent))
        try:
            shutil.rmtree(staging)
            shutil.copytree(source, staging, symlinks=True)
            self._validate_assistant_tree(staging, expected)
            self._secure_tree(staging)
            self._validate_assistant_tree(staging, expected)
            try:
                os.rename(staging, destination)
            except OSError:
                if not destination.exists() and not destination.is_symlink():
                    raise
                self._validate_assistant_object(expected)
        except (OSError, PackageError, ArchiveContractError) as error:
            raise LibraryError(f"cannot publish Assistant object: {error}") from None
        finally:
            shutil.rmtree(staging, ignore_errors=True)

    def _publish_text(
        self,
        source: str,
        destination: Path,
        *,
        expected: CatalogEntryV1,
    ) -> None:
        object_root = destination.parent
        if object_root.exists() or object_root.is_symlink():
            self._validate_team_object(expected)
            return
        ensure_owner_directory(object_root.parent, platform=self.platform)
        staging = Path(tempfile.mkdtemp(prefix=".import-", dir=object_root.parent))
        try:
            atomic_write_text(staging / destination.name, source, platform=self.platform)
            self._secure_tree(staging)
            self._validate_team_path(staging / destination.name, expected)
            try:
                os.rename(staging, object_root)
            except OSError:
                if not object_root.exists() and not object_root.is_symlink():
                    raise
                self._validate_team_object(expected)
        except OSError as error:
            raise LibraryError(f"cannot publish Team object: {error}") from None
        finally:
            shutil.rmtree(staging, ignore_errors=True)

    def _secure_tree(self, root: Path) -> None:
        if self.platform == "win32":
            return
        try:
            root.chmod(0o700)
            for path in root.rglob("*"):
                if path.is_symlink():
                    raise LibraryError(f"catalog object contains a symlink: {path}")
                path.chmod(0o700 if path.is_dir() else 0o600)
        except OSError as error:
            raise LibraryError(f"cannot secure catalog object permissions: {error}") from None

    def _validate_assistant_object(self, entry: CatalogEntryV1) -> None:
        self._validate_assistant_tree(self.root / entry.object_path, entry)

    @staticmethod
    def _validate_assistant_tree(path: Path, entry: CatalogEntryV1) -> None:
        if path.is_symlink() or not path.is_dir():
            raise LibraryError(f"catalog Assistant object is missing or unsafe: {path}")
        try:
            package = load_package(path)
            digest = hash_package(path)
        except (PackageError, ArchiveContractError) as error:
            raise LibraryError(f"invalid catalog Assistant object: {error}") from None
        problems = check_package(package, strict_content=True)
        if problems:
            raise LibraryError("invalid catalog Assistant object: " + "; ".join(problems))
        observed = (package.definition.id, package.definition.version, digest.package_hash)
        expected = (entry.id, entry.version, entry.content_hash)
        if observed != expected:
            raise LibraryError(
                f"catalog Assistant object identity mismatch: expected "
                f"{entry.id}@{entry.version}#{entry.content_hash}"
            )

    def _validate_team_object(self, entry: CatalogEntryV1) -> None:
        self._validate_team_path(self.root / entry.object_path, entry)

    @staticmethod
    def _validate_team_path(path: Path, entry: CatalogEntryV1) -> None:
        if path.is_symlink() or not path.is_file():
            raise LibraryError(f"catalog Team object is missing or unsafe: {path}")
        try:
            loaded = load_team_template_v2(path)
        except (ValueError, OSError) as error:
            raise LibraryError(f"invalid catalog Team object: {error}") from None
        observed = (
            loaded.definition.id,
            loaded.definition.version,
            hashlib.sha256(loaded.source.encode("utf-8")).hexdigest(),
        )
        expected = (entry.id, entry.version, entry.content_hash)
        if observed != expected:
            raise LibraryError(
                f"catalog Team object identity mismatch: expected "
                f"{entry.id}@{entry.version}#{entry.content_hash}"
            )
