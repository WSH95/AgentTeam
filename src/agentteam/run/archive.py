"""The run archive (plan section 13).

A pending archive exists before any harness side effect; every write is
atomic (`tmp` + `os.replace` in-directory); POSIX archives are owner-only
(0o700 directories, 0o600 files) while Windows relies on the profile ACL and
warns for roots outside it; the SHA-256 manifest written at finalize covers
every record file — never the per-leg working directories — and re-verifies.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agentteam.domain.bundle import BundleManifestV1
from agentteam.domain.common import RecordModel
from agentteam.domain.request import RunRequestV1
from agentteam.domain.review import NormalizedReviewV1, SynthesisReportV1
from agentteam.domain.run import (
    ArtifactRefV1,
    EnsembleRecordV1,
    HarnessInvocationV1,
    RunRecordV1,
    TeamRunRecordV1,
)
from agentteam.domain.team import MemberResultV1, TeamRunRequestV1
from agentteam.harness.types import RawInvocationV1, RenderedInvocationV1
from agentteam.run.ids import SYNTHESIS_INVOCATION_ID

_WORKING_DIRS = ("workspace", "config-home", "scratch")


class ManifestEntryV1(RecordModel):
    path: str
    sha256: str


class ManifestV1(RecordModel):
    files: list[ManifestEntryV1]


class RunArchive:
    def __init__(
        self,
        root: Path,
        *,
        retain_raw_streams: bool = True,
        platform: str = sys.platform,
    ) -> None:
        self.root = root
        self._retain_raw_streams = retain_raw_streams
        self._platform = platform
        self._message_sequence = 0

    # -- creation -------------------------------------------------------------

    @classmethod
    def create(
        cls,
        root: Path,
        *,
        run_record: RunRecordV1,
        resolved_request: RunRequestV1,
        bundle: BundleManifestV1,
        retain_raw_streams: bool = True,
        platform: str = sys.platform,
        home: Path | None = None,
    ) -> tuple[RunArchive, list[str]]:
        if root.exists() and any(root.iterdir()):
            raise ValueError(f"run archive root is not empty: {root}")
        root.mkdir(parents=True, exist_ok=True)
        archive = cls(root, retain_raw_streams=retain_raw_streams, platform=platform)
        archive._chmod_dir(root)
        warnings: list[str] = []
        if platform == "win32":
            resolved_home = home if home is not None else Path.home()
            resolved_root = root.resolve()
            if resolved_home.resolve() not in (resolved_root, *resolved_root.parents):
                warnings.append(
                    "run archive root is outside the user profile; access control "
                    f"relies on that profile's ACL: {root}"
                )
        archive.write_run_record(run_record)
        archive._write_json("request.resolved.json", resolved_request)
        archive._write_json("bundle-manifest.json", bundle)
        return archive, warnings

    @classmethod
    def create_team(
        cls,
        root: Path,
        *,
        run_record: TeamRunRecordV1,
        resolved_request: TeamRunRequestV1,
        bundles: dict[str, BundleManifestV1],
        retain_raw_streams: bool = True,
        platform: str = sys.platform,
        home: Path | None = None,
    ) -> tuple[RunArchive, list[str]]:
        """Create a pending team archive before a coordination side effect."""
        if root.exists() and any(root.iterdir()):
            raise ValueError(f"run archive root is not empty: {root}")
        root.mkdir(parents=True, exist_ok=True)
        archive = cls(root, retain_raw_streams=retain_raw_streams, platform=platform)
        archive._chmod_dir(root)
        warnings: list[str] = []
        if platform == "win32":
            resolved_home = home if home is not None else Path.home()
            resolved_root = root.resolve()
            if resolved_home.resolve() not in (resolved_root, *resolved_root.parents):
                warnings.append(
                    "run archive root is outside the user profile; access control "
                    f"relies on that profile's ACL: {root}"
                )
        archive.write_run_record(run_record)
        archive._write_json("request.resolved.json", resolved_request)
        for member, bundle in bundles.items():
            archive._write_json(f"bundles/{member}.json", bundle)
        return archive, warnings

    # -- layout ---------------------------------------------------------------

    @property
    def events_path(self) -> Path:
        return self.root / "events.jsonl"

    def leg_dir(self, invocation_id: str) -> Path:
        group = "synthesis" if invocation_id == SYNTHESIS_INVOCATION_ID else "legs"
        return self.root / group / invocation_id

    def working_dirs(self, invocation_id: str) -> tuple[Path, Path, Path]:
        base = self.leg_dir(invocation_id)
        dirs = tuple(base / name for name in _WORKING_DIRS)
        for directory in dirs:
            directory.mkdir(parents=True, exist_ok=True)
            self._chmod_dir(directory)
        workspace, config_home, scratch = dirs
        return workspace, config_home, scratch

    # -- writers --------------------------------------------------------------

    def write_run_record(self, record: RunRecordV1 | TeamRunRecordV1) -> None:
        self._write_json("run.json", record)

    def write_invocation(self, record: HarnessInvocationV1) -> None:
        relative = self.leg_dir(record.invocation_id).relative_to(self.root) / "invocation.json"
        self._write_json(relative.as_posix(), record)

    def write_rendered(self, invocation_id: str, rendered: RenderedInvocationV1) -> None:
        relative = self.leg_dir(invocation_id).relative_to(self.root) / "invocation.render.json"
        self._write_bytes(
            relative.as_posix(), (rendered.model_dump_json(indent=2) + "\n").encode("utf-8")
        )

    def write_raw_streams(self, invocation_id: str, raw: RawInvocationV1) -> list[ArtifactRefV1]:
        base = self.leg_dir(invocation_id).relative_to(self.root)
        refs: list[ArtifactRefV1] = []
        if self._retain_raw_streams:
            for role, name, data in (
                ("stdout", "stdout.raw", raw.stdout),
                ("stderr", "stderr.raw", raw.stderr),
            ):
                relative = (base / name).as_posix()
                self._write_bytes(relative, data)
                refs.append(self._ref(role, relative, data))
        if raw.output_file_text is not None:
            data = raw.output_file_text.encode("utf-8")
            relative = (base / "output-file.json").as_posix()
            self._write_bytes(relative, data)
            refs.append(self._ref("output-file", relative, data))
        return refs

    def write_review(self, invocation_id: str, review: NormalizedReviewV1) -> ArtifactRefV1:
        relative = (
            self.leg_dir(invocation_id).relative_to(self.root) / "review.normalized.json"
        ).as_posix()
        data = (review.model_dump_json(indent=2) + "\n").encode("utf-8")
        self._write_bytes(relative, data)
        return self._ref("normalized-review", relative, data)

    def write_member_result(self, invocation_id: str, result: MemberResultV1) -> ArtifactRefV1:
        relative = (
            self.leg_dir(invocation_id).relative_to(self.root) / "member-result.json"
        ).as_posix()
        data = (result.model_dump_json(indent=2) + "\n").encode("utf-8")
        self._write_bytes(relative, data)
        return self._ref("member-result", relative, data)

    def write_deliverable(
        self, invocation_id: str, relative_path: str, data: bytes
    ) -> ArtifactRefV1:
        relative = (
            self.leg_dir(invocation_id).relative_to(self.root)
            / "deliverables"
            / Path(relative_path)
        ).as_posix()
        self._write_bytes(relative, data)
        return self._ref("deliverable", relative, data)

    def append_message(self, *, sender: str, recipient: str, body: str) -> tuple[int, str]:
        """Durably append a full message envelope before provider transport."""
        self._message_sequence += 1
        row = {
            "seq": self._message_sequence,
            "ts": datetime.now(tz=UTC).isoformat().replace("+00:00", "Z"),
            "sender": sender,
            "recipient": recipient,
            "body": body,
        }
        path = self.root / "coordination" / "messages.jsonl"
        existing = path.read_bytes() if path.is_file() else b""
        line = (
            json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
        ).encode("utf-8")
        self._write_bytes("coordination/messages.jsonl", existing + line)
        return self._message_sequence, hashlib.sha256(body.encode("utf-8")).hexdigest()

    def write_coordination_snapshot(self, payload: dict[str, Any]) -> str:
        data = (
            json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
        ).encode("utf-8")
        self._write_bytes("coordination/snapshot.json", data)
        written = (self.root / "coordination" / "snapshot.json").read_bytes()
        if written != data:
            raise OSError("coordination snapshot read-back disagrees with provider bytes")
        return hashlib.sha256(written).hexdigest()

    def verify_team_bindings(self, record: TeamRunRecordV1) -> list[str]:
        """Enforce the durable invocation/run-record bijection before sealing."""
        problems: list[str] = []
        bindings = {
            member.execution.ref: member.name
            for member in record.members
            if member.execution is not None
        }
        invocations: dict[str, HarnessInvocationV1] = {}
        legs = self.root / "legs"
        if legs.is_dir():
            for path in sorted(legs.glob("inv-*/invocation.json")):
                try:
                    invocation = HarnessInvocationV1.model_validate_json(
                        path.read_text(encoding="utf-8")
                    )
                except (OSError, ValueError) as error:
                    problems.append(f"invalid invocation record: {path.parent.name}: {error}")
                    continue
                invocations[invocation.invocation_id] = invocation
        for ref, member in bindings.items():
            bound_invocation = invocations.get(ref)
            if bound_invocation is None:
                problems.append(f"member {member} binding has no invocation: {ref}")
            elif bound_invocation.status.value not in {
                "succeeded",
                "failed",
                "cancelled",
                "timed-out",
            }:
                problems.append(f"member {member} invocation is not terminal: {ref}")
        for ref in sorted(set(invocations) - set(bindings)):
            problems.append(f"invocation has no member binding: {ref}")
        return problems

    def write_leg_text(
        self, invocation_id: str, name: str, text: str, *, role: str
    ) -> ArtifactRefV1:
        relative = (self.leg_dir(invocation_id).relative_to(self.root) / name).as_posix()
        data = text.encode("utf-8")
        self._write_bytes(relative, data)
        return self._ref(role, relative, data)

    def write_ensemble(self, record: EnsembleRecordV1) -> None:
        self._write_json("ensemble.json", record)

    def write_synthesis_report(self, report: SynthesisReportV1) -> None:
        self._write_json("synthesis-report.json", report)

    # -- manifest -------------------------------------------------------------

    def secure_tree(self) -> None:
        """Recursive owner-only modes over every descendant (G6.R3): dirs
        0700, files 0600, symlinks never followed; win32 relies on the
        profile ACL. Runs at finalize only — sweeping mid-run would race the
        vendor processes still writing into their working dirs."""
        if self._platform == "win32":
            return
        for path in self.root.rglob("*"):
            if path.is_symlink():
                continue
            with contextlib.suppress(OSError):
                path.chmod(0o700 if path.is_dir() else 0o600)
        with contextlib.suppress(OSError):
            self.root.chmod(0o700)

    def finalize_manifest(self) -> None:
        self.secure_tree()
        self._write_json("manifest.sha256.json", self._compute_manifest())

    def verify_manifest(self) -> list[str]:
        stored = ManifestV1.model_validate_json(
            (self.root / "manifest.sha256.json").read_text(encoding="utf-8")
        )
        current = {entry.path: entry.sha256 for entry in self._compute_manifest().files}
        recorded = {entry.path: entry.sha256 for entry in stored.files}
        problems = [f"missing: {path}" for path in sorted(recorded.keys() - current.keys())]
        problems += [f"extra: {path}" for path in sorted(current.keys() - recorded.keys())]
        problems += [
            f"changed: {path}"
            for path in sorted(recorded.keys() & current.keys())
            if recorded[path] != current[path]
        ]
        return problems

    def _compute_manifest(self) -> ManifestV1:
        entries: list[ManifestEntryV1] = []
        for path in sorted(self.root.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(self.root)
            parts = relative.parts
            if relative.as_posix() == "manifest.sha256.json" or relative.suffix == ".tmp":
                continue
            if len(parts) >= 3 and parts[0] in ("legs", "synthesis") and parts[2] in _WORKING_DIRS:
                continue
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            entries.append(ManifestEntryV1(path=relative.as_posix(), sha256=digest))
        entries.sort(key=lambda entry: entry.path)
        return ManifestV1(files=entries)

    # -- primitives -----------------------------------------------------------

    def _ref(self, role: str, relative: str, data: bytes) -> ArtifactRefV1:
        return ArtifactRefV1(role=role, path=relative, sha256=hashlib.sha256(data).hexdigest())

    def _write_json(self, relative: str, record: RecordModel) -> None:
        self._write_bytes(relative, (record.model_dump_json(indent=2) + "\n").encode("utf-8"))

    def _write_bytes(self, relative: str, data: bytes) -> None:
        path = self.root / relative
        directory = path.parent
        directory.mkdir(parents=True, exist_ok=True)
        current = directory
        while True:
            self._chmod_dir(current)
            if current == self.root:
                break
            current = current.parent
        tmp = directory / (path.name + ".tmp")
        try:
            tmp.write_bytes(data)
            self._chmod_file(tmp)
            os.replace(tmp, path)
        finally:
            with contextlib.suppress(OSError):
                if tmp.exists():
                    tmp.unlink()

    def _chmod_dir(self, path: Path) -> None:
        if self._platform != "win32":
            with contextlib.suppress(OSError):
                path.chmod(0o700)

    def _chmod_file(self, path: Path) -> None:
        if self._platform != "win32":
            with contextlib.suppress(OSError):
                path.chmod(0o600)
