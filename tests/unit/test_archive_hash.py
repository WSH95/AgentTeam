"""V1 portable-archive contract (plan section 7): canonical package hashing."""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

import pytest

from agentteam.domain.bundle import AssistantRefV1, BundleManifestV1
from agentteam.resolution.archive import (
    ArchiveContractError,
    build_bundle_manifest,
    hash_package,
)


def _write(root: Path, rel: str, text: str, *, newline: str | None = "") -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline=newline) as fh:
        fh.write(text)
    return path


def _tree(root: Path) -> Path:
    _write(root, "assistant.yaml", "id: x\n")
    _write(root, "persona.md", "You are careful.\n")
    _write(root, "skills/code-review/SKILL.md", "# Skill\nline\n")
    return root


def test_hash_is_deterministic_and_order_independent(tmp_path: Path) -> None:
    a = _tree(tmp_path / "a")
    b = tmp_path / "b"
    # create the same files in a different order
    _write(b, "skills/code-review/SKILL.md", "# Skill\nline\n")
    _write(b, "persona.md", "You are careful.\n")
    _write(b, "assistant.yaml", "id: x\n")
    da, db = hash_package(a), hash_package(b)
    assert da.package_hash == db.package_hash
    assert [f.path for f in da.files] == sorted(f.path for f in da.files)


def test_hash_covers_path_size_and_bytes(tmp_path: Path) -> None:
    root = _tree(tmp_path / "a")
    before = hash_package(root).package_hash
    _write(root, "persona.md", "You are careless.\n")
    assert hash_package(root).package_hash != before
    # renaming changes the hash even with identical content
    c = _tree(tmp_path / "c")
    (c / "persona.md").rename(c / "persona2.md")
    assert hash_package(c).package_hash != before


def test_crlf_and_lone_cr_normalise_to_lf(tmp_path: Path) -> None:
    lf = _tree(tmp_path / "lf")
    crlf = tmp_path / "crlf"
    _write(crlf, "assistant.yaml", "id: x\r\n")
    _write(crlf, "persona.md", "You are careful.\r")  # lone CR at end -> LF
    _write(crlf, "skills/code-review/SKILL.md", "# Skill\r\nline\r\n")
    # adjust: the lone-CR file normalises to "You are careful.\n"
    d_lf, d_crlf = hash_package(lf), hash_package(crlf)
    assert d_lf.package_hash == d_crlf.package_hash
    sizes = {f.path: f.size for f in d_crlf.files}
    assert sizes["assistant.yaml"] == len(b"id: x\n")  # normalised size, not on-disk size


def test_per_file_sha_is_over_normalised_bytes(tmp_path: Path) -> None:
    root = tmp_path / "p"
    _write(root, "a.md", "one\r\ntwo\r\n")
    digest = hash_package(root)
    expected = hashlib.sha256(b"one\ntwo\n").hexdigest()
    assert digest.files[0].sha256 == expected


def test_nfd_paths_normalise_to_nfc_and_hash_identically(tmp_path: Path) -> None:
    nfc_name = "caf\u00e9.md"  # precomposed e-acute
    nfd_name = "cafe\u0301.md"  # e + combining acute
    assert nfc_name != nfd_name
    nfc = tmp_path / "nfc"
    _write(nfc, nfc_name, "x\n")
    nfd = tmp_path / "nfd"
    _write(nfd, nfd_name, "x\n")
    d_nfc, d_nfd = hash_package(nfc), hash_package(nfd)
    assert d_nfc.package_hash == d_nfd.package_hash
    assert [f.path for f in d_nfd.files] == [nfc_name]


def test_unicode_spaces_and_deep_paths_are_accepted(tmp_path: Path) -> None:
    root = tmp_path / "p"
    _write(root, "docs/very deep/path with spaces/中文.md", "ok\n")
    digest = hash_package(root)
    assert digest.files[0].path == "docs/very deep/path with spaces/中文.md"


def test_rejects_binary_and_invalid_utf8(tmp_path: Path) -> None:
    root = tmp_path / "p"
    _write(root, "ok.md", "fine\n")
    (root / "logo.png").write_bytes(b"\x89PNG\x00\x01")
    with pytest.raises(ArchiveContractError, match=r"logo\.png"):
        hash_package(root)
    (root / "logo.png").unlink()
    (root / "bad.md").write_bytes(b"\xff\xfe invalid")
    with pytest.raises(ArchiveContractError, match=r"bad\.md"):
        hash_package(root)


def test_rejects_empty_directories(tmp_path: Path) -> None:
    root = tmp_path / "p"
    _write(root, "ok.md", "fine\n")
    (root / "empty" / "nested").mkdir(parents=True)
    with pytest.raises(ArchiveContractError, match="empty"):
        hash_package(root)


@pytest.mark.skipif(sys.platform == "win32", reason="symlink creation needs privilege on Windows")
def test_rejects_symlinks(tmp_path: Path) -> None:
    root = tmp_path / "p"
    target = _write(root, "ok.md", "fine\n")
    os.symlink(target, root / "link.md")
    with pytest.raises(ArchiveContractError, match=r"link\.md"):
        hash_package(root)


@pytest.mark.skipif(sys.platform in {"win32", "darwin"}, reason="needs a case-sensitive filesystem")
def test_rejects_case_fold_collisions(tmp_path: Path) -> None:
    root = tmp_path / "p"
    _write(root, "README.md", "a\n")
    _write(root, "readme.md", "b\n")
    with pytest.raises(ArchiveContractError, match="case"):
        hash_package(root)


@pytest.mark.skipif(sys.platform == "win32", reason="backslash is a separator on Windows")
def test_rejects_backslash_in_a_file_name(tmp_path: Path) -> None:
    root = tmp_path / "p"
    _write(root, "ok.md", "fine\n")
    (root / "bad\\name.md").write_text("x\n", encoding="utf-8")
    with pytest.raises(ArchiveContractError, match="bad"):
        hash_package(root)


def test_rejects_missing_or_fileless_root(tmp_path: Path) -> None:
    with pytest.raises(ArchiveContractError):
        hash_package(tmp_path / "nowhere")
    empty = tmp_path / "empty-root"
    empty.mkdir()
    with pytest.raises(ArchiveContractError):
        hash_package(empty)


def test_pinned_vector_for_cross_os_identity(tmp_path: Path) -> None:
    """The exact digest of a fixed tree; must match on every OS and Python."""
    root = tmp_path / "p"
    _write(root, "a.md", "alpha\n")
    _write(root, "b/c.md", "beta\r\n")
    digest = hash_package(root)
    expected = hashlib.sha256(
        b"a.md\x00" + str(len(b"alpha\n")).encode() + b"\x00alpha\n"
        b"b/c.md\x00" + str(len(b"beta\n")).encode() + b"\x00beta\n"
    ).hexdigest()
    assert digest.package_hash == expected


def test_build_bundle_manifest_passes_the_manifest_validator(tmp_path: Path) -> None:
    from datetime import UTC, datetime

    root = _tree(tmp_path / "p")
    digest = hash_package(root)
    manifest = build_bundle_manifest(
        assistant=AssistantRefV1(id="code-reviewer", version=1, package_hash=digest.package_hash),
        digest=digest,
        created_at=datetime(2026, 8, 23, tzinfo=UTC),
    )
    assert isinstance(manifest, BundleManifestV1)
    assert manifest.effective_definition_hash == digest.package_hash
    assert manifest.overlay_refs == []
