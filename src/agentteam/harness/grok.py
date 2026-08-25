"""Grok adapter (plan section 11; fact sheet 2026-08-23, grok 1.0.5).

Headless entry uses `--prompt-file` directly (never a bare `-p`, which is the
`--single <PROMPT>` option, nor `grok agent headless`, a WebSocket relay).
`--rules`/`--system-prompt-override` and the structured output location are
selected only after probing. Cost is often absent under subscription OAuth;
`cost_source` is decided per run and never fabricated. The live recipe grants
an explicit `--max-turns` budget: without it, three 2026-08-24 cycles showed
headless grok 1.0.5 either answers in one turn (an empty progress snapshot)
or is vendor-`cancelled` at turn 2 with no final structured object
(ADR 0035); the bound doubles as a hard safety ceiling.
"""

from __future__ import annotations

import json
import os
import secrets
import stat
import tomllib
from collections.abc import Callable
from pathlib import Path

from agentteam.domain.run import InjectionV1, RenderedPartV1, SchemaOutcome, UsageV1
from agentteam.domain.team import WorkspaceAccess
from agentteam.harness.capabilities import (
    GROK_INSTRUCTION_LADDER,
    GROK_OUTPUT_LADDER,
    GROK_SKILL_LADDER,
    select_verified,
)
from agentteam.harness.environment import build_environment
from agentteam.harness.parsing import (
    cost_from_total_usd,
    review_from_object,
    tokens_from_model_usage,
)
from agentteam.harness.process import ProcessSpec, run_process
from agentteam.harness.rendering import (
    RenderError,
    build_command_record,
    guard_argv_length,
    instruction_parts,
    read_instruction_text,
    read_task_text,
    resolve_for_render,
    schema_name_for,
)
from agentteam.harness.skills import write_skills
from agentteam.harness.types import (
    ExtractedStructured,
    FileWriteV1,
    HarnessCapabilityReportV1,
    InvocationScope,
    ParsedLegV1,
    RawInvocationV1,
    RenderContext,
    RenderedInvocationV1,
)
from agentteam.schema import vendor_schema_min

# Explicit agent-turn budget for the live recipe (G6.R6, ADR 0035): generous
# enough for a real multi-turn review with Skill loading, and a hard ceiling
# against runaway loops. Dated capability evidence — revisit on version drift.
GROK_MAX_TURNS = 40


