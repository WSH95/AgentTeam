"""Raw-bytes target tree hashing, injection exclusions, and leg copies (plan sections 11-12).

The target hasher is deliberately not the V1 package hasher: user workspaces
may hold binary files, CRLF text, or empty subdirectories, and mutation
detection wants byte fidelity, not normalisation.
"""

from __future__ import annotations

import hashlib
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from agentteam.harness.types import FileWriteV1
from agentteam.run.workspace import TargetError, copy_workspace, exclusions_for, hash_tree

EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()


def _write(root: Path, rel: str, data: bytes) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def test_identical_trees_hash_equal_regardless_of_creation_order(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    _write(first, "src/a.ts", b"alpha")
    _write(first, "src/b.ts", b"beta")
    _write(first, "README.md", b"readme")
    _write(second, "README.md", b"readme")
    _write(second, "src/b.ts", b"beta")
    _write(second, "src/a.ts", b"alpha")
    assert hash_tree(first) == hash_tree(second)


def test_single_byte_change_changes_hash(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    _write(first, "a.txt", b"content")
    _write(second, "a.txt", b"contenT")
    assert hash_tree(first) != hash_tree(second)


def test_same_content_under_a_different_name_changes_hash(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    _write(first, "a.txt", b"content")
    _write(second, "b.txt", b"content")
    assert hash_tree(first) != hash_tree(second)


def test_crlf_and_lf_are_different_bytes(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    _write(first, "a.txt", b"line one\nline two\n")
    _write(second, "a.txt", b"line one\r\nline two\r\n")
    assert hash_tree(first) != hash_tree(second)


def test_binary_content_is_accepted(tmp_path: Path) -> None:
    root = tmp_path / "tree"
    _write(root, "blob.bin", b"\x00\x01\xff\xfePNG\x00")
    assert len(hash_tree(root)) == 64


def test_empty_tree_hashes_to_the_empty_input_digest(tmp_path: Path) -> None:
    root = tmp_path / "empty"
    root.mkdir()
    assert hash_tree(root) == EMPTY_SHA256


def test_nested_empty_directories_are_ignored(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    _write(first, "a.txt", b"content")
    _write(second, "a.txt", b"content")
    (second / "empty" / "nested").mkdir(parents=True)
    assert hash_tree(first) == hash_tree(second)


@pytest.mark.skipif(sys.platform == "win32", reason="symlink creation needs privilege on Windows")
def test_symlink_is_rejected_naming_the_path(tmp_path: Path) -> None:
    root = tmp_path / "tree"
    _write(root, "a.txt", b"content")
    (root / "link.txt").symlink_to(root / "a.txt")
    with pytest.raises(TargetError, match=r"link\.txt"):
        hash_tree(root)


def _codex_shaped_writes(workspace: Path) -> list[FileWriteV1]:
    return [
        FileWriteV1(
            path=workspace / "AGENTS.md",
            role="instructions",
            channel="workspace-agents-md",
        ),
        FileWriteV1(
            path=workspace / ".agents" / "skills" / "code-review" / "SKILL.md",
            role="skill:code-review",
            channel="workspace-skills",
        ),
    ]


def test_exclusions_cover_recorded_files_and_whole_skill_channel_roots(tmp_path: Path) -> None:
    pristine = tmp_path / "pristine"
    _write(pristine, "src/a.ts", b"alpha")
    workspace = tmp_path / "workspace"
    _write(workspace, "src/a.ts", b"alpha")
    _write(workspace, "AGENTS.md", b"instructions")
    _write(workspace, ".agents/skills/code-review/SKILL.md", b"skill body")
    _write(workspace, ".agents/skills/code-review/reference.md", b"vendored extra")
    _write(workspace, ".agents/skills/.agentteam-managed", b"marker\n")
    exclude = exclusions_for(_codex_shaped_writes(workspace), workspace)
    assert hash_tree(workspace, exclude=exclude) == hash_tree(pristine)


def test_unrecorded_extra_file_still_breaks_equality(tmp_path: Path) -> None:
    pristine = tmp_path / "pristine"
    _write(pristine, "src/a.ts", b"alpha")
    workspace = tmp_path / "workspace"
    _write(workspace, "src/a.ts", b"alpha")
    _write(workspace, "AGENTS.md", b"instructions")
    _write(workspace, "stray-output.txt", b"the harness wrote this")
    exclude = exclusions_for(_codex_shaped_writes(workspace), workspace)
    assert hash_tree(workspace, exclude=exclude) != hash_tree(pristine)


def test_exclusions_ignore_writes_outside_the_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write(workspace, "src/a.ts", b"alpha")
    elsewhere = FileWriteV1(
        path=tmp_path / "scratch" / "prompt.md",
        role="prompt",
        channel="prompt-file",
    )
    assert exclusions_for([elsewhere], workspace) == frozenset()


def test_copy_workspace_is_faithful(tmp_path: Path) -> None:
    src = tmp_path / "src"
    _write(src, "src/a.ts", b"alpha")
    _write(src, "nested/deep/blob.bin", b"\x00\xff")
    dst = tmp_path / "dst"
    copy_workspace(src, dst)
    assert hash_tree(dst) == hash_tree(src)


def test_copy_workspace_accepts_an_existing_empty_destination(tmp_path: Path) -> None:
    src = tmp_path / "src"
    _write(src, "a.txt", b"content")
    dst = tmp_path / "dst"
    dst.mkdir()
    copy_workspace(src, dst)
    assert hash_tree(dst) == hash_tree(src)


def test_copy_workspace_refuses_a_nonempty_destination(tmp_path: Path) -> None:
    src = tmp_path / "src"
    _write(src, "a.txt", b"content")
    dst = tmp_path / "dst"
    _write(dst, "existing.txt", b"already here")
    with pytest.raises(TargetError, match="not empty"):
        copy_workspace(src, dst)


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permission bits")
def test_copy_workspace_sets_owner_only_modes(
    tmp_path: Path, assert_owner_only_tree: Callable[[Path], None]
) -> None:
    # G6.R3: leg copies are owner-only regardless of the source tree's modes.
    src = tmp_path / "src"
    _write(src, "open/a.ts", b"alpha")
    (src / "open").chmod(0o755)
    (src / "open" / "a.ts").chmod(0o644)
    dst = tmp_path / "dst"
    copy_workspace(src, dst)
    assert_owner_only_tree(dst)


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permission bits")
def test_copy_workspace_win32_platform_skips_mode_enforcement(tmp_path: Path) -> None:
    # The win32 branch relies on the profile ACL; exercised here on POSIX so
    # every CI leg covers it without platform monkeypatching.
    src = tmp_path / "src"
    _write(src, "a.ts", b"alpha")
    (src / "a.ts").chmod(0o644)
    dst = tmp_path / "dst"
    copy_workspace(src, dst, platform="win32")
    assert (dst / "a.ts").stat().st_mode & 0o777 == 0o644  # copystat preserved


@pytest.mark.skipif(sys.platform == "win32", reason="symlink creation needs privilege on Windows")
def test_copy_workspace_rejects_a_symlink_in_the_source(tmp_path: Path) -> None:
    src = tmp_path / "src"
    _write(src, "a.txt", b"content")
    (src / "link.txt").symlink_to(src / "a.txt")
    dst = tmp_path / "dst"
    with pytest.raises(TargetError, match=r"link\.txt"):
        copy_workspace(src, dst)
    assert not dst.exists() or not any(dst.iterdir())
