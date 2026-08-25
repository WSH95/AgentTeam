"""Deterministic stdlib-only file coordination provider (M1b section 9.1)."""

from __future__ import annotations

import contextlib
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

from agentteam.coordination.protocol import (
    CleanupOutcome,
    CoordinationError,
    SnapshotState,
    SpaceUnavailableError,
    SubstrateInfo,
    SubstrateMessage,
    SubstrateTask,
    SubstrateTaskStatus,
    TaskClaimError,
    UnknownRecipientError,
    UnknownTaskError,
)
from agentteam.domain.team import IndependenceAchieved, SubstrateKind

_MEMBER_NAME = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")


class LocalCoordinationProvider:
    """One run-owned coordination root with deterministic, isolated spaces."""

    def __init__(self, coordination_root: Path, *, platform: str | None = None) -> None:
        self.coordination_root = Path(coordination_root)
        self.platform = platform or sys.platform
        self._ensure_directory(self.coordination_root)
        self._spaces: dict[str, Path] = {}
        self._space_sequence = 0

    def info(self) -> SubstrateInfo:
        return SubstrateInfo(
            kind=SubstrateKind.LOCAL,
            version="1",
            revision="builtin",
            achieved_isolation=IndependenceAchieved.DATA_DIR,
        )

    # -- space lifecycle ---------------------------------------------------

    def create_space(self, *, lead: str) -> str:
        self._validate_member_name(lead)
        self._space_sequence += 1
        space = "space" if self._space_sequence == 1 else f"space-{self._space_sequence}"
        root = self.coordination_root / space
        if root.exists() or root.is_symlink():
            raise CoordinationError(f"local space already exists: {space}")
        for directory in (
            root,
            root / "tasks",
            root / "inboxes",
            root / "consumed",
            root / "snapshots",
        ):
            self._ensure_directory(directory)
        self._spaces[space] = root
        self._write_json(
            root / "metadata.json",
            {
                "id": space,
                "lead": lead,
                "members": [lead],
                "next_task": 1,
                "next_message": 1,
                "next_snapshot": 1,
            },
        )
        self._write_json(root / "events.json", [])
        self._append_event(root, "space-created", lead=lead)
        return space

    def add_member(self, space: str, name: str) -> None:
        self._validate_member_name(name)
        root = self._open_space(space)
        metadata = self._metadata(root)
        members = self._string_list(metadata, "members")
        if name not in members:
            members.append(name)
            metadata["members"] = members
            self._write_json(root / "metadata.json", metadata)
            self._append_event(root, "member-added", member=name)

    def members(self, space: str) -> list[str]:
        return self._string_list(self._metadata(self._open_space(space)), "members")

    def cleanup(self, space: str, *, copy_out_verified: bool) -> CleanupOutcome:
        root = self._open_space(space)
        self._append_event(root, "space-closed", copy_out_verified=copy_out_verified)
        self._write_json(root / "closed", {"copy_out_verified": copy_out_verified})
        retained = any((root / "snapshots").glob("*.json"))
        return CleanupOutcome(
            space_closed=True,
            snapshot_state=SnapshotState.RETAINED if retained else SnapshotState.NONE,
            warning_codes=(),
        )

    # -- task store --------------------------------------------------------

    def create_task(self, space: str, subject: str, *, blocked_by: list[str]) -> str:
        if not subject:
            raise CoordinationError("task subject must be non-empty")
        root = self._open_space(space)
        if len(set(blocked_by)) != len(blocked_by):
            raise CoordinationError("task blockers must be unique")
        known = {task.id for task in self.tasks(space)}
        unknown = set(blocked_by) - known
        if unknown:
            raise UnknownTaskError("unknown blocker ids: " + ", ".join(sorted(unknown)))
        metadata = self._metadata(root)
        sequence = self._integer(metadata, "next_task")
        task_id = f"t-{sequence}"
        metadata["next_task"] = sequence + 1
        self._write_json(root / "metadata.json", metadata)
        status = SubstrateTaskStatus.BLOCKED if blocked_by else SubstrateTaskStatus.PENDING
        self._write_json(
            self._task_path(root, task_id),
            {
                "id": task_id,
                "subject": subject,
                "status": status.value,
                "blocked_by": blocked_by,
                "claimed_by": None,
            },
        )
        self._append_event(root, "task-created", task_id=task_id)
        return task_id

    def task(self, space: str, task_id: str) -> SubstrateTask:
        root = self._open_space(space)
        return self._public_task(self._task_row(root, task_id))

    def tasks(self, space: str) -> list[SubstrateTask]:
        root = self._open_space(space)
        paths = sorted((root / "tasks").glob("t-*.json"), key=self._sequence_key)
        return [self._public_task(self._read_object(path)) for path in paths]

    def update_task(
        self,
        space: str,
        task_id: str,
        status: SubstrateTaskStatus,
        *,
        caller: str,
    ) -> None:
        root = self._open_space(space)
        try:
            requested = SubstrateTaskStatus(status)
        except ValueError as error:
            raise ValueError(f"unsupported protocol task status: {status!r}") from error
        row = self._task_row(root, task_id)
        current = SubstrateTaskStatus(str(row["status"]))
        claimed_by = row.get("claimed_by")

        if current is SubstrateTaskStatus.RUNNING and claimed_by != caller:
            raise TaskClaimError(f"task {task_id} is claimed by another member")
        if current is SubstrateTaskStatus.PENDING and requested is SubstrateTaskStatus.RUNNING:
            row["status"] = requested.value
            row["claimed_by"] = caller
        elif current is SubstrateTaskStatus.RUNNING and requested is SubstrateTaskStatus.COMPLETED:
            row["status"] = requested.value
            row["claimed_by"] = None
        else:
            raise CoordinationError(
                f"invalid local task transition: {current.value} -> {requested.value}"
            )
        self._write_json(self._task_path(root, task_id), row)
        self._append_event(root, "task-updated", task_id=task_id, status=requested.value)
        if requested is SubstrateTaskStatus.COMPLETED:
            self._auto_unblock(root, task_id)

    def _auto_unblock(self, root: Path, completed_id: str) -> None:
        paths = sorted((root / "tasks").glob("t-*.json"), key=self._sequence_key)
        for path in paths:
            row = self._read_object(path)
            blockers = self._string_list(row, "blocked_by")
            if completed_id not in blockers:
                continue
            blockers.remove(completed_id)
            row["blocked_by"] = blockers
            if not blockers and row["status"] == SubstrateTaskStatus.BLOCKED.value:
                row["status"] = SubstrateTaskStatus.PENDING.value
            self._write_json(path, row)
            self._append_event(root, "task-unblocked", task_id=str(row["id"]))

    # -- mailbox -----------------------------------------------------------

    def send(self, space: str, sender: str, recipient: str, body: str) -> None:
        root = self._open_space(space)
        roster = self._string_list(self._metadata(root), "members")
        if recipient not in roster:
            raise UnknownRecipientError(f"unknown message recipient: {recipient}")
        if sender not in roster:
            raise CoordinationError(f"unknown message sender: {sender}")
        metadata = self._metadata(root)
        sequence = self._integer(metadata, "next_message")
        metadata["next_message"] = sequence + 1
        self._write_json(root / "metadata.json", metadata)
        inbox = root / "inboxes" / recipient
        self._ensure_directory(inbox)
        self._write_json(
            inbox / f"m-{sequence}.json",
            {"sender": sender, "recipient": recipient, "body": body},
        )
        self._append_event(root, "message-sent", sender=sender, recipient=recipient)

    def receive(self, space: str, recipient: str, *, limit: int) -> list[SubstrateMessage]:
        root = self._open_space(space)
        if recipient not in self._string_list(self._metadata(root), "members"):
            raise UnknownRecipientError(f"unknown message recipient: {recipient}")
        if limit < 0:
            raise ValueError("message limit must be non-negative")
        inbox = root / "inboxes" / recipient
        consumed = root / "consumed" / recipient
        self._ensure_directory(inbox)
        self._ensure_directory(consumed)
        messages: list[SubstrateMessage] = []
        paths = sorted(inbox.glob("m-*.json"), key=self._sequence_key)
        for path in paths[:limit]:
            destination = consumed / path.name
            try:
                os.replace(path, destination)
            except FileNotFoundError:
                continue
            self._chmod_file(destination)
            row = self._read_object(destination)
            messages.append(
                SubstrateMessage(
                    sender=str(row["sender"]),
                    recipient=str(row["recipient"]),
                    body=str(row["body"]),
                )
            )
        if messages:
            self._append_event(root, "messages-received", recipient=recipient, count=len(messages))
        return messages

    # -- snapshot ----------------------------------------------------------

    def snapshot(self, space: str, tag: str) -> str:
        root = self._open_space(space)
        metadata = self._metadata(root)
        sequence = self._integer(metadata, "next_snapshot")
        snapshot_id = f"s-{sequence}"
        metadata["next_snapshot"] = sequence + 1
        self._write_json(root / "metadata.json", metadata)
        self._append_event(root, "snapshot-created", snapshot_id=snapshot_id)
        bundle = self._bundle(root, tag=tag)
        self._write_json(self._snapshot_path(root, snapshot_id), bundle)
        return snapshot_id

    def read_snapshot(self, space: str, snapshot_id: str) -> dict[str, Any]:
        root = self._open_space(space)
        path = self._snapshot_path(root, snapshot_id)
        if not path.is_file():
            raise CoordinationError(f"unknown snapshot id: {snapshot_id}")
        return self._read_object(path)

    def restore(self, space: str, snapshot_id: str) -> dict[str, Any]:
        root = self._open_space(space)
        bundle = self.read_snapshot(space, snapshot_id)
        metadata = bundle.get("metadata")
        tasks = bundle.get("tasks")
        messages = bundle.get("messages")
        events = bundle.get("events")
        if not isinstance(metadata, dict) or not isinstance(tasks, list):
            raise CoordinationError("local snapshot has an invalid state shape")
        if not isinstance(messages, list) or not isinstance(events, list):
            raise CoordinationError("local snapshot has an invalid history shape")
        if metadata.get("id") != space:
            raise CoordinationError("local snapshot belongs to a different space")
        restored_members = self._string_list(metadata, "members")
        for member in restored_members:
            self._validate_member_name(member)

        self._reset_directory(root / "tasks")
        self._reset_directory(root / "inboxes")
        self._reset_directory(root / "consumed")
        self._write_json(root / "metadata.json", metadata)
        for row in tasks:
            if not isinstance(row, dict) or not isinstance(row.get("id"), str):
                raise CoordinationError("local snapshot has an invalid task row")
            self._write_json(self._task_path(root, row["id"]), row)
        for item in messages:
            if not isinstance(item, dict):
                raise CoordinationError("local snapshot has an invalid message row")
            location = item.get("location")
            recipient = item.get("recipient")
            filename = item.get("filename")
            row = item.get("message")
            if location not in {"inboxes", "consumed"}:
                raise CoordinationError("local snapshot has an invalid message location")
            if not isinstance(recipient, str) or not isinstance(filename, str):
                raise CoordinationError("local snapshot has an invalid message identity")
            if recipient not in restored_members or not re.fullmatch(r"m-[0-9]+\.json", filename):
                raise CoordinationError("local snapshot has an unsafe message identity")
            if not isinstance(row, dict):
                raise CoordinationError("local snapshot has an invalid message payload")
            self._write_json(root / location / recipient / filename, row)
        self._write_json(root / "events.json", events)
        self._append_event(root, "snapshot-restored", snapshot_id=snapshot_id)
        return bundle

    def _bundle(self, root: Path, *, tag: str) -> dict[str, Any]:
        tasks = [
            self._read_object(path)
            for path in sorted((root / "tasks").glob("t-*.json"), key=self._sequence_key)
        ]
        messages: list[dict[str, Any]] = []
        for location in ("inboxes", "consumed"):
            base = root / location
            for recipient_dir in sorted(path for path in base.iterdir() if path.is_dir()):
                for path in sorted(recipient_dir.glob("m-*.json"), key=self._sequence_key):
                    messages.append(
                        {
                            "location": location,
                            "recipient": recipient_dir.name,
                            "filename": path.name,
                            "message": self._read_object(path),
                        }
                    )
        return {
            "provider": "local",
            "tag": tag,
            "metadata": self._metadata(root),
            "tasks": tasks,
            "messages": messages,
            "events": self._read_list(root / "events.json"),
        }

    # -- file primitives ---------------------------------------------------

    def _open_space(self, space: str) -> Path:
        root = self._spaces.get(space)
        if root is None or not root.is_dir() or (root / "closed").exists():
            raise SpaceUnavailableError(f"coordination space is unavailable: {space}")
        return root

    def _metadata(self, root: Path) -> dict[str, Any]:
        return self._read_object(root / "metadata.json")

    def _task_row(self, root: Path, task_id: str) -> dict[str, Any]:
        path = self._task_path(root, task_id)
        if not path.is_file():
            raise UnknownTaskError(f"unknown task id: {task_id}")
        return self._read_object(path)

    @staticmethod
    def _task_path(root: Path, task_id: str) -> Path:
        if not task_id.startswith("t-") or not task_id[2:].isdigit():
            raise UnknownTaskError(f"unknown task id: {task_id}")
        return root / "tasks" / f"{task_id}.json"

    @staticmethod
    def _snapshot_path(root: Path, snapshot_id: str) -> Path:
        if not snapshot_id.startswith("s-") or not snapshot_id[2:].isdigit():
            raise CoordinationError(f"unknown snapshot id: {snapshot_id}")
        return root / "snapshots" / f"{snapshot_id}.json"

    @staticmethod
    def _public_task(row: dict[str, Any]) -> SubstrateTask:
        return SubstrateTask(
            id=str(row["id"]),
            subject=str(row["subject"]),
            status=SubstrateTaskStatus(str(row["status"])),
            blocked_by=tuple(str(item) for item in row["blocked_by"]),
        )

    def _append_event(self, root: Path, event: str, **facts: object) -> None:
        events = self._read_list(root / "events.json")
        events.append({"seq": len(events) + 1, "event": event, **facts})
        self._write_json(root / "events.json", events)

    def _write_json(self, path: Path, payload: object) -> None:
        text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
        self._ensure_directory(path.parent)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
        )
        temporary = Path(temporary_name)
        try:
            if self.platform != "win32":
                os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
                descriptor = -1
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
            self._chmod_file(path)
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            with contextlib.suppress(OSError):
                temporary.unlink()

    def _ensure_directory(self, path: Path) -> None:
        if path.is_symlink():
            raise CoordinationError(f"refusing symlinked coordination directory: {path.name}")
        path.mkdir(parents=True, exist_ok=True)
        if not path.is_dir() or path.is_symlink():
            raise CoordinationError(f"coordination path is not a directory: {path.name}")
        if self.platform != "win32":
            with contextlib.suppress(OSError):
                path.chmod(0o700)

    def _reset_directory(self, path: Path) -> None:
        if path.is_symlink():
            raise CoordinationError(f"refusing symlinked coordination directory: {path.name}")
        if path.exists():
            shutil.rmtree(path)
        self._ensure_directory(path)

    def _chmod_file(self, path: Path) -> None:
        if self.platform != "win32":
            with contextlib.suppress(OSError):
                path.chmod(0o600)

    @staticmethod
    def _read_object(path: Path) -> dict[str, Any]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise CoordinationError(f"cannot read local coordination state: {path.name}") from error
        if not isinstance(payload, dict):
            raise CoordinationError(f"local coordination object has wrong shape: {path.name}")
        return payload

    @staticmethod
    def _read_list(path: Path) -> list[Any]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise CoordinationError(f"cannot read local coordination state: {path.name}") from error
        if not isinstance(payload, list):
            raise CoordinationError(f"local coordination list has wrong shape: {path.name}")
        return payload

    @staticmethod
    def _string_list(row: dict[str, Any], key: str) -> list[str]:
        value = row.get(key)
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise CoordinationError(f"local coordination field is not a string list: {key}")
        return list(value)

    @staticmethod
    def _integer(row: dict[str, Any], key: str) -> int:
        value = row.get(key)
        if not isinstance(value, int):
            raise CoordinationError(f"local coordination field is not an integer: {key}")
        return value

    @staticmethod
    def _validate_member_name(name: str) -> None:
        if _MEMBER_NAME.fullmatch(name) is None:
            raise CoordinationError(f"invalid coordination member name: {name!r}")

    @staticmethod
    def _sequence_key(path: Path) -> int:
        try:
            return int(path.stem.rsplit("-", 1)[1])
        except (IndexError, ValueError) as error:
            raise CoordinationError(f"invalid local sequence file: {path.name}") from error
