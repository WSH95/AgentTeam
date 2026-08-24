"""Sequential, attended, two-call native-auth capability probes."""

from __future__ import annotations

import contextlib
import json
import os
import secrets
import signal as signal_module
import subprocess
import sys
import time
from collections.abc import Callable, Iterator, Mapping, Set
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agentteam.domain.common import HarnessId
from agentteam.domain.profile import CapabilityRecordV1, HarnessProfileV1, Verification
from agentteam.harness.capabilities import (
    CLAUDE_INSTRUCTION_LADDER,
    CLAUDE_SKILL_LADDER,
    CODEX_INSTRUCTION_LADDER,
    CODEX_SKILL_LADDER,
    GROK_INSTRUCTION_LADDER,
    GROK_OUTPUT_LADDER,
    GROK_SKILL_LADDER,
    readiness_problems,
)
from agentteam.harness.claude import CLAUDE_ALLOWED_TOOLS, CLAUDE_DISALLOWED_TOOLS
from agentteam.harness.environment import build_environment
from agentteam.harness.launcher import resolve_launcher
from agentteam.harness.skills import ManagedSkillsLease
from agentteam.harness.types import RawInvocationV1
from agentteam.profile.capture import ProbeCapture
from agentteam.resolution.profiles import (
    ProfileError,
    atomic_write_text,
    ensure_owner_directory,
    load_profile_set,
    resolve_config_home,
    resolve_profile_executable,
    write_profile_set,
)

ConfirmCall = Callable[[HarnessId, int, str], bool]
MAX_CALLS_PER_HARNESS = 2
MAX_PROBE_SECONDS = 180