class GrokAdapter:
    harness = "grok"

    def __init__(self, *, token_hex: Callable[[int], str] = secrets.token_hex) -> None:
        self._token_hex = token_hex

    async def probe(self, context: object) -> HarnessCapabilityReportV1:
        raise NotImplementedError("profile doctor owns attended capability probes")

    def render(self, ctx: RenderContext) -> RenderedInvocationV1:
        instructions = read_instruction_text(ctx)
        task = read_task_text(ctx)
        schema_min = vendor_schema_min(schema_name_for(ctx))
        instruction_channel = select_verified(
            ctx.profile, GROK_INSTRUCTION_LADDER, cli_version=ctx.cli_version
        )
        if instruction_channel is None:
            raise RenderError(
                "Grok has no current probe-verified instruction channel; "
                "run `atm profile doctor --probe`"
            )
        output_channel = select_verified(
            ctx.profile, GROK_OUTPUT_LADDER, cli_version=ctx.cli_version
        )
        if output_channel is None:
            raise RenderError(
                "Grok has no current probe-verified structured-output location; "
                "run `atm profile doctor --probe`"
            )
        skill_channel = (
            None
            if ctx.synthesis is not None
            else select_verified(ctx.profile, GROK_SKILL_LADDER, cli_version=ctx.cli_version)
        )
        if ctx.synthesis is None and skill_channel is None:
            raise RenderError(
                "Grok has no current probe-verified Skill channel; run `atm profile doctor --probe`"
            )

        ctx.workspace_root.mkdir(parents=True, exist_ok=True)
        ctx.scratch_dir.mkdir(parents=True, exist_ok=True)
        sandbox_name = "read-only"
        sandbox_write: FileWriteV1 | None = None
        if ctx.invocation_scope is InvocationScope.TEAM_MEMBER:
            if ctx.platform == "win32":
                raise RenderError("Grok team-member sandboxing is unsupported on Windows in M1b")
            nonce = self._token_hex(16)
            if len(nonce) != 32 or any(char not in "0123456789abcdef" for char in nonce):
                raise RenderError("Grok sandbox token source returned an invalid 128-bit nonce")
            suffix = "rw" if ctx.workspace_access is WorkspaceAccess.WORKSPACE_WRITE else "ro"
            sandbox_name = f"agentteam_{nonce}_{suffix}"
            # Guard/create .grok before Skill delivery so a symlinked parent
            # can never redirect workspace-channel writes outside the copy.
            sandbox_write = self._write_team_sandbox(ctx, sandbox_name)
        prompt_file = ctx.scratch_dir / "prompt.md"
        prompt_file.write_text(task, encoding="utf-8")
        skill_writes: list[FileWriteV1] = []
        if skill_channel == "skills-workspace-grok":
            skill_writes = write_skills(
                ctx, ctx.workspace_root / ".grok" / "skills", "workspace-grok-skills"
            )
        elif skill_channel == "skills-workspace-agents":
            skill_writes = write_skills(
                ctx, ctx.workspace_root / ".agents" / "skills", "workspace-agents-skills"
            )

        env_values, env_record = build_environment(
            ctx.profile, ctx.parent_env, platform=ctx.platform
        )
        env_values[ctx.profile.environment.config_home_variable] = str(ctx.config_root)
        env_values["GROK_MEMORY"] = "0"
        env_record = env_record.model_copy(
            update={"names": sorted({*env_record.names, "GROK_MEMORY"})}
        )

        rest = [
            "--prompt-file",
            str(prompt_file),
            "--output-format",
            "json",
            "--no-subagents",
            "--max-turns",
            str(GROK_MAX_TURNS),
            "--sandbox",
            sandbox_name,
            (
                "--rules"
                if instruction_channel == "instructions-rules"
                else "--system-prompt-override"
            ),
            instructions,
            "--json-schema",
            schema_min,
        ]
        if ctx.requested.model is not None:
            rest += ["--model", ctx.requested.model]
        if ctx.requested.effort is not None:
            rest += ["--reasoning-effort", ctx.requested.effort]

        argv, policy = resolve_for_render(ctx, rest)
        guard_argv_length(argv)

        rendered_instruction_channel = (
            "rules-inline"
            if instruction_channel == "instructions-rules"
            else "system-prompt-override-inline"
        )
        parts = instruction_parts(ctx, rendered_instruction_channel)
        parts.append(RenderedPartV1(part="task", channel="prompt-file"))
        parts.append(RenderedPartV1(part="output-schema", channel="argv-inline"))
        parts += [RenderedPartV1(part=w.role, channel=w.channel) for w in skill_writes]

        command, placeholders = build_command_record(
            ctx=ctx,
            profile=ctx.profile,
            argv=argv,
            policy=policy,
            launcher_prefix=len(argv) - len(rest),
            substitutions={
                schema_min: "<SCHEMA_JSON>",
                instructions: "<INSTRUCTIONS_TEXT>",
                str(prompt_file): "<PROMPT_FILE>",
                str(ctx.workspace_root): "<WORKSPACE>",
                str(ctx.config_root): "<CONFIG_HOME>",
            },
        )
        files = [
            FileWriteV1(path=prompt_file, role="prompt", channel="prompt-file"),
            *skill_writes,
            *([sandbox_write] if sandbox_write is not None else []),
        ]
        return RenderedInvocationV1(
            harness=self.harness,
            argv=argv,
            cwd=ctx.workspace_root,
            env_values=env_values,
            stdin_text=None,
            output_file=None,
            files_written=files,
            injection=InjectionV1(render=parts),
            command=command,
            environment=env_record,
            placeholders=placeholders,
            schema_channel="argv-inline",
            timeout_seconds=ctx.timeout_seconds,
            structured_output_channel=output_channel,
        )

    def _write_team_sandbox(self, ctx: RenderContext, name: str) -> FileWriteV1:
        """Create one collision-safe project-local custom sandbox profile."""
        global_file = Path(ctx.profile.config_home) / "sandbox.toml"
        if global_file.exists() or global_file.is_symlink():
            try:
                parsed = tomllib.loads(global_file.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
                raise RenderError(
                    "persistent Grok sandbox.toml is unreadable or malformed"
                ) from error
            profiles = parsed.get("profiles", {})
            if not isinstance(profiles, dict):
                raise RenderError("persistent Grok sandbox.toml has a malformed profiles table")
            if name in profiles:
                raise RenderError(f"generated Grok sandbox profile already exists: {name}")

        project_dir = ctx.workspace_root / ".grok"
        try:
            metadata = project_dir.lstat()
        except FileNotFoundError:
            project_dir.mkdir(mode=0o700, parents=False)
            metadata = project_dir.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise RenderError("workspace .grok must be a real directory")
        if ctx.platform != "win32":
            project_dir.chmod(0o700)

        sandbox_file = project_dir / "sandbox.toml"
        try:
            sandbox_file.lstat()
        except FileNotFoundError:
            pass
        else:
            raise RenderError("workspace .grok/sandbox.toml already exists")

        extends = (
            "workspace" if ctx.workspace_access is WorkspaceAccess.WORKSPACE_WRITE else "read-only"
        )
        document = (f'[profiles.{name}]\nextends = "{extends}"\nrestrict_network = true\n').encode()
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        try:
            descriptor = os.open(sandbox_file, flags, 0o600)
        except OSError as error:
            raise RenderError("cannot exclusively create workspace Grok sandbox profile") from error
        try:
            with os.fdopen(descriptor, "wb") as handle:
                descriptor = -1
                handle.write(document)
        finally:
            if descriptor >= 0:
                os.close(descriptor)
        return FileWriteV1(
            path=sandbox_file,
            role="sandbox-profile",
            channel="workspace-grok-sandbox",
        )

    async def invoke(self, rendered: RenderedInvocationV1) -> RawInvocationV1:
        raw = await run_process(
            ProcessSpec(
                argv=rendered.argv,
                env=rendered.env_values,
                cwd=rendered.cwd,
                stdin_text=rendered.stdin_text,
                timeout_seconds=rendered.timeout_seconds,
                output_file=rendered.output_file,
            )
        )
        return raw.model_copy(
            update={"structured_output_channel": rendered.structured_output_channel}
        )

    def extract_structured(self, raw: RawInvocationV1) -> ExtractedStructured:
        try:
            payload = json.loads(raw.stdout.decode("utf-8", errors="replace"))
        except json.JSONDecodeError as error:
            return ExtractedStructured(
                usage=UsageV1(),
                observed=tokens_from_model_usage(None)[1],
                problems=[f"stdout is not JSON: {error}"],
                hard_failure=True,
            )
        if not isinstance(payload, dict):
            return ExtractedStructured(
                usage=UsageV1(),
                observed=tokens_from_model_usage(None)[1],
                problems=["vendor result is not a JSON object"],
                hard_failure=True,
            )
        if payload.get("type") == "error":
            return ExtractedStructured(
                usage=UsageV1(),
                observed=tokens_from_model_usage(None)[1],
                problems=[f"vendor error: {payload.get('message', 'unknown')}"],
                hard_failure=True,
            )
        candidate = None
        channel = raw.structured_output_channel
        if channel in (None, "structured-output-field"):
            for name in ("structuredOutput", "structured_output"):
                value = payload.get(name)
                if isinstance(value, dict):
                    candidate = value
                    break
        if candidate is None and channel in (None, "structured-output-text"):
            text = payload.get("text")
            if isinstance(text, str):
                try:
                    candidate = json.loads(text)
                except json.JSONDecodeError:
                    candidate = None
        problems: list[str] = []
        if candidate is None:
            # Preserve the vendor's own explanation (`structuredOutput: null`
            # with `structuredOutputError`) on the record for diagnosis on
            # every ladder rung; the verified-field policy still refuses
            # unverified `text` (G6.R2).
            for name in ("structuredOutputError", "structured_output_error"):
                value = payload.get(name)
                if isinstance(value, str) and value:
                    problems.append(f"vendor structured output error: {value}")
                    break
        usage, observed = tokens_from_model_usage(payload.get("modelUsage"))
        raw_usage = payload.get("usage")
        if isinstance(raw_usage, dict):
            usage = usage.model_copy(
                update={
                    "input_tokens": int(raw_usage.get("input_tokens", 0) or 0),
                    "output_tokens": int(raw_usage.get("output_tokens", 0) or 0),
                }
            )
        usage = cost_from_total_usd(usage, payload.get("total_cost_usd"))
        return ExtractedStructured(
            candidate=candidate, usage=usage, observed=observed, problems=problems
        )

    def parse(self, raw: RawInvocationV1) -> ParsedLegV1:
        extracted = self.extract_structured(raw)
        if extracted.hard_failure:
            return ParsedLegV1(
                review=None,
                schema_outcome=SchemaOutcome.MISSING,
                usage=extracted.usage,
                observed=extracted.observed,
                problems=extracted.problems,
            )
        review, outcome, review_problems = review_from_object(extracted.candidate)
        return ParsedLegV1(
            review=review,
            schema_outcome=outcome,
            usage=extracted.usage,
            observed=extracted.observed,
            problems=extracted.problems + review_problems,
        )
