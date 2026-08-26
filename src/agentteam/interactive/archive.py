"""Owner-only durable archive for interactive runs and sanitized audit export."""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeVar

from pydantic import ValidationError

from agentteam.domain.common import RecordModel
from agentteam.domain.interactive import (
    CompletionProposalV1,
    ControlReceiptV1,
    ControlRequestV1,
    InteractiveRunRecordV1,
    InteractiveRunRequestV1,
    MemberSessionV1,
    RunEventV1,
    TurnRecordV1,
    WorkItemV1,
    WorkspaceCheckpointV1,
)
from agentteam.execution.protocol import ProviderEvent
from agentteam.resolution.profiles import atomic_write_text, ensure_owner_directory


class InteractiveArchiveError(RuntimeError):
    pass


_WORKSPACE_PLACEHOLDER = "<WORKSPACE>"
_OUTPUT_DIR_PLACEHOLDER = "<OUTPUT_DIR>"
_PROVIDER_SESSION_PLACEHOLDER = "<PROVIDER_SESSION>"
_ABSOLUTE_PATH_TEXT = re.compile(
    r"(?<![A-Za-z0-9._:/\\-])/(?!/)[^\s\"'<>]*"
    r"|(?<![A-Za-z0-9._-])[A-Za-z]:[\\/]+[^\s\"'<>]+"
    r"|(?<![A-Za-z0-9._-])\\{2,}[^\s\"'<>]+"
)
_LOCAL_FILE_URI_TEXT = re.compile(r"(?i)(?<![A-Za-z0-9+.-])file:")


ModelT = TypeVar("ModelT", bound=RecordModel)


class ExportManifestEntry(RecordModel):
    path: str
    sha256: str


class ExportManifest(RecordModel):
    files: list[ExportManifestEntry]


