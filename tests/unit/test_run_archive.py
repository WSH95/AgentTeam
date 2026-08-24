"""Run archive writers (plan section 13): pending-first, atomic, owner-only, manifested."""

from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from agentteam.domain.bundle import BundleManifestV1
from agentteam.domain.common import RunStatus
from agentteam.domain.request import RunRequestV1
from agentteam.domain.review import NormalizedReviewV1
from agentteam.domain.run import HarnessInvocationV1, RunRecordV1, TimingV1
from agentteam.harness.types import RawInvocationV1
from agentteam.run.archive import RunArchive
from agentteam.run.events import EventLog

Payloads = dict[str, dict[str, Any]]


def _create(
    root: Path,
    payloads: Payloads,
    **kwargs: Any,
) -> tuple[RunArchive, list[str]]:
    return RunArchive.create(
        root,
        run_record=RunRecordV1.model_validate(payloads["run-record-v1.schema.json"]),
        resolved_request=RunRequestV1.model_validate(payloads["run-request-v1.schema.json"]),
        bundle=BundleManifestV1.model_validate(payloads["bundle-manifest-v1.schema.json"]),
        **kwargs,
    )


def _raw() -> RawInvocationV1:
    return RawInvocationV1(
        exit_code=0,
        signal=None,
        stdout=b"leg stdout",
        stderr=b"leg stderr",
        output_file_text='{"final": true}',
        timed_out=False,
        duration_ms=5,
        started_at=datetime.now(tz=UTC),
        finished_at=datetime.now(tz=UTC),
    )


def test_create_writes_pending_records_before_anything_else(
    tmp_path: Path, payloads: Payloads
) -> None:
    root = tmp_path / "archive"
    archive, warnings = _create(root, payloads)
    assert warnings == []
    run = json.loads((root / "run.json").read_text(encoding="utf-8"))
    assert run["status"] == "pending"
    assert (root / "request.resolved.json").is_file()
    assert (root / "bundle-manifest.json").is_file()
    assert archive.root == root


def test_create_refuses_a_nonempty_root_but_accepts_an_empty_one(
    tmp_path: Path, payloads: Payloads
) -> None:
    occupied = tmp_path / "occupied"
    occupied.mkdir()
    (occupied / "stray.txt").write_text("here", encoding="utf-8")
    with pytest.raises(ValueError, match="not empty"):
        _create(occupied, payloads)
    empty = tmp_path / "empty"
    empty.mkdir()
    archive, _ = _create(empty, payloads)
    assert (empty / "run.json").is_file()
    assert archive.root == empty


