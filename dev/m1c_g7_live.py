#!/usr/bin/env python3
"""Attended, fail-closed M1c G7 live matrix and sanitized-evidence driver.

Run only from the exact committed candidate after its eight non-Windows hosted
CI jobs pass. The script has no retry or diagnostic path. Raw run archives stay
under the owner's AgentTeam home; only scanner-clean audit exports are staged in
``docs/evidence``.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import secrets
import shutil
import signal
import subprocess
import sys
import tempfile
from collections import deque
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import IO, Protocol, cast

from agentteam.commands.runtime import _qualification_targets
from agentteam.domain.common import HarnessId
from agentteam.domain.interactive import (
    CapabilityLevel,
    InteractiveRunOutcome,
    InteractiveRunPhase,
    ProviderLiveAttestationV1,
)
from agentteam.domain.team import TeamTaskStatus
from agentteam.execution.direct_acp import (
    DirectAcpQualificationTarget,
    live_attestation_path,
    load_direct_acp_live_attestation,
    load_direct_acp_qualification,
)
from agentteam.interactive.archive import (
    InteractiveArchive,
    InteractiveRunStore,
    scan_interactive_audit_export,
)
from agentteam.interactive.resolution import default_interactive_roots
from agentteam.interactive.workspace import WorkspaceReservation
from agentteam.library import LibraryStore, default_library_root
from agentteam.resolution.archive import hash_package
from agentteam.resolution.interactive import load_team_template_v2
from agentteam.resolution.profiles import atomic_write_text, ensure_owner_directory

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSISTANT_PATH = REPO_ROOT / "examples" / "assistants" / "m1c-workflow-verifier"
TEAM_PATH = REPO_ROOT / "examples" / "teams" / "m1c-live-workflow.yaml"
ASSISTANT_HASH = "d54e35114f56ee67d72a5dcfa560d8d13139be93e07ca27887bd0dd26a4ee29e"
TEAM_HASH = "b1002f133a3d5fd9dd82456f6c375dcca49e4cc26e69fe2ea7015c068d115ada"
TEAM_ID = "m1c-live-workflow"
TEAM_VERSION = 1
LIFECYCLE_ORDER = (
    HarnessId.CLAUDE_CODE,
    HarnessId.CODEX,
    HarnessId.GROK,
)
WORKFLOW_BINDINGS = {
    "implementer": HarnessId.CODEX,
    "reviewer": HarnessId.CLAUDE_CODE,
    "lead": HarnessId.GROK,
}
DONE_WHEN = "the three bounded artifacts contain the same workflow marker"
MAX_TOTAL_CALLS = 23
EXPECTED_LIFECYCLE_CALLS = 15
EXPECTED_WORKFLOW_CALLS = 4
_HEX_HEAD = re.compile(r"[0-9a-f]{40}")
_RUN_ID = re.compile(r"[0-9]+")
_AGENT_BASENAMES = {
    "acpx",
    "acpx.exe",
    "claude",
    "claude-agent-acp",
    "claude.exe",
    "codex",
    "codex-acp",
    "codex.exe",
    "grok",
    "grok.exe",
}


class G7Error(RuntimeError):
    """A mechanical gate failed; the matrix must stop without retry."""


class LifecycleStopped(G7Error):
    """One lifecycle command stopped, optionally with a fresh partial attestation."""

    def __init__(
        self,
        message: str,
        *,
        attestation: ProviderLiveAttestationV1 | None = None,
    ) -> None:
        super().__init__(message)
        self.attestation = attestation


class ProcessLike(Protocol):
    @property
    def pid(self) -> int: ...

    @property
    def stdin(self) -> IO[str] | None: ...

    @property
    def stdout(self) -> IO[str] | None: ...

    def poll(self) -> int | None: ...

    def wait(self, timeout: float | None = None) -> int: ...

    def terminate(self) -> None: ...

    def kill(self) -> None: ...


@dataclass(frozen=True)
class TurnContract:
    member: str
    work_item: str | None
    prompt: str
    expected_text: str
    readable: frozenset[Path]
    writable: Path | None


@dataclass(frozen=True)
class ToolRequest:
    permission_id: str
    classification: str
    kind: str
    title: str
    paths: tuple[Path, ...]


@dataclass(frozen=True)
class WorkflowResult:
    run_id: str
    turn_ids: tuple[str, ...]
    attempted_calls: int


def _json_bytes(payload: Mapping[str, object]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _owner_home(environ: Mapping[str, str]) -> Path:
    configured = environ.get("AGENTTEAM_HOME")
    return Path(configured).expanduser() if configured else Path.home() / ".agentteam"


def _write_owner_json(path: Path, payload: Mapping[str, object]) -> None:
    ensure_owner_directory(path.parent, platform=sys.platform)
    atomic_write_text(path, _json_bytes(payload).decode("utf-8"), platform=sys.platform)


def _run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode != 0:
        raise G7Error(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _candidate_head(expected: str) -> str:
    head = _run_git("rev-parse", "HEAD")
    if not _HEX_HEAD.fullmatch(expected) or head != expected:
        raise G7Error(f"candidate HEAD mismatch: expected {expected}, found {head}")
    status = _run_git("status", "--porcelain=v1", "--untracked-files=all")
    unexpected = [
        line
        for line in status.splitlines()
        if line and not (line.startswith("?? .codex/") or line == "?? .codex")
    ]
    if unexpected:
        raise G7Error(
            "candidate is not clean outside the ignored .codex user state: " + "; ".join(unexpected)
        )
    return head


def _validate_hosted_run_payload(payload: object, candidate_head: str) -> None:
    if not isinstance(payload, dict):
        raise G7Error("hosted run response is not an object")
    if (
        payload.get("headSha") != candidate_head
        or payload.get("status") != "completed"
        or payload.get("conclusion") != "success"
    ):
        raise G7Error("hosted run is not completed/success at the exact candidate HEAD")
    jobs = payload.get("jobs")
    if not isinstance(jobs, list) or len(jobs) != 8:
        raise G7Error("hosted run must contain exactly eight default non-Windows jobs")
    expected_names = {
        "scaffold (ubuntu-latest, py3.11)",
        "scaffold (ubuntu-latest, py3.13)",
        "scaffold (macos-latest, py3.11)",
        "scaffold (macos-latest, py3.13)",
        "clawteam (ubuntu-latest, py3.11)",
        "clawteam (macos-latest, py3.11)",
        "vendor-smoke (ubuntu-latest, py3.11)",
        "vendor-smoke (macos-latest, py3.11)",
    }
    observed_names: set[str] = set()
    for job in jobs:
        if not isinstance(job, dict):
            raise G7Error("hosted run contains a malformed job")
        name = job.get("name")
        if (
            not isinstance(name, str)
            or "windows" in name.lower()
            or job.get("status") != "completed"
            or job.get("conclusion") != "success"
        ):
            raise G7Error("hosted run contains a non-green or Windows job")
        observed_names.add(name)
    if observed_names != expected_names:
        raise G7Error("hosted run job names do not match the exact eight-job matrix")


def _verify_hosted_run(run_id: str, candidate_head: str) -> None:
    try:
        result = subprocess.run(
            [
                "gh",
                "run",
                "view",
                run_id,
                "--json",
                "headSha,status,conclusion,jobs",
            ],
            cwd=REPO_ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise G7Error(f"cannot read hosted CI evidence: {error}") from None
    if result.returncode != 0:
        raise G7Error(f"cannot read hosted CI evidence: {result.stderr.strip()}")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise G7Error(f"hosted CI response is malformed: {error}") from None
    _validate_hosted_run_payload(payload, candidate_head)


def _evidence_destination(value: str) -> Path:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise G7Error("--evidence-date must be an exact YYYY-MM-DD UTC date")
    try:
        parsed_date = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise G7Error("--evidence-date must be a real calendar date") from None
    if parsed_date.isoformat() != value:
        raise G7Error("--evidence-date is not canonical")
    return REPO_ROOT / "docs" / "evidence" / f"m1c-live-{value}"


def _ancestor_pids(pid: int | None = None) -> set[int]:
    current = os.getpid() if pid is None else pid
    ancestors: set[int] = set()
    while current > 1 and current not in ancestors:
        ancestors.add(current)
        try:
            status = (Path("/proc") / str(current) / "status").read_text(encoding="utf-8")
        except OSError:
            break
        match = re.search(r"(?m)^PPid:\s+(\d+)$", status)
        if match is None:
            break
        current = int(match.group(1))
    ancestors.add(1)
    return ancestors


def _agent_processes(*, proc_root: Path = Path("/proc")) -> list[str]:
    ancestors = _ancestor_pids()
    found: list[str] = []
    for entry in proc_root.iterdir():
        if not entry.name.isdigit() or int(entry.name) in ancestors:
            continue
        try:
            raw = (entry / "cmdline").read_bytes()
        except OSError:
            continue
        words = [part.decode("utf-8", errors="replace") for part in raw.split(b"\0") if part]
        if not words:
            continue
        basename = Path(words[0]).name.lower()
        joined = " ".join(words)
        lowered = joined.lower()
        is_agent = basename in _AGENT_BASENAMES
        is_packaged_agent = any(
            marker in lowered
            for marker in (
                "@anthropic-ai/claude-code",
                "@openai/codex",
                "claude-agent-acp",
                "codex-acp",
                "grok agent stdio",
            )
        )
        is_bridge = "bridge.mjs" in lowered and "direct-acp" in lowered
        is_agentteam_session = "agentteam.cli" in lowered and any(
            marker in lowered
            for marker in (" team chat ", " assistant chat ", " runtime qualify-live ")
        )
        if is_agent or is_packaged_agent or is_bridge or is_agentteam_session:
            category = (
                basename
                if is_agent
                else "packaged-agent"
                if is_packaged_agent
                else "direct-acp-bridge"
                if is_bridge
                else "agentteam-interactive-session"
            )
            found.append(f"pid {entry.name}: {category}")
    return sorted(found)


def _nonterminal_runs(environ: Mapping[str, str]) -> list[str]:
    runs_root, reservations_root = default_interactive_roots(environ)
    records = InteractiveRunStore(runs_root).list_records() if runs_root.exists() else []
    active = [
        f"{record.run_id}:{record.phase.value}"
        for record in records
        if record.phase is not InteractiveRunPhase.CLOSED
    ]
    reservations = sorted(reservations_root.glob("*.json")) if reservations_root.exists() else []
    if reservations and not active:
        active.extend(f"orphan-reservation:{path.name}" for path in reservations)
    return active


def _verify_fixture_hashes() -> None:
    assistant_hash = hash_package(ASSISTANT_PATH).package_hash
    team = load_team_template_v2(TEAM_PATH)
    team_hash = hashlib.sha256(team.source.encode("utf-8")).hexdigest()
    if assistant_hash != ASSISTANT_HASH:
        raise G7Error(f"Assistant fixture hash drifted: {assistant_hash}")
    if team_hash != TEAM_HASH:
        raise G7Error(f"Team fixture hash drifted: {team_hash}")
    expected_preferences = {member: [harness] for member, harness in WORKFLOW_BINDINGS.items()}
    if team.definition.preferences.harness_preferences != expected_preferences:
        raise G7Error("Team harness mapping drifted")
    refs = {member.assistant.content_hash for member in team.definition.members}
    if refs != {ASSISTANT_HASH}:
        raise G7Error("Team Assistant refs do not all pin the exact fixture hash")


def _import_fixtures(environ: Mapping[str, str]) -> None:
    store = LibraryStore(default_library_root(environ), platform=sys.platform)
    assistant = store.import_assistant(ASSISTANT_PATH)
    if assistant.content_hash != ASSISTANT_HASH:
        raise G7Error("immutable-library Assistant import returned an unexpected hash")
    team = store.import_team(TEAM_PATH)
    if team.content_hash != TEAM_HASH:
        raise G7Error("immutable-library Team import returned an unexpected hash")


def _staged_targets(
    environ: Mapping[str, str],
) -> dict[HarnessId, DirectAcpQualificationTarget]:
    targets: dict[HarnessId, DirectAcpQualificationTarget] = {}
    for harness in LIFECYCLE_ORDER:
        selected, problems = _qualification_targets(config=None, selected=(harness,))
        if problems or len(selected) != 1:
            detail = "; ".join(f"{key}: {value}" for key, value in sorted(problems.items()))
            raise G7Error(f"{harness.value} target is not exactly staged: {detail or 'missing'}")
        target = selected[0]
        report, report_problems = load_direct_acp_qualification(
            target,
            environ=environ,
            platform=sys.platform,
        )
        if report is None:
            raise G7Error(
                f"{harness.value} no-call qualification is stale: " + "; ".join(report_problems)
            )
        if (
            report.status != "pass"
            or report.model_calls != 0
            or report.capabilities.persistent_turns is not CapabilityLevel.UNKNOWN
            or report.capabilities.recovery is not CapabilityLevel.UNKNOWN
        ):
            raise G7Error(f"{harness.value} no-call report does not have the staged shape")
        targets[harness] = target
    return targets


def _confirm(prompt: str) -> bool:
    try:
        answer = input(f"{prompt} [y/N] ")
    except (EOFError, KeyboardInterrupt):
        return False
    return answer.strip().lower() in {"y", "yes"}


def _preflight(args: argparse.Namespace, environ: Mapping[str, str]) -> tuple[str, Path]:
    if sys.platform != "linux":
        raise G7Error("M1c G7 live execution is Linux-only; Windows remains paused")
    if not all(stream.isatty() for stream in (sys.stdin, sys.stdout, sys.stderr)):
        raise G7Error("M1c G7 requires an attended stdin/stdout/stderr TTY")
    if not _RUN_ID.fullmatch(args.hosted_run):
        raise G7Error("--hosted-run must be the numeric eight-job green workflow run id")
    head = _candidate_head(args.candidate_head)
    _verify_hosted_run(args.hosted_run, head)
    other_agents = _agent_processes()
    if other_agents:
        raise G7Error(
            "another local coding-agent/ACP process is active: " + "; ".join(other_agents)
        )
    active_runs = _nonterminal_runs(environ)
    if active_runs:
        raise G7Error("another interactive run/reservation is active: " + "; ".join(active_runs))
    _verify_fixture_hashes()
    evidence_dir = _evidence_destination(args.evidence_date)
    if evidence_dir.exists():
        raise G7Error(f"evidence destination already exists: {evidence_dir.relative_to(REPO_ROOT)}")
    return head, evidence_dir


def _file_digest(path: Path) -> str | None:
    if not path.is_file() or path.is_symlink():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _raw_attestation(path: Path) -> ProviderLiveAttestationV1:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return ProviderLiveAttestationV1.model_validate(payload["attestation"])
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise G7Error(f"cannot read the latest live attestation: {error}") from None


def _run_lifecycle(
    target: DirectAcpQualificationTarget,
    *,
    environ: Mapping[str, str],
) -> ProviderLiveAttestationV1:
    path = live_attestation_path(target.harness, environ)
    before = _file_digest(path)
    command = [
        sys.executable,
        "-m",
        "agentteam.cli",
        "runtime",
        "qualify-live",
        "direct-acp",
        "--harness",
        target.harness.value,
        "--json",
    ]
    result = subprocess.run(command, cwd=REPO_ROOT, env=dict(environ), check=False)
    after = _file_digest(path)
    if after is None or after == before:
        if result.returncode == 130:
            raise LifecycleStopped(f"{target.harness.value} lifecycle confirmation was declined")
        raise LifecycleStopped(f"{target.harness.value} lifecycle produced no fresh attestation")
    observed = _raw_attestation(path)
    if result.returncode != 0:
        raise LifecycleStopped(
            f"{target.harness.value} lifecycle stopped after "
            f"{observed.attempted_prompts} attempted prompt(s); status={observed.status}",
            attestation=observed,
        )
    current, problems = load_direct_acp_live_attestation(
        target,
        environ=environ,
        platform=sys.platform,
    )
    if current is None:
        raise LifecycleStopped(
            f"{target.harness.value} passing attestation failed revalidation: "
            + "; ".join(problems),
            attestation=observed,
        )
    if current.attempted_prompts != 5 or len(current.evidence) != 2:
        raise LifecycleStopped(
            f"{target.harness.value} lifecycle did not produce the exact 5/2 shape",
            attestation=current,
        )
    return current


def _extract_paths(raw: object, workspace: Path) -> tuple[Path, ...]:
    if not isinstance(raw, str):
        return ()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return ()
    values: list[str] = []

    def visit(value: object, key: str | None = None) -> None:
        if isinstance(value, dict):
            for child_key, child in value.items():
                visit(child, str(child_key))
        elif isinstance(value, list):
            for child in value:
                visit(child, key)
        elif (
            isinstance(value, str)
            and key is not None
            and any(token in key.lower() for token in ("path", "file", "directory", "cwd"))
        ):
            values.append(value)

    visit(payload)
    normalized: list[Path] = []
    root = workspace.resolve()
    for value in values:
        path = Path(value).expanduser()
        candidate = (path if path.is_absolute() else root / path).resolve(strict=False)
        if candidate not in normalized:
            normalized.append(candidate)
    return tuple(normalized)


def _tool_request(frame: Mapping[str, object], workspace: Path) -> ToolRequest:
    permission_id = frame.get("permission_id")
    classification = frame.get("classification")
    if not isinstance(permission_id, str) or not isinstance(classification, str):
        raise G7Error("permission-awaiting event is missing its exact identity")
    kind = frame.get("tool_kind")
    title = frame.get("tool_title")
    return ToolRequest(
        permission_id=permission_id,
        classification=classification,
        kind=kind if isinstance(kind, str) else "",
        title=title if isinstance(title, str) else "tool",
        paths=_extract_paths(frame.get("tool_input"), workspace),
    )


def _allowed_tool(request: ToolRequest, contract: TurnContract) -> bool:
    declared = {path.resolve() for path in contract.readable}
    workspace_roots = {path.parent.resolve() for path in contract.readable}
    if contract.writable is not None:
        workspace_roots.add(contract.writable.parent.resolve())
    if request.classification == "workspace-write":
        expected = None if contract.writable is None else contract.writable.resolve()
        paths = set(request.paths)
        return (
            expected is not None
            and expected in paths
            and paths.issubset({expected, *workspace_roots})
            and request.kind.lower().replace("_", "-")
            in {"edit", "write", "create", "workspace-write"}
        )
    if request.classification == "workspace-read":
        paths = set(request.paths)
        return (
            bool(paths & declared)
            and paths.issubset(declared | workspace_roots)
            and request.kind.lower().replace("_", "-")
            in {"read", "search", "list", "workspace-read"}
        )
    return False


class NdjsonClient:
    def __init__(self, process: ProcessLike, *, workspace: Path) -> None:
        if process.stdin is None or process.stdout is None:
            raise G7Error("NDJSON child pipes are unavailable")
        self.process = process
        self.stdin = process.stdin
        self.stdout = process.stdout
        self.workspace = workspace
        self.client_sequence = 0
        self.server_sequence = 0
        self.command_sequence = 0
        self.pending: deque[dict[str, object]] = deque()
        self.run_id: str | None = None

    def _send(self, command: str, **data: object) -> str:
        self.command_sequence += 1
        command_id = f"g7-{self.command_sequence}"
        frame = {
            "schema": {"kind": "stream-command", "version": 1},
            "id": command_id,
            "sequence": self.client_sequence,
            "command": command,
            **data,
        }
        self.client_sequence += 1
        self.stdin.write(json.dumps(frame, separators=(",", ":")) + "\n")
        self.stdin.flush()
        return command_id

    def _read_wire(self) -> dict[str, object]:
        line = self.stdout.readline()
        if not line:
            code = self.process.poll()
            raise G7Error(f"NDJSON child ended unexpectedly (exit {code})")
        try:
            frame = json.loads(line)
        except json.JSONDecodeError as error:
            raise G7Error(f"NDJSON child emitted malformed JSON: {error}") from None
        if not isinstance(frame, dict):
            raise G7Error("NDJSON child frame is not an object")
        if frame.get("sequence") != self.server_sequence:
            raise G7Error("NDJSON server sequence is not contiguous")
        self.server_sequence += 1
        schema = frame.get("schema")
        if not isinstance(schema, dict) or schema.get("version") != 1:
            raise G7Error("NDJSON child emitted an unsupported schema")
        run_id = frame.get("run_id")
        if not isinstance(run_id, str) or not run_id:
            raise G7Error("NDJSON child frame has no run id")
        if self.run_id is None:
            self.run_id = run_id
        elif self.run_id != run_id:
            raise G7Error("NDJSON run identity changed mid-stream")
        return cast(dict[str, object], frame)

    def _read(self) -> dict[str, object]:
        return self.pending.popleft() if self.pending else self._read_wire()

    def command(self, command: str, **data: object) -> dict[str, object]:
        command_id = self._send(command, **data)
        deferred: list[dict[str, object]] = []
        while True:
            frame = self._read_wire()
            if frame.get("correlation_id") == command_id and frame.get("schema") == {
                "kind": "stream-receipt",
                "version": 1,
            }:
                self.pending.extend(deferred)
                if frame.get("command") != command:
                    raise G7Error(f"NDJSON receipt mislabeled command {command}")
                if frame.get("status") == "error":
                    raise G7Error(f"NDJSON command {command} failed: {frame.get('error')}")
                return frame
            deferred.append(frame)

    def negotiate(self) -> None:
        receipt = self.command("negotiate", versions=[1], client_mode="attended")
        if receipt.get("status") != "ok" or receipt.get("client_mode") != "attended":
            raise G7Error("attended NDJSON negotiation failed")

    def turn(self, contract: TurnContract) -> str:
        command_id = self._send(
            "turn.start",
            member=contract.member,
            text=contract.prompt,
            **({"work_item_id": contract.work_item} if contract.work_item is not None else {}),
        )
        receipt_seen = False
        violation: str | None = None
        awaiting_writes: dict[str, ToolRequest] = {}

        def record_violation(message: str) -> None:
            nonlocal violation
            if violation is None:
                violation = message

        while True:
            frame = self._read()
            schema = frame.get("schema")
            if schema == {"kind": "stream-receipt", "version": 1}:
                if frame.get("correlation_id") != command_id or receipt_seen:
                    raise G7Error("unexpected receipt while a workflow turn is active")
                if frame.get("status") != "accepted":
                    raise G7Error(f"workflow turn was not accepted: {frame}")
                receipt_seen = True
                continue
            if schema != {"kind": "stream-event", "version": 1}:
                raise G7Error("unexpected NDJSON frame during workflow turn")
            if frame.get("correlation_id") != command_id:
                raise G7Error("workflow event is correlated to a different command")
            event = frame.get("event")
            if event == "permission-awaiting":
                request = _tool_request(frame, self.workspace)
                allowed = _allowed_tool(request, contract)
                if request.permission_id in awaiting_writes:
                    record_violation("duplicate permission identity in one workflow turn")
                if not allowed:
                    record_violation(
                        f"unexpected tool request: {request.classification}/{request.kind}/"
                        f"{[str(path) for path in request.paths]}"
                    )
                approved = False
                if allowed and violation is None:
                    if contract.writable is None:
                        raise G7Error("attended mutation has no declared output path")
                    relative = contract.writable.resolve().relative_to(self.workspace.resolve())
                    approved = _confirm(
                        f"Allow once [{request.classification}/{request.kind}] exact path "
                        f"{relative.as_posix()} (answer within 30 seconds)?"
                    )
                    if not approved:
                        record_violation("attended workspace mutation approval was declined")
                awaiting_writes[request.permission_id] = request
                self.command(
                    "permission.respond",
                    permission_id=request.permission_id,
                    approved=approved,
                    attended=True,
                )
                continue
            if event == "provider-event":
                provider_event = frame.get("provider_event")
                if not isinstance(provider_event, dict):
                    raise G7Error("provider event has an invalid shape")
                if provider_event.get("event") == "permission-request":
                    data = provider_event.get("data")
                    if not isinstance(data, dict):
                        raise G7Error("provider permission event has invalid data")
                    observed = ToolRequest(
                        permission_id=str(data.get("permission_id", "")),
                        classification="",
                        kind=str(data.get("tool_kind", "")),
                        title=str(data.get("tool_title", "tool")),
                        paths=_extract_paths(data.get("tool_input"), self.workspace),
                    )
                    # Reads are auto-decided by the controller and therefore appear only here.
                    kind = observed.kind.lower().replace("_", "-")
                    if kind in {"read", "search", "list", "workspace-read"}:
                        read_request = ToolRequest(
                            observed.permission_id,
                            "workspace-read",
                            observed.kind,
                            observed.title,
                            observed.paths,
                        )
                        if not _allowed_tool(read_request, contract):
                            record_violation("provider attempted an unexpected workspace read")
                    elif kind in {"edit", "write", "create", "workspace-write"}:
                        write_request = ToolRequest(
                            observed.permission_id,
                            "workspace-write",
                            observed.kind,
                            observed.title,
                            observed.paths,
                        )
                        awaited = awaiting_writes.pop(observed.permission_id, None)
                        if awaited is None:
                            record_violation(
                                "provider write had no correlated attended permission request"
                            )
                        elif (
                            awaited.kind != observed.kind
                            or awaited.paths != observed.paths
                            or awaited.classification != "workspace-write"
                        ):
                            record_violation(
                                "provider write details changed after attended permission review"
                            )
                        if not _allowed_tool(write_request, contract):
                            record_violation("provider attempted an unexpected workspace write")
                    else:
                        record_violation(
                            f"provider attempted a prohibited tool kind: {observed.kind}"
                        )
                continue
            if event == "turn-terminal" and frame.get("correlation_id") == command_id:
                result = frame.get("result")
                turn = frame.get("turn")
                if not isinstance(result, dict) or not isinstance(turn, dict):
                    raise G7Error("workflow turn terminal frame is incomplete")
                if not receipt_seen:
                    raise G7Error("workflow turn terminated before its acceptance receipt")
                if awaiting_writes:
                    raise G7Error("workflow turn ended before permission events were correlated")
                if violation is not None:
                    raise G7Error(violation)
                if result.get("status") != "completed":
                    raise G7Error(f"workflow turn failed: {result.get('error')}")
                if result.get("text") != contract.expected_text:
                    raise G7Error("workflow turn response did not match the exact contract")
                turn_id = turn.get("turn_id")
                if not isinstance(turn_id, str):
                    raise G7Error("workflow turn has no committed turn id")
                return turn_id
            raise G7Error(f"unexpected workflow stream event: {event}")

    def abort(self) -> None:
        try:
            self._send("abort")
        except (BrokenPipeError, OSError):
            pass
        finally:
            with contextlib.suppress(OSError):
                self.stdin.close()


def _spawn_workflow(workspace: Path, environ: Mapping[str, str]) -> ProcessLike:
    command = [
        sys.executable,
        "-m",
        "agentteam.cli",
        "team",
        "chat",
        TEAM_ID,
        "--version",
        str(TEAM_VERSION),
        "--workspace",
        str(workspace),
        "--goal",
        "Prove one bounded shared-workspace implement-review-complete workflow.",
        "--done-when",
        DONE_WHEN,
        "--stream-json",
    ]
    return subprocess.Popen(
        command,
        cwd=REPO_ROOT,
        env=dict(environ),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=None,
        text=True,
        encoding="utf-8",
        bufsize=1,
        start_new_session=True,
    )


def _signal_workflow_group(
    process: ProcessLike,
    requested: signal.Signals,
    fallback: Callable[[], None],
) -> None:
    try:
        os.killpg(process.pid, requested)
    except ProcessLookupError:
        return
    except OSError:
        with contextlib.suppress(OSError):
            fallback()


def _reap_failed_workflow(process: ProcessLike, error: BaseException) -> None:
    try:
        process.wait(timeout=30)
        return
    except subprocess.TimeoutExpired:
        _signal_workflow_group(process, signal.SIGTERM, process.terminate)
    try:
        process.wait(timeout=10)
        return
    except subprocess.TimeoutExpired:
        _signal_workflow_group(process, signal.SIGKILL, process.kill)
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        raise G7Error("workflow controller process cleanup is unproven") from error


def _workflow_contracts(workspace: Path, marker: str) -> tuple[TurnContract, ...]:
    implementation = workspace / "implementation.txt"
    review = workspace / "review.txt"
    proposal = workspace / "proposal.txt"
    return (
        TurnContract(
            member="implementer",
            work_item="implement",
            prompt=(
                "Write exactly one file named implementation.txt. Its complete UTF-8 bytes must "
                f"spell implementation marker: {marker}, followed by exactly one LF byte (0A). "
                "Do not include quotes or backslash characters. "
                f"Then reply exactly: IMPLEMENTED {marker}"
            ),
            expected_text=f"IMPLEMENTED {marker}",
            readable=frozenset({implementation}),
            writable=implementation,
        ),
        TurnContract(
            member="reviewer",
            work_item="review",
            prompt=(
                "Read only implementation.txt and verify that its marker is "
                f"{marker}. Write exactly one file named review.txt. Its complete UTF-8 bytes "
                f"must spell reviewed implementation marker: {marker}, followed by exactly one "
                "LF byte (0A). Do not include quotes or backslash characters. "
                f"Then reply exactly: REVIEWED {marker}"
            ),
            expected_text=f"REVIEWED {marker}",
            readable=frozenset({implementation, review}),
            writable=review,
        ),
        TurnContract(
            member="lead",
            work_item="complete",
            prompt=(
                "Read only implementation.txt and review.txt and verify that both contain marker "
                f"{marker}. Write exactly one file named proposal.txt. Its complete UTF-8 bytes "
                f"must spell completion marker: {marker}, followed by exactly one LF byte (0A). "
                "Do not include quotes or backslash characters. "
                f"Then reply exactly: PROPOSED {marker}"
            ),
            expected_text=f"PROPOSED {marker}",
            readable=frozenset({implementation, review, proposal}),
            writable=proposal,
        ),
        TurnContract(
            member="lead",
            work_item=None,
            prompt=(
                "Without reading files or using any tool, recall the marker from your immediately "
                "preceding turn and reply with exactly RECALLED, one space, and that marker."
            ),
            expected_text=f"RECALLED {marker}",
            readable=frozenset(),
            writable=None,
        ),
    )


def _update_work(client: NdjsonClient, item: str, status: TeamTaskStatus) -> None:
    receipt = client.command("work.update", work_item_id=item, status=status.value)
    control = receipt.get("control_receipt")
    if not isinstance(control, dict) or control.get("status") != "applied":
        raise G7Error(f"work transition {item}->{status.value} did not apply")


def _propose(client: NdjsonClient, source_turn_id: str) -> None:
    receipt = client.command(
        "completion.propose",
        source_turn_id=source_turn_id,
        summary="All three bounded workflow artifacts were verified.",
        criteria=[
            {
                "criterion": DONE_WHEN,
                "evidence": ["implementation.txt", "review.txt", "proposal.txt"],
            }
        ],
        work_items=["implement", "review", "complete"],
    )
    control = receipt.get("control_receipt")
    if not isinstance(control, dict) or control.get("status") != "applied":
        raise G7Error("completion proposal did not apply")


def _run_workflow(
    workspace: Path,
    marker: str,
    *,
    candidate_head: str,
    environ: Mapping[str, str],
    attempt_sink: Callable[[int, str | None], None] | None = None,
) -> WorkflowResult:
    if not _confirm("Attempt the exact four-prompt Codex → Claude → Grok → Grok workflow?"):
        raise G7Error("workflow confirmation was declined; attempted workflow prompts: 0")
    process = _spawn_workflow(workspace, environ)
    client = NdjsonClient(process, workspace=workspace)
    turn_ids: list[str] = []
    attempted = 0
    try:
        client.negotiate()
        contracts = _workflow_contracts(workspace, marker)
        for item, contract in zip(("implement", "review", "complete"), contracts[:3], strict=True):
            _update_work(client, item, TeamTaskStatus.RUNNING)
            _candidate_head(candidate_head)
            attempted += 1
            if attempt_sink is not None:
                attempt_sink(attempted, client.run_id)
            turn_ids.append(client.turn(contract))
            _assert_workspace(workspace, marker, completed=len(turn_ids))
            _candidate_head(candidate_head)
            _update_work(client, item, TeamTaskStatus.COMPLETED)
        _propose(client, turn_ids[-1])
        if not _confirm(
            "Reject the first completion proposal and continue this same Lead session?"
        ):
            raise G7Error("first completion rejection was not attended")
        rejected = client.command("completion.reject")
        record = rejected.get("record")
        if not isinstance(record, dict) or record.get("phase") != "open":
            raise G7Error("completion rejection did not reopen the run")
        _candidate_head(candidate_head)
        attempted += 1
        if attempt_sink is not None:
            attempt_sink(attempted, client.run_id)
        turn_ids.append(client.turn(contracts[3]))
        _assert_workspace(workspace, marker, completed=3)
        _candidate_head(candidate_head)
        _propose(client, turn_ids[-1])
        if not _confirm("Accept the second completion proposal and close this run succeeded?"):
            raise G7Error("final completion acceptance was declined")
        accepted = client.command("completion.accept")
        final = accepted.get("record")
        if (
            not isinstance(final, dict)
            or final.get("phase") != "closed"
            or final.get("outcome") != "succeeded"
        ):
            raise G7Error("completion acceptance did not close the run succeeded")
        code = process.wait(timeout=30)
        if code != 0:
            raise G7Error(f"workflow NDJSON child exited {code}")
        if client.run_id is None:
            raise G7Error("workflow produced no run identity")
        return WorkflowResult(client.run_id, tuple(turn_ids), attempted)
    except BaseException as error:
        client.abort()
        _reap_failed_workflow(process, error)
        raise


def _assert_workspace(workspace: Path, marker: str, *, completed: int = 3) -> None:
    all_expected = [
        ("implementation.txt", f"implementation marker: {marker}\n".encode()),
        ("review.txt", f"reviewed implementation marker: {marker}\n".encode()),
        ("proposal.txt", f"completion marker: {marker}\n".encode()),
    ]
    if completed not in {1, 2, 3}:
        raise G7Error("invalid workflow artifact checkpoint")
    expected = dict(all_expected[:completed])
    observed = sorted(path.name for path in workspace.iterdir())
    if observed != sorted(expected):
        raise G7Error(f"workflow workspace has unexpected entries: {observed}")
    for name, content in expected.items():
        path = workspace / name
        if path.is_symlink() or not path.is_file() or path.read_bytes() != content:
            raise G7Error(f"workflow artifact bytes do not match: {name}")


def _assert_workflow_archive(
    run_id: str,
    turn_ids: Sequence[str],
    workspace: Path,
    *,
    environ: Mapping[str, str],
) -> InteractiveArchive:
    runs_root, reservations_root = default_interactive_roots(environ)
    archive = InteractiveArchive(runs_root / run_id, platform=sys.platform)
    record = archive.load_run()
    if (
        record.phase is not InteractiveRunPhase.CLOSED
        or record.outcome is not InteractiveRunOutcome.SUCCEEDED
    ):
        raise G7Error("workflow archive is not closed succeeded")
    if (
        record.target.kind.value != "team"
        or record.target.id != TEAM_ID
        or record.target.version != TEAM_VERSION
        or record.target.content_hash != TEAM_HASH
    ):
        raise G7Error("workflow archive target is not the exact pinned Team fixture")
    member_refs = {
        member.name: (
            member.assistant.id,
            member.assistant.version,
            member.assistant.content_hash,
        )
        for member in record.members
    }
    if member_refs != {
        member: ("m1c-workflow-verifier", 1, ASSISTANT_HASH) for member in WORKFLOW_BINDINGS
    }:
        raise G7Error("workflow archive members do not pin the exact Assistant fixture")
    for member, harness in WORKFLOW_BINDINGS.items():
        launch = archive.load_launch_record(member)
        session_id = next(item.session_id for item in record.members if item.name == member)
        session = archive.load_session(session_id)
        if (
            launch.get("provider") != "direct-acp"
            or launch.get("harness") != harness.value
            or launch.get("assistant_hash") != ASSISTANT_HASH
            or launch.get("generation") != session.generation
            or session.generation != 1
        ):
            raise G7Error(f"workflow launch binding is not exact for Member {member}")
    if list(record.turns) != list(turn_ids) or len(turn_ids) != EXPECTED_WORKFLOW_CALLS:
        raise G7Error("workflow archive does not contain exactly four committed turns")
    members = [archive.load_turn(turn_id).member for turn_id in turn_ids]
    statuses = [archive.load_turn(turn_id).status.value for turn_id in turn_ids]
    if members != ["implementer", "reviewer", "lead", "lead"] or statuses != ["completed"] * 4:
        raise G7Error("workflow turn sequence/status does not match the exact matrix")
    work = [archive.load_work_item(item_id) for item_id in record.work_items]
    if [item.id for item in work] != ["implement", "review", "complete"] or any(
        item.status is not TeamTaskStatus.COMPLETED for item in work
    ):
        raise G7Error("workflow work graph did not complete in order")
    proposals = archive.list_proposals()
    if [proposal.status.value for proposal in proposals] != ["rejected", "accepted"]:
        raise G7Error("workflow completion reject/continue/accept sequence is incomplete")
    if archive.verify_manifest():
        raise G7Error("workflow source manifest failed verification")
    reservation = WorkspaceReservation(reservations_root, platform=sys.platform)
    if reservation.path_for(workspace).exists():
        raise G7Error("workflow workspace reservation was not released")
    for session_id in record.sessions:
        session = archive.load_session(session_id)
        if session.status.value != "closed" or session.close is None:
            raise G7Error("workflow Member session did not close")
        if session.close.process.value not in {"confirmed", "not-applicable"}:
            raise G7Error("workflow Member process stop was not proven")
        if session.close.local_state.value not in {"confirmed", "not-applicable"}:
            raise G7Error("workflow Member local-state deletion was not proven")
    return archive


def _manifest_payload(root: Path) -> dict[str, object]:
    files = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and not path.is_symlink() and path.name != "manifest.sha256.json":
            files.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
    return {"files": files}


def _stage_evidence(
    destination: Path,
    *,
    candidate_head: str,
    hosted_run: str,
    attestations: Mapping[HarnessId, ProviderLiveAttestationV1],
    workflow_run_id: str,
    marker: str,
    evidence_date: str,
    environ: Mapping[str, str],
) -> None:
    ensure_owner_directory(destination.parent, platform=sys.platform)
    staging = Path(tempfile.mkdtemp(prefix=".m1c-live-staging-", dir=destination.parent))
    lifecycle_rows: list[dict[str, object]] = []
    revalidation: list[dict[str, object]] = []
    runs_root, _reservations = default_interactive_roots(environ)
    try:
        for harness in LIFECYCLE_ORDER:
            attestation = attestations[harness]
            lifecycle_rows.append(
                {
                    "harness": harness.value,
                    "attempted_prompts": attestation.attempted_prompts,
                    "status": attestation.status,
                    "run_ids": [item.run_id for item in attestation.evidence],
                }
            )
            attestation_path = staging / "attestations" / f"{harness.value}.json"
            ensure_owner_directory(attestation_path.parent, platform=sys.platform)
            attestation_path.write_bytes(
                _json_bytes(cast(Mapping[str, object], attestation.model_dump(mode="json")))
            )
            for sequence, evidence in enumerate(attestation.evidence, start=1):
                archive = InteractiveArchive(runs_root / evidence.run_id, platform=sys.platform)
                source_problems = archive.verify_manifest()
                if source_problems:
                    raise G7Error(
                        f"source manifest failed for {evidence.run_id}: {source_problems}"
                    )
                source_manifest = archive.root / "manifest.sha256.json"
                if (
                    hashlib.sha256(source_manifest.read_bytes()).hexdigest()
                    != evidence.manifest_sha256
                ):
                    raise G7Error(f"attested manifest digest changed for {evidence.run_id}")
                name = f"{harness.value}-lifecycle-{sequence}"
                exported = archive.export_audit(staging / "runs" / name)
                export_scan = scan_interactive_audit_export(exported)
                if export_scan:
                    raise G7Error(f"export scanner failed for {evidence.run_id}: {export_scan}")
                export_problems = InteractiveArchive(
                    exported,
                    platform=sys.platform,
                ).verify_manifest()
                if export_problems:
                    raise G7Error(
                        f"export manifest failed for {evidence.run_id}: {export_problems}"
                    )
                revalidation.append(
                    {
                        "bundle": name,
                        "run_id": evidence.run_id,
                        "source_manifest": "pass",
                        "attested_manifest_digest": "pass",
                        "export_manifest": "pass",
                        "export_scanner": "pass",
                    }
                )
        workflow_archive = InteractiveArchive(runs_root / workflow_run_id, platform=sys.platform)
        if workflow_archive.verify_manifest():
            raise G7Error("workflow source manifest failed during evidence staging")
        workflow_export = workflow_archive.export_audit(staging / "runs" / "workflow")
        workflow_scan = scan_interactive_audit_export(workflow_export)
        if workflow_scan:
            raise G7Error(f"workflow export scanner failed: {workflow_scan}")
        workflow_export_problems = InteractiveArchive(
            workflow_export,
            platform=sys.platform,
        ).verify_manifest()
        if workflow_export_problems:
            raise G7Error(f"workflow export manifest failed: {workflow_export_problems}")
        revalidation.append(
            {
                "bundle": "workflow",
                "run_id": workflow_run_id,
                "source_manifest": "pass",
                "export_manifest": "pass",
                "export_scanner": "pass",
            }
        )
        ledger: dict[str, object] = {
            "schema_version": 1,
            "kind": "m1c-g7-live-ledger",
            "candidate_head": candidate_head,
            "hosted_non_windows_run": hosted_run,
            "evidence_date": evidence_date,
            "assistant_hash": ASSISTANT_HASH,
            "team_hash": TEAM_HASH,
            "lifecycle": lifecycle_rows,
            "workflow": {
                "run_id": workflow_run_id,
                "attempted_prompts": EXPECTED_WORKFLOW_CALLS,
                "members": ["codex", "claude-code", "grok", "grok"],
                "bindings": [
                    {
                        "member": member,
                        "harness": harness.value,
                        "provider": "direct-acp",
                        "assistant_hash": ASSISTANT_HASH,
                    }
                    for member, harness in WORKFLOW_BINDINGS.items()
                ],
            },
            "counts": {
                "lifecycle": EXPECTED_LIFECYCLE_CALLS,
                "workflow": EXPECTED_WORKFLOW_CALLS,
                "diagnostic": 0,
                "spent": EXPECTED_LIFECYCLE_CALLS + EXPECTED_WORKFLOW_CALLS,
                "ceiling": MAX_TOTAL_CALLS,
                "per_harness": {"claude-code": 6, "codex": 6, "grok": 7},
            },
            "windows": "paused-not-run",
        }
        (staging / "ledger.json").write_bytes(_json_bytes(ledger))
        (staging / "revalidation.json").write_bytes(
            _json_bytes({"bundles": revalidation, "status": "pass"})
        )
        readme = (
            "# M1c G7 live evidence\n\n"
            f"Candidate `{candidate_head}` passed hosted non-Windows run `{hosted_run}` "
            "before live execution. The attended matrix spent exactly 19 of 23 allowed "
            "prompts (15 lifecycle, 4 workflow, 0 diagnostic). Windows was paused and "
            "was not run. Raw transcripts and provider state are intentionally absent.\n"
        )
        (staging / "README.md").write_text(readme, encoding="utf-8")
        if marker.encode("utf-8") in b"".join(
            path.read_bytes() for path in staging.rglob("*") if path.is_file()
        ):
            raise G7Error("workflow marker leaked into sanitized evidence")
        evidence_scan = scan_interactive_audit_export(staging)
        if evidence_scan:
            raise G7Error(f"evidence staging scanner failed: {evidence_scan}")
        (staging / "manifest.sha256.json").write_bytes(_json_bytes(_manifest_payload(staging)))
        final_scan = scan_interactive_audit_export(staging)
        if final_scan:
            raise G7Error(f"final evidence scanner failed: {final_scan}")
        if destination.exists():
            raise G7Error("evidence destination appeared during atomic staging")
        staging.rename(destination)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-head", required=True, help="Exact hosted-green Git HEAD")
    parser.add_argument("--hosted-run", required=True, help="Eight-job green GitHub Actions run id")
    parser.add_argument(
        "--evidence-date",
        default=datetime.now(tz=UTC).date().isoformat(),
        help="UTC evidence directory date (YYYY-MM-DD)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    environ = dict(os.environ)
    attempt_id = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(4)
    attempt_root = _owner_home(environ) / "m1c-g7" / "attempts" / attempt_id
    workspace = attempt_root / "workspace"
    ledger_path = attempt_root / "ledger.json"
    ensure_owner_directory(workspace, platform=sys.platform)
    raw_ledger: dict[str, object] = {
        "schema_version": 1,
        "kind": "m1c-g7-attempt-ledger",
        "attempt_id": attempt_id,
        "status": "preflight",
        "lifecycle": [],
        "workflow_attempted": 0,
        "diagnostic_attempted": 0,
        "ceiling": MAX_TOTAL_CALLS,
    }
    _write_owner_json(ledger_path, raw_ledger)
    candidate_head = ""
    try:
        candidate_head, evidence_dir = _preflight(args, environ)
        targets = _staged_targets(environ)
        _import_fixtures(environ)
        raw_ledger.update(
            {
                "candidate_head": candidate_head,
                "hosted_non_windows_run": args.hosted_run,
                "status": "lifecycle",
            }
        )
        _write_owner_json(ledger_path, raw_ledger)
        attestations: dict[HarnessId, ProviderLiveAttestationV1] = {}
        lifecycle_rows = cast(list[object], raw_ledger["lifecycle"])
        for harness in LIFECYCLE_ORDER:
            _candidate_head(candidate_head)
            try:
                attestation = _run_lifecycle(targets[harness], environ=environ)
            except LifecycleStopped as error:
                if error.attestation is not None:
                    observed = error.attestation
                    lifecycle_rows.append(
                        {
                            "harness": harness.value,
                            "status": observed.status,
                            "attempted_prompts": observed.attempted_prompts,
                        }
                    )
                _write_owner_json(ledger_path, raw_ledger)
                raise
            attestations[harness] = attestation
            lifecycle_rows.append(
                {
                    "harness": harness.value,
                    "status": "pass",
                    "attempted_prompts": attestation.attempted_prompts,
                    "run_ids": [item.run_id for item in attestation.evidence],
                }
            )
            _write_owner_json(ledger_path, raw_ledger)
            _candidate_head(candidate_head)
            remaining_processes = _agent_processes()
            if remaining_processes:
                raise G7Error(
                    f"{harness.value} lifecycle left an agent process: "
                    + "; ".join(remaining_processes)
                )
        if (
            sum(item.attempted_prompts for item in attestations.values())
            != EXPECTED_LIFECYCLE_CALLS
        ):
            raise G7Error("lifecycle ledger did not reconcile to exactly 15 prompts")
        _candidate_head(candidate_head)
        marker = secrets.token_hex(16)
        raw_ledger["status"] = "workflow"
        _write_owner_json(ledger_path, raw_ledger)

        def record_workflow_attempt(attempted: int, run_id: str | None) -> None:
            raw_ledger["workflow_attempted"] = attempted
            if run_id is not None:
                raw_ledger["workflow_run_id"] = run_id
            _write_owner_json(ledger_path, raw_ledger)

        workflow = _run_workflow(
            workspace,
            marker,
            candidate_head=candidate_head,
            environ=environ,
            attempt_sink=record_workflow_attempt,
        )
        raw_ledger["workflow_attempted"] = workflow.attempted_calls
        raw_ledger["workflow_run_id"] = workflow.run_id
        _write_owner_json(ledger_path, raw_ledger)
        if workflow.attempted_calls != EXPECTED_WORKFLOW_CALLS:
            raise G7Error("workflow ledger did not reconcile to exactly four prompts")
        _assert_workspace(workspace, marker)
        _assert_workflow_archive(
            workflow.run_id,
            workflow.turn_ids,
            workspace,
            environ=environ,
        )
        _candidate_head(candidate_head)
        remaining_processes = _agent_processes()
        if remaining_processes:
            raise G7Error("workflow left an agent process: " + "; ".join(remaining_processes))
        _stage_evidence(
            evidence_dir,
            candidate_head=candidate_head,
            hosted_run=args.hosted_run,
            attestations=attestations,
            workflow_run_id=workflow.run_id,
            marker=marker,
            evidence_date=args.evidence_date,
            environ=environ,
        )
        raw_ledger.update(
            {
                "status": "pass",
                "spent": EXPECTED_LIFECYCLE_CALLS + EXPECTED_WORKFLOW_CALLS,
                "ceiling": MAX_TOTAL_CALLS,
                "evidence": evidence_dir.relative_to(REPO_ROOT).as_posix(),
            }
        )
        _write_owner_json(ledger_path, raw_ledger)
        print(
            f"M1c G7 PASS: 19/23 prompts, diagnostics 0; sanitized evidence: "
            f"{evidence_dir.relative_to(REPO_ROOT)}"
        )
        return 0
    except (Exception, KeyboardInterrupt) as error:
        raw_ledger["status"] = "stopped"
        raw_ledger["failure"] = str(error) or type(error).__name__
        if candidate_head:
            raw_ledger["candidate_head"] = candidate_head
        _write_owner_json(ledger_path, raw_ledger)
        print(f"M1c G7 STOPPED: {error}", file=sys.stderr)
        print(f"Partial owner-only ledger: {ledger_path}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