class InteractiveArchive:
    def __init__(
        self,
        root: Path,
        *,
        platform: str = sys.platform,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.root = Path(root)
        self.platform = platform
        self.clock = clock or (lambda: datetime.now(tz=UTC))
        self._event_sequence = self._last_event_sequence()

    @classmethod
    def create(
        cls,
        root: Path,
        *,
        request: InteractiveRunRequestV1,
        record: InteractiveRunRecordV1,
        team_source: bytes,
        assistant_sources: Mapping[str, Path],
        platform: str = sys.platform,
        clock: Callable[[], datetime] | None = None,
    ) -> InteractiveArchive:
        root = Path(root)
        if root.exists() and (not root.is_dir() or root.is_symlink() or any(root.iterdir())):
            raise InteractiveArchiveError(f"interactive archive is not empty and safe: {root}")
        ensure_owner_directory(root, platform=platform)
        archive = cls(root, platform=platform, clock=clock)
        archive._write_bytes("definitions/team.yaml", team_source)
        for member, source in assistant_sources.items():
            archive._snapshot_tree(source, Path("definitions/assistants") / member)
        archive.write_request(request)
        archive.write_run(record)
        archive.write_checkpoint("initial", "observed", record.initial_checkpoint)
        archive._write_bytes("events.jsonl", b"")
        return archive

    @property
    def run_path(self) -> Path:
        return self.root / "run.json"

    def write_request(self, request: InteractiveRunRequestV1) -> None:
        self._write_model("request.resolved.json", request)

    def load_request(self) -> InteractiveRunRequestV1:
        return self._load_model("request.resolved.json", InteractiveRunRequestV1)

    def write_run(self, record: InteractiveRunRecordV1) -> None:
        self._write_model("run.json", record)

    def load_run(self) -> InteractiveRunRecordV1:
        return self._load_model("run.json", InteractiveRunRecordV1)

    def write_session(self, session: MemberSessionV1) -> None:
        self._write_model(f"sessions/{session.session_id}.json", session)

    def load_session(self, session_id: str) -> MemberSessionV1:
        return self._load_model(f"sessions/{session_id}.json", MemberSessionV1)

    def write_turn(self, turn: TurnRecordV1) -> None:
        self._write_model(f"turns/{turn.turn_id}.json", turn)

    def load_turn(self, turn_id: str) -> TurnRecordV1:
        return self._load_model(f"turns/{turn_id}.json", TurnRecordV1)

    def write_checkpoint(
        self,
        turn_id: str,
        stage: str,
        checkpoint: WorkspaceCheckpointV1,
    ) -> None:
        if stage not in {"before", "after", "observed", "final"}:
            raise InteractiveArchiveError(f"invalid checkpoint stage: {stage}")
        self._write_model(f"checkpoints/{turn_id}.{stage}.json", checkpoint)

    def latest_checkpoint(self) -> WorkspaceCheckpointV1:
        directory = self.root / "checkpoints"
        if directory.is_symlink() or not directory.is_dir():
            return self.load_run().initial_checkpoint
        record = self.load_run()
        candidates = [directory / "run.final.json"]
        candidates.extend(directory / f"{turn_id}.after.json" for turn_id in reversed(record.turns))
        candidates.append(directory / "initial.observed.json")
        for path in candidates:
            if path.is_file() and not path.is_symlink():
                return self._load_model(
                    path.relative_to(self.root).as_posix(),
                    WorkspaceCheckpointV1,
                )
        return record.initial_checkpoint

    def write_work_item(self, item: WorkItemV1) -> None:
        self._write_model(f"work-items/{item.id}.json", item)

    def load_work_item(self, item_id: str) -> WorkItemV1:
        return self._load_model(f"work-items/{item_id}.json", WorkItemV1)

    def list_work_items(self) -> list[WorkItemV1]:
        return self._load_directory("work-items", WorkItemV1)

    def write_control_request(self, request: ControlRequestV1) -> None:
        self._write_model(f"controls/requests/{request.request_id}.json", request)

    def write_control_receipt(self, receipt: ControlReceiptV1) -> None:
        self._write_model(f"controls/receipts/{receipt.request_id}.json", receipt)

    def load_control_receipt(self, request_id: str) -> ControlReceiptV1:
        return self._load_model(f"controls/receipts/{request_id}.json", ControlReceiptV1)

    def load_control_request(self, request_id: str) -> ControlRequestV1:
        return self._load_model(f"controls/requests/{request_id}.json", ControlRequestV1)

    def write_proposal(self, proposal: CompletionProposalV1) -> None:
        self._write_model(f"completion/{proposal.proposal_id}.json", proposal)

    def load_proposal(self, proposal_id: str) -> CompletionProposalV1:
        return self._load_model(f"completion/{proposal_id}.json", CompletionProposalV1)

    def list_proposals(self) -> list[CompletionProposalV1]:
        return self._load_directory("completion", CompletionProposalV1)

    def write_state_summary(self, member: str, generation: int, summary: str) -> None:
        self._write_bytes(
            f"summaries/{member}-g{generation}.txt",
            summary.encode("utf-8"),
        )

    def write_launch_record(self, member: str, payload: Mapping[str, Any]) -> None:
        data = (
            json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
        ).encode("utf-8")
        self._write_bytes(f"launch/{member}.json", data)

    def load_launch_record(self, member: str) -> dict[str, Any]:
        path = self.root / "launch" / f"{member}.json"
        if path.is_symlink() or not path.is_file():
            raise InteractiveArchiveError(f"missing or unsafe launch record: {path}")
        try:
            payload = json.loads(path.read_bytes())
        except (OSError, json.JSONDecodeError) as error:
            raise InteractiveArchiveError(f"invalid launch record for {member}: {error}") from None
        if not isinstance(payload, dict) or not all(isinstance(key, str) for key in payload):
            raise InteractiveArchiveError(f"invalid launch record shape for {member}")
        return payload

    def write_workspace_reservation(self, *, run_id: str, workspace: Path) -> None:
        payload = (
            json.dumps(
                {"run_id": run_id, "workspace": str(workspace)},
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
        self._write_bytes("reservation.json", payload)

    def append_provider_event(self, turn_id: str, event: ProviderEvent) -> None:
        payload = {
            "event": event.event,
            "text": event.text,
            "data": dict(event.data),
        }
        self._append_json_line(f"turns/{turn_id}.events.jsonl", payload)

    def append_event(
        self,
        run_id: str,
        event: str,
        *,
        correlation_id: str | None = None,
        data: Mapping[str, str | int | bool | None] | None = None,
    ) -> RunEventV1:
        sequence = self._event_sequence + 1
        record = RunEventV1(
            schema_version=1,
            kind="run-event",
            run_id=run_id,
            sequence=sequence,
            event=event,
            occurred_at=self.clock(),
            correlation_id=correlation_id,
            data=dict(data or {}),
        )
        self._append_json_line("events.jsonl", record.model_dump(mode="json"))
        self._event_sequence = sequence
        return record

    def event_sequence(self, event: str, correlation_id: str) -> int:
        path = self.root / "events.jsonl"
        matches = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line:
                continue
            record = RunEventV1.model_validate_json(line)
            if record.event == event and record.correlation_id == correlation_id:
                matches.append(record.sequence)
        if not matches:
            raise InteractiveArchiveError(
                f"run event not found: {event} correlated to {correlation_id}"
            )
        return matches[-1]

    def finalize_manifest(self) -> None:
        unsafe = self._unsafe_entries()
        if unsafe:
            raise InteractiveArchiveError(
                "interactive archive contains unsafe entries: " + "; ".join(unsafe)
            )
        self._secure_tree()
        self._write_model("manifest.sha256.json", self._manifest())

    def verify_manifest(self) -> list[str]:
        stored = self._load_model("manifest.sha256.json", ExportManifest)
        current = {entry.path: entry.sha256 for entry in self._manifest().files}
        expected = {entry.path: entry.sha256 for entry in stored.files}
        problems = [f"missing: {path}" for path in sorted(expected.keys() - current.keys())]
        problems += [f"extra: {path}" for path in sorted(current.keys() - expected.keys())]
        problems += [
            f"changed: {path}"
            for path in sorted(current.keys() & expected.keys())
            if current[path] != expected[path]
        ]
        return [*problems, *self._unsafe_entries()]

    def export_audit(self, destination: Path) -> Path:
        """Atomically export sanitized records/definitions without local runtime facts."""
        if self.root.is_symlink() or not self.root.is_dir():
            raise InteractiveArchiveError(f"interactive archive root is unsafe: {self.root}")
        record = self.load_run()
        if record.phase.value != "closed":
            raise InteractiveArchiveError("only a closed interactive run can be exported")
        manifest_problems = self.verify_manifest()
        if manifest_problems:
            raise InteractiveArchiveError(
                "interactive archive manifest is invalid: " + "; ".join(manifest_problems)
            )
        destination = Path(destination)
        source_root = self.root.resolve()
        resolved_destination = destination.resolve(strict=False)
        if resolved_destination == source_root or source_root in resolved_destination.parents:
            raise InteractiveArchiveError("audit export destination cannot be inside its source")
        if destination.exists() and (
            not destination.is_dir() or destination.is_symlink() or any(destination.iterdir())
        ):
            raise InteractiveArchiveError(
                f"export destination is not empty and safe: {destination}"
            )
        ensure_owner_directory(destination.parent, platform=self.platform)
        staging = Path(
            tempfile.mkdtemp(
                prefix=f".{destination.name or 'audit-export'}-",
                dir=destination.parent,
            )
        )
        removed_empty_destination = False
        try:
            for source in self._record_files():
                relative = source.relative_to(self.root)
                if self._excluded_from_export(relative):
                    continue
                target = staging / relative
                ensure_owner_directory(target.parent, platform=self.platform)
                target.write_bytes(self._sanitized_export_bytes(relative, source))
                self._chmod_file(target)
            exported = InteractiveArchive(staging, platform=self.platform, clock=self.clock)
            problems = scan_interactive_audit_export(staging)
            if problems:
                raise InteractiveArchiveError(
                    "interactive audit export failed its safety scan: " + "; ".join(problems)
                )
            exported.finalize_manifest()
            problems = scan_interactive_audit_export(staging)
            if problems:
                raise InteractiveArchiveError(
                    "interactive audit export failed its final safety scan: " + "; ".join(problems)
                )
            if destination.exists():
                if (
                    destination.is_symlink()
                    or not destination.is_dir()
                    or any(destination.iterdir())
                ):
                    raise InteractiveArchiveError(
                        f"export destination changed while exporting: {destination}"
                    )
                destination.rmdir()
                removed_empty_destination = True
            os.rename(staging, destination)
            return destination
        except BaseException:
            shutil.rmtree(staging, ignore_errors=True)
            if removed_empty_destination and not destination.exists():
                ensure_owner_directory(destination, platform=self.platform)
            raise

    @staticmethod
    def _excluded_from_export(relative: Path) -> bool:
        return (
            relative.parts[0] in {"runtime", "launch", "summaries"}
            or relative.name in {"controller.lock", "manifest.sha256.json"}
            or relative.name.endswith(".events.jsonl")
        )

    def _sanitized_export_bytes(self, relative: Path, source: Path) -> bytes:
        name = relative.as_posix()
        if name == "request.resolved.json":
            request = self._load_model(name, InteractiveRunRequestV1)
            request = request.model_copy(
                update={
                    "workspace": _WORKSPACE_PLACEHOLDER,
                    "output_dir": (
                        _OUTPUT_DIR_PLACEHOLDER if request.output_dir is not None else None
                    ),
                }
            )
            return (request.model_dump_json(indent=2) + "\n").encode()
        if name == "run.json":
            record = self._load_model(name, InteractiveRunRecordV1)
            initial = record.initial_checkpoint.model_copy(
                update={"canonical_path": _WORKSPACE_PLACEHOLDER}
            )
            final = (
                None
                if record.final_checkpoint is None
                else record.final_checkpoint.model_copy(
                    update={"canonical_path": _WORKSPACE_PLACEHOLDER}
                )
            )
            record = record.model_copy(
                update={
                    "workspace": _WORKSPACE_PLACEHOLDER,
                    "initial_checkpoint": initial,
                    "final_checkpoint": final,
                }
            )
            return (record.model_dump_json(indent=2) + "\n").encode()
        if relative.parts[0] == "checkpoints" and relative.suffix == ".json":
            checkpoint = self._load_model(name, WorkspaceCheckpointV1).model_copy(
                update={"canonical_path": _WORKSPACE_PLACEHOLDER}
            )
            return (checkpoint.model_dump_json(indent=2) + "\n").encode()
        if relative.parts[0] == "sessions" and relative.suffix == ".json":
            session = self._load_model(name, MemberSessionV1).model_copy(
                update={"provider_session_ref": _PROVIDER_SESSION_PLACEHOLDER}
            )
            return (session.model_dump_json(indent=2) + "\n").encode()
        if name == "reservation.json":
            try:
                reservation = json.loads(source.read_bytes())
            except (OSError, json.JSONDecodeError) as error:
                raise InteractiveArchiveError(f"invalid reservation record: {error}") from None
            if not isinstance(reservation, dict) or not isinstance(
                reservation.get("workspace"), str
            ):
                raise InteractiveArchiveError("invalid reservation record shape")
            reservation["workspace"] = _WORKSPACE_PLACEHOLDER
            return (json.dumps(reservation, sort_keys=True, separators=(",", ":")) + "\n").encode()
        return source.read_bytes()

    def _manifest(self) -> ExportManifest:
        entries = []
        for path in self._record_files():
            relative = path.relative_to(self.root).as_posix()
            if relative in {"controller.lock", "manifest.sha256.json"}:
                continue
            entries.append(
                ExportManifestEntry(
                    path=relative,
                    sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                )
            )
        return ExportManifest(files=entries)

    def _record_files(self) -> list[Path]:
        return sorted(
            path for path in self.root.rglob("*") if path.is_file() and not path.is_symlink()
        )

    def _unsafe_entries(self) -> list[str]:
        problems: list[str] = []
        for path in self.root.rglob("*"):
            relative = path.relative_to(self.root).as_posix()
            if path.is_symlink():
                problems.append(f"unsafe symlink: {relative}")
            elif not path.is_dir() and not path.is_file():
                problems.append(f"unsafe irregular entry: {relative}")
        return sorted(problems)

    def _snapshot_tree(self, source: Path, relative: Path) -> None:
        source = Path(source)
        if not source.is_dir() or source.is_symlink():
            raise InteractiveArchiveError(f"unsafe Assistant snapshot source: {source}")
        for path in sorted(source.rglob("*")):
            if path.is_symlink():
                raise InteractiveArchiveError(f"Assistant snapshot contains a symlink: {path}")
            target = self.root / relative / path.relative_to(source)
            if path.is_dir():
                ensure_owner_directory(target, platform=self.platform)
            elif path.is_file():
                self._write_bytes(target.relative_to(self.root), path.read_bytes())
            else:
                raise InteractiveArchiveError(f"Assistant snapshot has irregular entry: {path}")

    def _last_event_sequence(self) -> int:
        path = self.root / "events.jsonl"
        if not path.is_file() or path.is_symlink():
            return 0
        last = 0
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line:
                continue
            try:
                value = json.loads(line).get("sequence")
            except (json.JSONDecodeError, AttributeError):
                raise InteractiveArchiveError("invalid run event log") from None
            if not isinstance(value, int) or value != last + 1:
                raise InteractiveArchiveError("run event sequence is not contiguous")
            last = value
        return last

    def _append_json_line(self, relative: str, payload: Mapping[str, Any]) -> None:
        path = self.root / relative
        ensure_owner_directory(path.parent, platform=self.platform)
        flags = os.O_APPEND | os.O_CREAT | os.O_WRONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(path, flags, 0o600)
        try:
            data = (
                json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
                + "\n"
            ).encode("utf-8")
            if self.platform != "win32":
                os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "ab") as handle:
                descriptor = -1
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
        finally:
            if descriptor >= 0:
                os.close(descriptor)

    def _write_model(self, relative: str, model: RecordModel) -> None:
        self._write_bytes(relative, (model.model_dump_json(indent=2) + "\n").encode("utf-8"))

    def _write_bytes(self, relative: str | Path, data: bytes) -> None:
        path = self.root / relative
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            ensure_owner_directory(path.parent, platform=self.platform)
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
            )
            temporary = Path(temporary_name)
            try:
                if self.platform != "win32":
                    os.fchmod(descriptor, 0o600)
                with os.fdopen(descriptor, "wb") as handle:
                    descriptor = -1
                    handle.write(data)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, path)
            finally:
                if descriptor >= 0:
                    os.close(descriptor)
                with contextlib.suppress(OSError):
                    temporary.unlink()
        else:
            atomic_write_text(path, text, platform=self.platform)

    def _load_model(self, relative: str, model: type[ModelT]) -> ModelT:
        path = self.root / relative
        if path.is_symlink() or not path.is_file():
            raise InteractiveArchiveError(f"missing or unsafe interactive record: {path}")
        try:
            return model.model_validate_json(path.read_bytes())
        except (OSError, ValidationError) as error:
            raise InteractiveArchiveError(
                f"invalid interactive record {relative}: {error}"
            ) from None

    def _load_directory(self, relative: str, model: type[ModelT]) -> list[ModelT]:
        directory = self.root / relative
        if not directory.exists():
            return []
        if directory.is_symlink() or not directory.is_dir():
            raise InteractiveArchiveError(f"unsafe interactive record directory: {directory}")
        return [
            self._load_model(path.relative_to(self.root).as_posix(), model)
            for path in sorted(directory.glob("*.json"))
        ]

    def _secure_tree(self) -> None:
        if self.platform == "win32":
            return
        try:
            self.root.chmod(0o700)
            for path in self.root.rglob("*"):
                if path.is_symlink():
                    continue
                path.chmod(0o700 if path.is_dir() else 0o600)
        except OSError as error:
            raise InteractiveArchiveError(
                f"cannot secure interactive archive permissions: {error}"
            ) from None

    def _chmod_file(self, path: Path) -> None:
        if self.platform != "win32":
            try:
                path.chmod(0o600)
            except OSError as error:
                raise InteractiveArchiveError(
                    f"cannot secure exported audit file permissions: {error}"
                ) from None


