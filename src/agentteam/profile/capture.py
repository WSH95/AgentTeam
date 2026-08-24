"""Owner-only, pending-first persistence for attended profile probes."""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import secrets
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agentteam.harness.types import RawInvocationV1
from agentteam.resolution.profiles import atomic_write_text, ensure_owner_directory


class ProbeCapture:
    def __init__(self, root: Path, capture_id: str, *, platform: str) -> None:
        self.root = root
        self.capture_id = capture_id
        self.platform = platform

    @classmethod
    def create(
        cls,
        profile_path: Path,
        *,
        now: datetime | None = None,
        platform: str = sys.platform,
    ) -> ProbeCapture:
        timestamp = now or datetime.now(tz=UTC)
        day = timestamp.date().isoformat()
        probes = Path(profile_path).parent / "probes"
        ensure_owner_directory(probes, platform=platform)
        parent = probes / day
        ensure_owner_directory(parent, platform=platform)
        for _ in range(10):
            capture_id = timestamp.strftime("probe-%Y%m%dT%H%M%SZ-") + secrets.token_hex(4)
            root = parent / capture_id
            try:
                root.mkdir(mode=0o700)
            except FileExistsError:
                continue
            if platform != "win32":
                root.chmod(0o700)
            return cls(root, capture_id, platform=platform)
        raise OSError("could not allocate a unique probe capture directory")

    def begin_call(
        self,
        harness: str,
        call_number: int,
        *,
        command: dict[str, Any],
        started_at: datetime,
    ) -> Path:
        harness_dir = self.root / harness
        ensure_owner_directory(harness_dir, platform=self.platform)
        call_dir = harness_dir / f"call-{call_number}"
        ensure_owner_directory(call_dir, platform=self.platform)
        atomic_write_text(
            call_dir / "command.redacted.json",
            json.dumps(command, indent=2, sort_keys=True) + "\n",
            platform=self.platform,
        )
        self._write_manifest(
            call_dir,
            {
                "schema_version": 1,
                "kind": "probe-call-manifest",
                "capture_id": self.capture_id,
                "harness": harness,
                "call": call_number,
                "status": "pending",
                "started_at": started_at.isoformat().replace("+00:00", "Z"),
                "finished_at": None,
                "artifacts": [],
            },
        )
        return call_dir

    def finish_call(
        self,
        call_dir: Path,
        *,
        raw: RawInvocationV1,
        status: str,
        sanitized_result: dict[str, Any],
    ) -> None:
        artifacts: list[dict[str, str]] = []
        payloads = {
            "stdout.raw": raw.stdout,
            "stderr.raw": raw.stderr,
            "output-file.raw": (
                raw.output_file_text.encode("utf-8") if raw.output_file_text is not None else b""
            ),
            "result.sanitized.json": (
                json.dumps(sanitized_result, indent=2, sort_keys=True) + "\n"
            ).encode("utf-8"),
        }
        for name, data in payloads.items():
            path = call_dir / name
            _atomic_write_bytes(path, data, platform=self.platform)
            artifacts.append({"path": name, "sha256": hashlib.sha256(data).hexdigest()})
        command = call_dir / "command.redacted.json"
        artifacts.append(
            {"path": command.name, "sha256": hashlib.sha256(command.read_bytes()).hexdigest()}
        )
        started_at = raw.started_at or datetime.now(tz=UTC)
        finished_at = raw.finished_at or datetime.now(tz=UTC)
        self._write_manifest(
            call_dir,
            {
                "schema_version": 1,
                "kind": "probe-call-manifest",
                "capture_id": self.capture_id,
                "harness": call_dir.parent.name,
                "call": int(call_dir.name.removeprefix("call-")),
                "status": status,
                "started_at": started_at.isoformat().replace("+00:00", "Z"),
                "finished_at": finished_at.isoformat().replace("+00:00", "Z"),
                "exit_code": raw.exit_code,
                "signal": raw.signal,
                "timed_out": raw.timed_out,
                "duration_ms": raw.duration_ms,
                "artifacts": artifacts,
            },
        )
        self._secure_tree(call_dir)

    def _write_manifest(self, call_dir: Path, payload: dict[str, Any]) -> None:
        atomic_write_text(
            call_dir / "manifest.json",
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            platform=self.platform,
        )

    def _secure_tree(self, root: Path) -> None:
        if self.platform == "win32":
            return
        for path in root.rglob("*"):
            if path.is_symlink():
                continue
            with contextlib.suppress(OSError):
                path.chmod(0o700 if path.is_dir() else 0o600)
        with contextlib.suppress(OSError):
            root.chmod(0o700)


def _atomic_write_bytes(path: Path, data: bytes, *, platform: str) -> None:
    ensure_owner_directory(path.parent, platform=platform)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        if platform != "win32":
            os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = -1
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        if platform != "win32":
            with contextlib.suppress(OSError):
                path.chmod(0o600)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        with contextlib.suppress(OSError):
            temporary.unlink()