def test_writes_are_atomic_and_leave_no_tmp_residue_on_failure(
    tmp_path: Path, payloads: Payloads, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "archive"
    archive, _ = _create(root, payloads)
    original = (root / "run.json").read_text(encoding="utf-8")
    record = RunRecordV1.model_validate(payloads["run-record-v1.schema.json"])
    finished = record.model_copy(
        update={
            "status": RunStatus.SUCCEEDED,
            "timing": TimingV1(
                started_at=record.timing.started_at,
                finished_at=datetime.now(tz=UTC),
                duration_ms=1,
            ),
        }
    )

    import os

    def boom(src: str | Path, dst: str | Path) -> None:
        raise OSError("disk detached")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(OSError, match="disk detached"):
        archive.write_run_record(finished)
    monkeypatch.undo()
    assert (root / "run.json").read_text(encoding="utf-8") == original
    assert not list(root.rglob("*.tmp"))


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permission bits")
def test_posix_archive_is_owner_only(tmp_path: Path, payloads: Payloads) -> None:
    root = tmp_path / "archive"
    _create(root, payloads)
    assert root.stat().st_mode & 0o777 == 0o700
    for path in root.rglob("*"):
        if path.is_file():
            assert path.stat().st_mode & 0o777 == 0o600, path


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permission bits")
def test_finalize_sweeps_every_descendant_owner_only(
    tmp_path: Path, payloads: Payloads, assert_owner_only_tree: Callable[[Path], None]
) -> None:
    # G6.R3: the terminal archive is recursively owner-only, including
    # `events.jsonl` and files planted in working dirs with loose umask modes
    # (as adapters and vendor processes do during a live run).
    root = tmp_path / "archive"
    archive, _ = _create(root, payloads)
    workspace, config_home, scratch = archive.working_dirs("inv-codex")
    EventLog(archive.events_path, run_id="run-test").emit("run-created")
    nested = workspace / "sub"
    nested.mkdir()
    for path, mode in (
        (nested / "copy.ts", 0o644),
        (config_home / "session.json", 0o664),
        (scratch / "prompt.md", 0o644),
    ):
        path.write_text("x", encoding="utf-8")
        path.chmod(mode)
    nested.chmod(0o755)
    archive.finalize_manifest()
    assert_owner_only_tree(root)
    assert (root / "events.jsonl").stat().st_mode & 0o777 == 0o600


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permission bits")
def test_secure_tree_on_a_win32_archive_is_a_mode_noop(tmp_path: Path, payloads: Payloads) -> None:
    root = tmp_path / "archive"
    _create(root, payloads)
    loose = root / "loose.txt"
    loose.write_text("x", encoding="utf-8")
    loose.chmod(0o644)
    RunArchive(root, platform="win32").secure_tree()
    assert loose.stat().st_mode & 0o777 == 0o644


def test_windows_platform_warns_when_root_is_outside_the_profile(
    tmp_path: Path, payloads: Payloads
) -> None:
    home = tmp_path / "Users" / "owner"
    home.mkdir(parents=True)
    outside = tmp_path / "elsewhere" / "archive"
    _, warnings = _create(outside, payloads, platform="win32", home=home)
    assert len(warnings) == 1
    assert "outside" in warnings[0]
    inside = home / "archive"
    _, no_warnings = _create(inside, payloads, platform="win32", home=home)
    assert no_warnings == []


def test_leg_and_synthesis_invocations_land_in_their_directories(
    tmp_path: Path, payloads: Payloads
) -> None:
    archive, _ = _create(tmp_path / "archive", payloads)
    invocation = HarnessInvocationV1.model_validate(payloads["harness-invocation-v1.schema.json"])
    leg = invocation.model_copy(update={"invocation_id": "inv-codex"})
    synthesis = invocation.model_copy(update={"invocation_id": "inv-synthesis"})
    archive.write_invocation(leg)
    archive.write_invocation(synthesis)
    assert (archive.root / "legs" / "inv-codex" / "invocation.json").is_file()
    assert (archive.root / "synthesis" / "inv-synthesis" / "invocation.json").is_file()


def test_raw_streams_are_written_with_verifiable_artifact_refs(
    tmp_path: Path, payloads: Payloads
) -> None:
    archive, _ = _create(tmp_path / "archive", payloads)
    refs = archive.write_raw_streams("inv-codex", _raw())
    by_role = {ref.role: ref for ref in refs}
    assert set(by_role) == {"stdout", "stderr", "output-file"}
    stdout_path = archive.root / "legs" / "inv-codex" / "stdout.raw"
    assert stdout_path.read_bytes() == b"leg stdout"
    assert by_role["stdout"].path == "legs/inv-codex/stdout.raw"
    assert by_role["stdout"].sha256 == hashlib.sha256(b"leg stdout").hexdigest()
    output_path = archive.root / "legs" / "inv-codex" / "output-file.json"
    assert output_path.read_text(encoding="utf-8") == '{"final": true}'


def test_retain_raw_streams_false_skips_streams_but_keeps_structured_output(
    tmp_path: Path, payloads: Payloads
) -> None:
    archive, _ = _create(tmp_path / "archive", payloads, retain_raw_streams=False)
    refs = archive.write_raw_streams("inv-codex", _raw())
    roles = {ref.role for ref in refs}
    assert roles == {"output-file"}
    leg = archive.root / "legs" / "inv-codex"
    assert not (leg / "stdout.raw").exists()
    assert not (leg / "stderr.raw").exists()
    assert (leg / "output-file.json").is_file()


def test_review_and_leg_text_writers_return_refs(tmp_path: Path, payloads: Payloads) -> None:
    archive, _ = _create(tmp_path / "archive", payloads)
    review = NormalizedReviewV1.model_validate(payloads["normalized-review-v1.schema.json"])
    review_ref = archive.write_review("inv-codex", review)
    assert review_ref.role == "normalized-review"
    assert review_ref.path == "legs/inv-codex/review.normalized.json"
    reloaded = NormalizedReviewV1.model_validate_json(
        (archive.root / "legs" / "inv-codex" / "review.normalized.json").read_text(encoding="utf-8")
    )
    assert reloaded == review
    task_ref = archive.write_leg_text("inv-synthesis", "task.md", "labelled reports", role="task")
    assert task_ref.path == "synthesis/inv-synthesis/task.md"
    assert (archive.root / "synthesis" / "inv-synthesis" / "task.md").read_text(
        encoding="utf-8"
    ) == "labelled reports"


def test_terminal_run_record_roundtrips(tmp_path: Path, payloads: Payloads) -> None:
    archive, _ = _create(tmp_path / "archive", payloads)
    record = RunRecordV1.model_validate(payloads["run-record-v1.schema.json"])
    finished = record.model_copy(
        update={
            "status": RunStatus.SUCCEEDED,
            "timing": TimingV1(
                started_at=record.timing.started_at,
                finished_at=datetime.now(tz=UTC),
                duration_ms=12,
            ),
        }
    )
    archive.write_run_record(finished)
    reloaded = RunRecordV1.model_validate_json(
        (archive.root / "run.json").read_text(encoding="utf-8")
    )
    assert reloaded == finished


def test_manifest_covers_records_but_not_working_dirs_and_reconstructs(
    tmp_path: Path, payloads: Payloads
) -> None:
    archive, _ = _create(tmp_path / "archive", payloads)
    invocation = HarnessInvocationV1.model_validate(payloads["harness-invocation-v1.schema.json"])
    archive.write_invocation(invocation.model_copy(update={"invocation_id": "inv-codex"}))
    workspace, config_home, scratch = archive.working_dirs("inv-codex")
    (workspace / "target.ts").write_text("export const x = 1\n", encoding="utf-8")
    (config_home / "settings.json").write_text("{}", encoding="utf-8")
    (scratch / "prompt.md").write_text("prompt", encoding="utf-8")
    archive.finalize_manifest()
    manifest = json.loads((archive.root / "manifest.sha256.json").read_text(encoding="utf-8"))
    paths = {entry["path"] for entry in manifest["files"]}
    assert "run.json" in paths
    assert "legs/inv-codex/invocation.json" in paths
    assert not any(
        "workspace" in path or "config-home" in path or "scratch" in path for path in paths
    )
    assert "manifest.sha256.json" not in paths
    assert archive.verify_manifest() == []


def test_rendered_record_on_disk_carries_no_environment_values(
    tmp_path: Path, payloads: Payloads, render_context_builder: Any
) -> None:
    from agentteam.harness.codex import CodexAdapter

    context = render_context_builder("codex", tmp_path)
    rendered = CodexAdapter().render(context)
    assert rendered.env_values  # the live invocation needs real values
    archive, _ = _create(tmp_path / "archive", payloads)
    archive.write_rendered("inv-codex", rendered)
    text = (archive.root / "legs" / "inv-codex" / "invocation.render.json").read_text(
        encoding="utf-8"
    )
    assert "env_values" not in text
    for value in rendered.env_values.values():
        assert value not in text


def test_manifest_verification_detects_tampering(tmp_path: Path, payloads: Payloads) -> None:
    archive, _ = _create(tmp_path / "archive", payloads)
    archive.finalize_manifest()
    (archive.root / "run.json").write_text(
        (archive.root / "run.json").read_text(encoding="utf-8").replace("pending", "running"),
        encoding="utf-8",
    )
    problems = archive.verify_manifest()
    assert problems
    assert any("run.json" in problem for problem in problems)