def scan_interactive_audit_export(root: Path) -> list[str]:
    """Return path/value-shaped leaks that make an audit export unsafe to publish."""
    root = Path(root)
    problems: list[str] = []
    if root.is_symlink() or not root.is_dir():
        return [f"unsafe export root: {root}"]
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            problems.append(f"{relative}: symlink is not allowed")
            continue
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            problems.append(f"{relative}: cannot scan UTF-8 content: {error}")
            continue
        if "env_values" in text:
            problems.append(f"{relative}: contains an env_values key")
        if _ABSOLUTE_PATH_TEXT.search(text) or _LOCAL_FILE_URI_TEXT.search(text):
            problems.append(f"{relative}: contains an absolute-path-shaped string")
    return problems


class InteractiveRunStore:
    def __init__(self, root: Path, *, platform: str = sys.platform) -> None:
        self.root = Path(root)
        self.platform = platform

    def archive(self, run_id: str) -> InteractiveArchive:
        if not run_id.startswith("run-") or "/" in run_id or "\\" in run_id:
            raise InteractiveArchiveError(f"invalid run id: {run_id!r}")
        path = self.root / run_id
        if path.is_symlink() or not path.is_dir():
            raise InteractiveArchiveError(f"interactive run not found: {run_id}")
        return InteractiveArchive(path, platform=self.platform)

    def list_records(self) -> list[InteractiveRunRecordV1]:
        if not self.root.exists():
            return []
        if self.root.is_symlink() or not self.root.is_dir():
            raise InteractiveArchiveError(f"unsafe interactive runs root: {self.root}")
        records = []
        for path in sorted(self.root.iterdir()):
            if not path.name.startswith("run-"):
                continue
            if path.is_symlink() or not path.is_dir():
                raise InteractiveArchiveError(f"unsafe interactive run entry: {path.name}")
            run_path = path / "run.json"
            if not run_path.is_file() or run_path.is_symlink():
                raise InteractiveArchiveError(f"run identity is missing or unsafe: {path.name}")
            try:
                identity = json.loads(run_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
                raise InteractiveArchiveError(
                    f"cannot inspect run identity for {path.name}: {error}"
                ) from None
            if isinstance(identity, dict) and identity.get("kind") == "run-record":
                continue
            if not isinstance(identity, dict) or identity.get("kind") != "interactive-run-record":
                raise InteractiveArchiveError(f"unknown run identity for {path.name}")
            records.append(InteractiveArchive(path, platform=self.platform).load_run())
        return records

    def cleanup_closed(self, run_id: str) -> None:
        archive = self.archive(run_id)
        record = archive.load_run()
        if record.phase.value != "closed":
            raise InteractiveArchiveError("only a closed interactive run can be cleaned up")
        problems = archive.verify_manifest()
        if problems:
            raise InteractiveArchiveError(
                "refusing to remove an invalid interactive archive: " + "; ".join(problems)
            )
        shutil.rmtree(archive.root)