_PROBE_SCHEMA = json.dumps(
    {
        "type": "object",
        "properties": {
            "instruction_markers": {"type": "array", "items": {"type": "string"}},
            "skill_markers": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["instruction_markers", "skill_markers"],
        "additionalProperties": False,
    },
    separators=(",", ":"),
)
_TASK = (
    "Load every available Skill whose name begins `agentteam-probe`. Return exactly one "
    "object matching the supplied schema. Report exact opaque markers that are actually "
    "delivered through instruction and Skill channels. Do not guess or invent markers."
)
_GROK_TASK = (
    "Invoke `/agentteam-probe-grok` and `/agentteam-probe-agents` before responding. "
    "Return exactly one object matching the supplied schema. Report exact opaque markers "
    "that are actually delivered through instruction and Skill channels. Do not guess or "
    "invent markers."
)


class ProbeCancelled(Exception):
    """The owner declined or interrupted a call; completed evidence is retained."""

    def __init__(self, results: dict[HarnessId, ProbeHarnessResult]) -> None:
        super().__init__("probe cancelled by owner")
        self.results = results


@dataclass(frozen=True)
class ProbeHarnessResult:
    status: str
    calls_used: int
    capture_id: str | None
    profile_updated: bool


@dataclass(frozen=True)
class ProbeRunResult:
    by_harness: dict[HarnessId, ProbeHarnessResult]
    capture_id: str | None
    all_ready: bool


@dataclass(frozen=True)
class _Recipe:
    argv: list[str]
    cwd: Path
    env: dict[str, str]
    stdin_text: str | None
    output_file: Path | None
    redacted_command: dict[str, Any]
    instruction_markers: dict[str, str]
    skill_markers: dict[str, str]
    attempted_base: tuple[str, ...]


@dataclass(frozen=True)
class _CallAssessment:
    raw: RawInvocationV1
    assessed: dict[str, bool]
    matrix_passed: bool
    output_location: str | None = None


def run_attended_probes(
    profiles: list[HarnessProfileV1],
    *,
    profile_path: Path,
    versions: Mapping[HarnessId, str],
    environ: Mapping[str, str],
    confirm: ConfirmCall,
    platform: str = sys.platform,
    selected_harnesses: Set[HarnessId] | None = None,
    reprobe_ready: bool = False,
) -> ProbeRunResult:
    """Probe in profile order; confirmation occurs immediately before every process."""
    capture: ProbeCapture | None = None
    results: dict[HarnessId, ProbeHarnessResult] = {
        profile.harness: ProbeHarnessResult(
            status="not-selected",
            calls_used=0,
            capture_id=None,
            profile_updated=False,
        )
        for profile in profiles
        if selected_harnesses is not None and profile.harness not in selected_harnesses
    }
    all_ready = True

    for original in profiles:
        if selected_harnesses is not None and original.harness not in selected_harnesses:
            continue
        version = versions[original.harness]
        current = _current_profile(profile_path, original.harness)
        initially_ready = not readiness_problems(current, cli_version=version, needs_skills=True)
        if initially_ready and not reprobe_ready:
            results[original.harness] = ProbeHarnessResult(
                status="already-ready",
                calls_used=0,
                capture_id=None,
                profile_updated=False,
            )
            continue
        if capture is None:
            capture = ProbeCapture.create(profile_path, platform=platform)

        calls_used = 0
        updated = False
        force_next_call = initially_ready and reprobe_ready
        reassessment_passed = False
        for call_number in range(1, MAX_CALLS_PER_HARNESS + 1):
            current = _current_profile(profile_path, original.harness)
            current_ready = not readiness_problems(current, cli_version=version, needs_skills=True)
            if current_ready and not force_next_call:
                break
            force_next_call = False
            description = _call_description(
                current,
                version=version,
                call_number=call_number,
                reassessment=reprobe_ready,
            )
            try:
                confirmed = confirm(original.harness, call_number, description)
            except (KeyboardInterrupt, EOFError):
                results[original.harness] = ProbeHarnessResult(
                    status="cancelled",
                    calls_used=calls_used,
                    capture_id=capture.capture_id,
                    profile_updated=updated,
                )
                raise ProbeCancelled(results) from None
            if not confirmed:
                results[original.harness] = ProbeHarnessResult(
                    status="cancelled",
                    calls_used=calls_used,
                    capture_id=capture.capture_id,
                    profile_updated=updated,
                )
                raise ProbeCancelled(results)

            calls_used += 1
            started = datetime.now(tz=UTC)
            call_dir = capture.begin_call(
                original.harness.value,
                call_number,
                command={"status": "preparing; redacted command follows"},
                started_at=started,
            )
            lease: ManagedSkillsLease | None = None
            recipe = _empty_recipe(
                current,
                call_dir,
                environ,
                platform,
                call_number=call_number,
                version=version,
            )
            try:
                recipe, lease = _build_recipe(
                    current,
                    call_number=call_number,
                    call_dir=call_dir,
                    parent=environ,
                    platform=platform,
                    version=version,
                )
                atomic_write_text(
                    call_dir / "command.redacted.json",
                    json.dumps(recipe.redacted_command, indent=2, sort_keys=True) + "\n",
                    platform=platform,
                )
                raw = _run_probe_process(
                    recipe,
                    timeout_seconds=min(current.timeouts.attempt_seconds, MAX_PROBE_SECONDS),
                    platform=platform,
                )
            except KeyboardInterrupt:
                raw = RawInvocationV1(
                    exit_code=130,
                    signal="SIGINT",
                    stdout=b"",
                    stderr=b"probe interrupted by owner",
                    output_file_text=None,
                    timed_out=False,
                    duration_ms=0,
                    started_at=started,
                    finished_at=datetime.now(tz=UTC),
                )
                capture.finish_call(
                    call_dir,
                    raw=raw,
                    status="cancelled",
                    sanitized_result={"status": "cancelled", "assessed_capabilities": []},
                )
                results[original.harness] = ProbeHarnessResult(
                    status="cancelled",
                    calls_used=calls_used,
                    capture_id=capture.capture_id,
                    profile_updated=updated,
                )
                raise ProbeCancelled(results) from None
            except (OSError, ValueError) as error:
                raw = RawInvocationV1(
                    exit_code=None,
                    signal=None,
                    stdout=b"",
                    stderr=str(error).encode("utf-8", errors="replace"),
                    output_file_text=None,
                    timed_out=False,
                    duration_ms=0,
                    started_at=started,
                    finished_at=datetime.now(tz=UTC),
                )
            finally:
                if lease is not None:
                    lease.close()

            assessment = _assess_call(current.harness, recipe, raw)
            capture.finish_call(
                call_dir,
                raw=raw,
                status=(
                    "timed-out"
                    if raw.timed_out
                    else ("succeeded" if assessment.matrix_passed else "failed")
                ),
                sanitized_result={
                    "status": "passed" if assessment.matrix_passed else "failed",
                    "assessed_capabilities": sorted(assessment.assessed),
                    "verified_capabilities": sorted(
                        name for name, passed in assessment.assessed.items() if passed
                    ),
                    "output_location": assessment.output_location,
                },
            )
            _update_capabilities(
                profile_path,
                current.harness,
                assessment.assessed,
                cli_version=version,
                assessed_at=datetime.now(tz=UTC),
                platform=platform,
            )
            updated = True
            reassessment_passed = reassessment_passed or assessment.matrix_passed
            if reprobe_ready and not assessment.matrix_passed:
                force_next_call = True

        current = _current_profile(profile_path, original.harness)
        ready = not readiness_problems(current, cli_version=version, needs_skills=True)
        if reprobe_ready and initially_ready:
            ready = ready and reassessment_passed
        all_ready = all_ready and ready
        results[original.harness] = ProbeHarnessResult(
            status="passed" if ready else "failed",
            calls_used=calls_used,
            capture_id=capture.capture_id,
            profile_updated=updated,
        )

    return ProbeRunResult(
        by_harness=results,
        capture_id=capture.capture_id if capture is not None else None,
        all_ready=all_ready,
    )


def _build_recipe(
    profile: HarnessProfileV1,
    *,
    call_number: int,
    call_dir: Path,
    parent: Mapping[str, str],
    platform: str,
    version: str,
) -> tuple[_Recipe, ManagedSkillsLease | None]:
    if profile.harness is HarnessId.CLAUDE_CODE:
        return _claude_recipe(
            profile,
            call_number=call_number,
            call_dir=call_dir,
            parent=parent,
            platform=platform,
            version=version,
        )
    if profile.harness is HarnessId.CODEX:
        return (
            _codex_recipe(
                profile,
                call_number=call_number,
                call_dir=call_dir,
                parent=parent,
                platform=platform,
                version=version,
            ),
            None,
        )
    return (
        _grok_recipe(
            profile,
            call_number=call_number,
            call_dir=call_dir,
            parent=parent,
            platform=platform,
            version=version,
        ),
        None,
    )


def _claude_recipe(
    profile: HarnessProfileV1,
    *,
    call_number: int,
    call_dir: Path,
    parent: Mapping[str, str],
    platform: str,
    version: str,
) -> tuple[_Recipe, ManagedSkillsLease | None]:
    workspace = call_dir / "workspace"
    ensure_owner_directory(workspace, platform=platform)
    instruction: dict[str, str] = {}
    skills: dict[str, str] = {}
    lease: ManagedSkillsLease | None = None
    rest = [
        "-p",
        "--output-format",
        "json",
        "--no-session-persistence",
        "--setting-sources",
        "user",
        "--mcp-config",
        json.dumps({"mcpServers": {}}),
        "--strict-mcp-config",
        "--permission-mode",
        "dontAsk",
        "--allowedTools",
        CLAUDE_ALLOWED_TOOLS,
        "--disallowedTools",
        CLAUDE_DISALLOWED_TOOLS,
    ]
    if call_number == 1:
        marker = _marker("INSTRUCTION")
        instruction["append-system-prompt-file"] = marker
        instruction_file = call_dir / "instructions.md"
        atomic_write_text(instruction_file, _instruction_text(marker), platform=platform)
        rest += ["--append-system-prompt-file", str(instruction_file)]
        skill_marker = _marker("SKILL")
        skills["skills-config-home"] = skill_marker
        lease = ManagedSkillsLease(Path(profile.config_home), platform=platform).acquire()
        try:
            _write_probe_skill(
                Path(profile.config_home) / "skills" / "agentteam-probe-config",
                "agentteam-probe-config",
                skill_marker,
                platform=platform,
            )
        except BaseException:
            lease.close()
            raise
    else:
        instruction_missing = not _ladder_current(profile, CLAUDE_INSTRUCTION_LADDER, version)
        skills_missing = not _ladder_current(profile, CLAUDE_SKILL_LADDER, version)
        inline = _marker("INSTRUCTION") if instruction_missing else "AgentTeam probe fallback."
        if instruction_missing:
            instruction["append-system-prompt"] = inline
        rest += ["--append-system-prompt", _instruction_text(inline)]
        if skills_missing:
            plugin_marker = _marker("SKILL")
            workspace_marker = _marker("SKILL")
            skills["skills-plugin-dir"] = plugin_marker
            skills["skills-workspace"] = workspace_marker
            plugin = call_dir / "plugin"
            atomic_write_text(
                plugin / ".claude-plugin" / "plugin.json",
                json.dumps({"name": "agentteam-probe", "version": "1.0.0", "description": "Probe"})
                + "\n",
                platform=platform,
            )
            _write_probe_skill(
                plugin / "skills" / "agentteam-probe-plugin",
                "agentteam-probe-plugin",
                plugin_marker,
                platform=platform,
            )
            _write_probe_skill(
                workspace / ".claude" / "skills" / "agentteam-probe-workspace",
                "agentteam-probe-workspace",
                workspace_marker,
                platform=platform,
            )
            rest += ["--plugin-dir", str(plugin)]
    rest += ["--json-schema", _PROBE_SCHEMA]
    return (
        _recipe(
            profile,
            rest=rest,
            cwd=workspace,
            parent=parent,
            platform=platform,
            stdin_text=_TASK,
            output_file=None,
            instruction=instruction,
            skills=skills,
            base=_base_for_call(
                profile,
                ("headless-json", "structured-output", "native-auth"),
                version=version,
                call_number=call_number,
            ),
        ),
        lease,
    )


def _codex_recipe(
    profile: HarnessProfileV1,
    *,
    call_number: int,
    call_dir: Path,
    parent: Mapping[str, str],
    platform: str,
    version: str,
) -> _Recipe:
    workspace = call_dir / "workspace"
    ensure_owner_directory(workspace, platform=platform)
    instruction: dict[str, str] = {}
    skills: dict[str, str] = {}
    config_args: list[str] = []
    if call_number == 1:
        marker = _marker("INSTRUCTION")
        instruction["instructions-model-instructions-file"] = marker
        instruction_file = call_dir / "model-instructions.md"
        atomic_write_text(instruction_file, _instruction_text(marker), platform=platform)
        config_args = [
            "-c",
            "model_instructions_file=" + json.dumps(str(instruction_file)),
        ]
    else:
        instruction_missing = not _ladder_current(profile, CODEX_INSTRUCTION_LADDER, version)
        developer = _marker("INSTRUCTION") if instruction_missing else "AgentTeam probe fallback."
        if instruction_missing:
            instruction["instructions-developer-instructions"] = developer
            agents = _marker("INSTRUCTION")
            instruction["instructions-workspace-agents-md"] = agents
            atomic_write_text(workspace / "AGENTS.md", _instruction_text(agents), platform=platform)
        config_args = ["-c", "developer_instructions=" + json.dumps(_instruction_text(developer))]

    if call_number == 1 or not _ladder_current(profile, CODEX_SKILL_LADDER, version):
        marker = _marker("SKILL")
        skills["skills-workspace"] = marker
        _write_probe_skill(
            workspace / ".agents" / "skills" / "agentteam-probe",
            "agentteam-probe",
            marker,
            platform=platform,
        )
    schema = call_dir / "output-schema.json"
    atomic_write_text(schema, _PROBE_SCHEMA + "\n", platform=platform)
    output = call_dir / "final-message.json"
    rest = [
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--skip-git-repo-check",
        "-C",
        str(workspace),
        "-s",
        "read-only",
        "-c",
        'approval_policy="never"',
        *config_args,
        "--output-schema",
        str(schema),
        "-o",
        str(output),
        "--json",
        "--color",
        "never",
    ]
    return _recipe(
        profile,
        rest=rest,
        cwd=workspace,
        parent=parent,
        platform=platform,
        stdin_text=_TASK,
        output_file=output,
        instruction=instruction,
        skills=skills,
        base=_base_for_call(
            profile,
            (
                "headless-jsonl",
                "structured-output",
                "output-last-message",
                "jsonl-final-agent-message",
                "native-auth",
            ),
            version=version,
            call_number=call_number,
        ),
    )


def _grok_recipe(
    profile: HarnessProfileV1,
    *,
    call_number: int,
    call_dir: Path,
    parent: Mapping[str, str],
    platform: str,
    version: str,
) -> _Recipe:
    workspace = call_dir / "workspace"
    ensure_owner_directory(workspace, platform=platform)
    prompt = call_dir / "prompt.md"
    atomic_write_text(prompt, _GROK_TASK + "\n", platform=platform)
    instruction: dict[str, str] = {}
    skills: dict[str, str] = {}
    instruction_missing = call_number == 1 or not _ladder_current(
        profile, GROK_INSTRUCTION_LADDER, version
    )
    marker = _marker("INSTRUCTION") if instruction_missing else "AgentTeam probe fallback."
    if instruction_missing:
        capability = (
            "instructions-rules" if call_number == 1 else "instructions-system-prompt-override"
        )
        instruction[capability] = marker
    instruction_flag = "--rules" if call_number == 1 else "--system-prompt-override"

    if call_number == 1 or not _ladder_current(profile, GROK_SKILL_LADDER, version):
        grok_marker = _marker("SKILL")
        agents_marker = _marker("SKILL")
        skills["skills-workspace-grok"] = grok_marker
        skills["skills-workspace-agents"] = agents_marker
        _write_probe_skill(
            workspace / ".grok" / "skills" / "agentteam-probe-grok",
            "agentteam-probe-grok",
            grok_marker,
            platform=platform,
        )
        _write_probe_skill(
            workspace / ".agents" / "skills" / "agentteam-probe-agents",
            "agentteam-probe-agents",
            agents_marker,
            platform=platform,
        )
    rest = [
        "--prompt-file",
        str(prompt),
        "--output-format",
        "json",
        "--no-subagents",
        "--sandbox",
        "read-only",
        instruction_flag,
        _instruction_text(marker),
        "--json-schema",
        _PROBE_SCHEMA,
    ]
    recipe = _recipe(
        profile,
        rest=rest,
        cwd=workspace,
        parent=parent,
        platform=platform,
        stdin_text=None,
        output_file=None,
        instruction=instruction,
        skills=skills,
        base=_base_for_call(
            profile,
            (
                "headless-json",
                "structured-output",
                "prompt-file",
                "structured-output-field",
                "structured-output-text",
                "native-auth",
            ),
            version=version,
            call_number=call_number,
        ),
    )
    recipe.env["GROK_MEMORY"] = "0"
    recipe.redacted_command["environment_names"] = sorted(recipe.env)
    return recipe


def _recipe(
    profile: HarnessProfileV1,
    *,
    rest: list[str],
    cwd: Path,
    parent: Mapping[str, str],
    platform: str,
    stdin_text: str | None,
    output_file: Path | None,
    instruction: dict[str, str],
    skills: dict[str, str],
    base: tuple[str, ...],
) -> _Recipe:
    environment, _record = build_environment(profile, parent, platform=platform)
    launched = resolve_launcher(Path(profile.executable), rest, platform=platform)
    if launched.reason is not None:
        raise ValueError(launched.reason)
    return _Recipe(
        argv=launched.argv,
        cwd=cwd,
        env=environment,
        stdin_text=stdin_text,
        output_file=output_file,
        redacted_command={
            "argv_redacted": _redact_argv(launched.argv, instruction, skills),
            "launcher_policy": launched.policy.value,
            "cwd": "<PROBE_WORKSPACE>",
            "environment_names": sorted(environment),
        },
        instruction_markers=instruction,
        skill_markers=skills,
        attempted_base=base,
    )


def _redact_argv(
    argv: list[str], instruction: Mapping[str, str], skills: Mapping[str, str]
) -> list[str]:
    """Retain flag shape while removing paths, schemas, and generated marker text."""
    safe_values = {
        "exec",
        "json",
        "never",
        "read-only",
        "dontAsk",
        "user",
        CLAUDE_ALLOWED_TOOLS,
        CLAUDE_DISALLOWED_TOOLS,
    }
    markers = set(instruction.values()) | set(skills.values())
    redacted: list[str] = []
    for index, value in enumerate(argv):
        if index == 0:
            redacted.append("<LAUNCHER>")
        elif value.startswith("-") or value in safe_values:
            redacted.append(value)
        elif value == _PROBE_SCHEMA:
            redacted.append("<SCHEMA_JSON>")
        elif any(marker in value for marker in markers):
            redacted.append("<MARKER-BEARING-ARG>")
        elif "=" in value:
            key, _separator, _rest = value.partition("=")
            redacted.append(f"{key}=<REDACTED>")
        else:
            redacted.append("<ARG>")
    return redacted


def _empty_recipe(
    profile: HarnessProfileV1,
    call_dir: Path,
    parent: Mapping[str, str],
    platform: str,
    *,
    call_number: int,
    version: str,
) -> _Recipe:
    instruction_names, skill_names = _channel_capabilities_for_call(
        profile,
        version=version,
        call_number=call_number,
    )
    environment, _record = build_environment(profile, parent, platform=platform)
    return _Recipe(
        argv=[],
        cwd=call_dir,
        env=environment,
        stdin_text=None,
        output_file=None,
        redacted_command={
            "argv_redacted": ["<LAUNCH-FAILED>"],
            "cwd": "<PROBE_WORKSPACE>",
            "environment_names": sorted(environment),
        },
        instruction_markers={name: "<UNAVAILABLE>" for name in instruction_names},
        skill_markers={name: "<UNAVAILABLE>" for name in skill_names},
        attempted_base=_base_for_call(
            profile,
            _base_capabilities(profile.harness),
            version=version,
            call_number=call_number,
        ),
    )


def _channel_capabilities_for_call(
    profile: HarnessProfileV1,
    *,
    version: str,
    call_number: int,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    instruction: tuple[str, ...]
    skills: tuple[str, ...]
    if profile.harness is HarnessId.CLAUDE_CODE:
        if call_number == 1:
            return ("append-system-prompt-file",), ("skills-config-home",)
        instruction = (
            ("append-system-prompt",)
            if not _ladder_current(profile, CLAUDE_INSTRUCTION_LADDER, version)
            else ()
        )
        skills = (
            ("skills-plugin-dir", "skills-workspace")
            if not _ladder_current(profile, CLAUDE_SKILL_LADDER, version)
            else ()
        )
        return instruction, skills
    if profile.harness is HarnessId.CODEX:
        instruction = (
            ("instructions-model-instructions-file",)
            if call_number == 1
            else (
                (
                    "instructions-developer-instructions",
                    "instructions-workspace-agents-md",
                )
                if not _ladder_current(profile, CODEX_INSTRUCTION_LADDER, version)
                else ()
            )
        )
        skills = (
            ("skills-workspace",)
            if call_number == 1 or not _ladder_current(profile, CODEX_SKILL_LADDER, version)
            else ()
        )
        return instruction, skills
    instruction = (
        ("instructions-rules",)
        if call_number == 1
        else (
            ("instructions-system-prompt-override",)
            if not _ladder_current(profile, GROK_INSTRUCTION_LADDER, version)
            else ()
        )
    )
    skills = (
        ("skills-workspace-grok", "skills-workspace-agents")
        if call_number == 1 or not _ladder_current(profile, GROK_SKILL_LADDER, version)
        else ()
    )
    return instruction, skills


def _run_probe_process(recipe: _Recipe, *, timeout_seconds: int, platform: str) -> RawInvocationV1:
    """Run one confirmed probe synchronously so sequential child reaping is deterministic."""
    creationflags = 0
    start_new_session = False
    if platform == "win32":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
    else:
        start_new_session = True
    started_at = datetime.now(tz=UTC)
    started = time.monotonic()
    process = subprocess.Popen(
        recipe.argv,
        cwd=str(recipe.cwd),
        env=recipe.env,
        stdin=subprocess.PIPE if recipe.stdin_text is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=start_new_session,
        creationflags=creationflags,
    )
    stdin_bytes = recipe.stdin_text.encode("utf-8") if recipe.stdin_text is not None else None
    timed_out = False
    try:
        stdout, stderr = process.communicate(stdin_bytes, timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        _terminate_probe_process(process, platform=platform)
        try:
            stdout, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
    except KeyboardInterrupt:
        _terminate_probe_process(process, platform=platform)
        with contextlib.suppress(subprocess.TimeoutExpired):
            process.communicate(timeout=10)
        raise
    finally:
        if process.poll() is None:
            _terminate_probe_process(process, platform=platform)

    output_file_text: str | None = None
    if recipe.output_file is not None and recipe.output_file.is_file():
        output_file_text = recipe.output_file.read_text(encoding="utf-8", errors="replace")
    returncode = process.returncode
    return RawInvocationV1(
        exit_code=returncode if returncode is not None and returncode >= 0 else None,
        signal=_signal_name(returncode),
        stdout=stdout,
        stderr=stderr,
        output_file_text=output_file_text,
        timed_out=timed_out,
        duration_ms=int((time.monotonic() - started) * 1000),
        started_at=started_at,
        finished_at=datetime.now(tz=UTC),
    )


def _terminate_probe_process(process: subprocess.Popen[bytes], *, platform: str) -> None:
    if process.poll() is not None:
        return
    if platform == "win32":
        subprocess.run(
            ["taskkill.exe", "/T", "/F", "/PID", str(process.pid)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return
    try:
        os.killpg(process.pid, signal_module.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=0.5)
    except subprocess.TimeoutExpired:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal_module.SIGKILL)


def _signal_name(returncode: int | None) -> str | None:
    if returncode is None or returncode >= 0:
        return None
    try:
        return signal_module.Signals(-returncode).name
    except ValueError:
        return f"signal-{-returncode}"


def _assess_call(harness: HarnessId, recipe: _Recipe, raw: RawInvocationV1) -> _CallAssessment:
    attempted = {
        name: False
        for name in (
            *recipe.attempted_base,
            *recipe.instruction_markers,
            *recipe.skill_markers,
        )
    }
    if raw.exit_code != 0 or raw.timed_out:
        return _CallAssessment(raw=raw, assessed=attempted, matrix_passed=False)

    candidate: Any = None
    headless = False
    output_location: str | None = None
    jsonl_candidate: Any = None
    if harness is HarnessId.CLAUDE_CODE:
        outer = _json_object(raw.stdout)
        headless = outer is not None
        candidate = outer.get("structured_output") if outer is not None else None
    elif harness is HarnessId.CODEX:
        events = _jsonl_objects(raw.stdout)
        headless = bool(events)
        jsonl_candidate = _codex_final_message(events)
        if raw.output_file_text is not None:
            candidate = _json_object(raw.output_file_text.encode("utf-8"))
    else:
        outer = _json_object(raw.stdout)
        headless = outer is not None
        structured_field = _grok_structured_field(outer)
        if structured_field is not None:
            candidate = structured_field
            output_location = "structured-output-field"
        elif outer is not None and isinstance(outer.get("text"), str):
            candidate = _json_object(outer["text"].encode("utf-8"))
            if candidate is not None:
                output_location = "structured-output-text"

    instruction_seen, skills_seen, structured = _marker_arrays(candidate)
    if harness is HarnessId.CLAUDE_CODE:
        _record_assessment(attempted, "headless-json", headless)
    elif harness is HarnessId.CODEX:
        _record_assessment(attempted, "headless-jsonl", headless)
        _record_assessment(attempted, "output-last-message", structured)
        _record_assessment(
            attempted,
            "jsonl-final-agent-message",
            structured and jsonl_candidate == candidate,
        )
    else:
        _record_assessment(attempted, "headless-json", headless)
        _record_assessment(attempted, "prompt-file", structured)
        if output_location is not None:
            _record_assessment(attempted, output_location, True)

    _record_assessment(attempted, "structured-output", structured)
    _record_assessment(attempted, "native-auth", structured)
    for name, marker in recipe.instruction_markers.items():
        attempted[name] = structured and marker in instruction_seen
    for name, marker in recipe.skill_markers.items():
        attempted[name] = structured and marker in skills_seen
    instruction_passed = not recipe.instruction_markers or any(
        attempted[name] for name in recipe.instruction_markers
    )
    skill_passed = not recipe.skill_markers or any(attempted[name] for name in recipe.skill_markers)
    matrix_passed = (
        structured
        and instruction_passed
        and skill_passed
        and _required_base_passed(harness, attempted)
    )
    return _CallAssessment(
        raw=raw,
        assessed=attempted,
        matrix_passed=matrix_passed,
        output_location=output_location,
    )


def _record_assessment(assessment: dict[str, bool], name: str, passed: bool) -> None:
    if name in assessment:
        assessment[name] = passed


def _grok_structured_field(outer: dict[str, Any] | None) -> dict[str, Any] | None:
    if outer is None:
        return None
    for name in ("structuredOutput", "structured_output"):
        candidate = outer.get(name)
        if isinstance(candidate, dict):
            return candidate
    return None


def _required_base_passed(harness: HarnessId, assessment: Mapping[str, bool]) -> bool:
    optional = {"jsonl-final-agent-message"}
    output_names = set(GROK_OUTPUT_LADDER)
    ordinary = [
        passed
        for name, passed in assessment.items()
        if name not in optional
        and name not in output_names
        and not name.startswith("instructions-")
        and not name.startswith("append-system-prompt")
        and not name.startswith("skills-")
    ]
    if not all(ordinary):
        return False
    attempted_outputs = [assessment[name] for name in GROK_OUTPUT_LADDER if name in assessment]
    return harness is not HarnessId.GROK or not attempted_outputs or any(attempted_outputs)


def _marker_arrays(candidate: Any) -> tuple[set[str], set[str], bool]:
    if not isinstance(candidate, dict):
        return set(), set(), False
    instructions = candidate.get("instruction_markers")
    skills = candidate.get("skill_markers")
    if not isinstance(instructions, list) or not all(isinstance(x, str) for x in instructions):
        return set(), set(), False
    if not isinstance(skills, list) or not all(isinstance(x, str) for x in skills):
        return set(), set(), False
    return set(instructions), set(skills), True


def _json_object(data: bytes) -> dict[str, Any] | None:
    try:
        payload = json.loads(data.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _jsonl_objects(data: bytes) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in data.decode("utf-8", errors="replace").splitlines():
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            events.append(payload)
    return events


def _codex_final_message(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    for event in reversed(events):
        item = event.get("item")
        if event.get("type") != "item.completed" or not isinstance(item, dict):
            continue
        if item.get("type") != "agent_message" or not isinstance(item.get("text"), str):
            continue
        return _json_object(item["text"].encode("utf-8"))
    return None


def _write_probe_skill(root: Path, name: str, marker: str, *, platform: str) -> None:
    body = (
        f"---\nname: {name}\ndescription: AgentTeam probe marker carrier.\n---\n\n"
        f"When asked for opaque Skill markers, report `{marker}` exactly.\n"
    )
    atomic_write_text(root / "SKILL.md", body, platform=platform)


def _instruction_text(marker: str) -> str:
    return f"When asked for opaque instruction markers, report `{marker}` exactly."


def _marker(channel: str) -> str:
    return f"ATM_{channel}_{secrets.token_hex(12).upper()}"


def _ladder_current(profile: HarnessProfileV1, ladder: tuple[str, ...], version: str) -> bool:
    return any(_capability_current(profile, name, version) for name in ladder)


def _capability_current(profile: HarnessProfileV1, name: str, version: str) -> bool:
    row = next((row for row in profile.capabilities if row.name == name), None)
    return (
        row is not None
        and row.verification is Verification.VERIFIED
        and row.cli_version == version
        and row.verified_at is not None
    )


def _base_for_call(
    profile: HarnessProfileV1,
    capabilities: tuple[str, ...],
    *,
    version: str,
    call_number: int,
) -> tuple[str, ...]:
    if call_number == 1:
        return capabilities
    unresolved: list[str] = []
    grok_output_ready = _ladder_current(profile, GROK_OUTPUT_LADDER, version)
    for name in capabilities:
        if name == "jsonl-final-agent-message":
            continue
        if name in GROK_OUTPUT_LADDER and grok_output_ready:
            continue
        if not _capability_current(profile, name, version):
            unresolved.append(name)
    return tuple(unresolved)


def _call_description(
    profile: HarnessProfileV1,
    *,
    version: str,
    call_number: int,
    reassessment: bool = False,
) -> str:
    if call_number == 1:
        channels = {
            HarnessId.CLAUDE_CODE: "prompt-file instructions + config-home Skill",
            HarnessId.CODEX: "model instructions + workspace Skill + schema/-o/JSONL",
            HarnessId.GROK: "rules + both workspace Skill paths + output location",
        }[profile.harness]
    else:
        channels = {
            HarnessId.CLAUDE_CODE: "unresolved inline/plugin/workspace fallbacks",
            HarnessId.CODEX: "unresolved developer/AGENTS.md fallbacks",
            HarnessId.GROK: "unresolved system-prompt/Skill fallbacks",
        }[profile.harness]
    warning = (
        "forced reassessment; failure replaces current capability evidence; "
        if reassessment
        else ""
    )
    return f"{warning}{channels}; version {version}; timeout <= {MAX_PROBE_SECONDS}s"


def _base_capabilities(harness: HarnessId) -> tuple[str, ...]:
    if harness is HarnessId.CLAUDE_CODE:
        return ("headless-json", "structured-output", "native-auth")
    if harness is HarnessId.CODEX:
        return (
            "headless-jsonl",
            "structured-output",
            "output-last-message",
            "jsonl-final-agent-message",
            "native-auth",
        )
    return (
        "headless-json",
        "structured-output",
        "prompt-file",
        "structured-output-field",
        "structured-output-text",
        "native-auth",
    )


def _current_profile(profile_path: Path, harness: HarnessId) -> HarnessProfileV1:
    profile_set = load_profile_set(profile_path)
    try:
        profile = next(profile for profile in profile_set.profiles if profile.harness is harness)
    except StopIteration:
        raise ProfileError(f"profile disappeared during probe: {harness.value}") from None
    return profile.model_copy(
        update={
            "executable": str(resolve_profile_executable(profile_path, profile.executable)),
            "config_home": str(resolve_config_home(profile_path, profile.config_home)),
        }
    )


def _update_capabilities(
    profile_path: Path,
    harness: HarnessId,
    assessment: Mapping[str, bool],
    *,
    cli_version: str,
    assessed_at: datetime,
    platform: str,
) -> None:
    with _profile_lock(profile_path, platform=platform):
        profile_set = load_profile_set(profile_path)
        profiles: list[HarnessProfileV1] = []
        found = False
        for profile in profile_set.profiles:
            if profile.harness is not harness:
                profiles.append(profile)
                continue
            found = True
            by_name = {row.name: row for row in profile.capabilities}
            rows: list[CapabilityRecordV1] = []
            for row in profile.capabilities:
                passed = assessment.get(row.name)
                if passed is None:
                    rows.append(row)
                else:
                    rows.append(
                        row.model_copy(
                            update={
                                "verification": (
                                    Verification.VERIFIED if passed else Verification.UNVERIFIED
                                ),
                                "cli_version": cli_version,
                                "verified_at": assessed_at,
                            }
                        )
                    )
            for name, passed in assessment.items():
                if name not in by_name:
                    rows.append(
                        CapabilityRecordV1(
                            name=name,
                            verification=(
                                Verification.VERIFIED if passed else Verification.UNVERIFIED
                            ),
                            cli_version=cli_version,
                            verified_at=assessed_at,
                        )
                    )
            profiles.append(profile.model_copy(update={"capabilities": rows}))
        if not found:
            raise ProfileError(f"profile disappeared during probe: {harness.value}")
        write_profile_set(
            profile_path,
            profile_set.model_copy(update={"profiles": profiles}),
            platform=platform,
        )


@contextmanager
def _profile_lock(profile_path: Path, *, platform: str) -> Iterator[None]:
    lock_path = Path(profile_path).parent / ".profiles.lock"
    flags = os.O_CREAT | os.O_RDWR
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(lock_path, flags, 0o600)
    try:
        if platform == "win32":
            import msvcrt

            if os.fstat(descriptor).st_size == 0:
                os.write(descriptor, b"0")
            os.lseek(descriptor, 0, os.SEEK_SET)
            msvcrt.locking(descriptor, msvcrt.LK_LOCK, 1)  # type: ignore[attr-defined]
        else:
            import fcntl

            fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        if platform == "win32":
            import msvcrt

            os.lseek(descriptor, 0, os.SEEK_SET)
            msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)  # type: ignore[attr-defined]
        else:
            import fcntl

            fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)
