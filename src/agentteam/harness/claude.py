"""Claude Code adapter (plan section 11; fact sheet 2026-08-23, claude 2.1.241).

Isolation: fresh `CLAUDE_CONFIG_DIR` + `--setting-sources user` +
`--strict-mcp-config` with an AgentTeam-written empty `--mcp-config` + explicit
tool restriction + `--no-session-persistence`. Never `--safe-mode` (disables
Skills), never `--bare` (never reads OAuth). Instructions travel through
`--append-system-prompt` with text AgentTeam reads from the rendered files —
the plan's pre-probe fallback; the `--append-system-prompt-file` upgrade and
the Skill-channel choice are G5 probe outcomes carried as profile data.
"""

from __future__ import annotations

import json

from agentteam.domain.run import InjectionV1, RenderedPartV1, SchemaOutcome, UsageV1
from agentteam.harness.environment import build_environment
from agentteam.harness.parsing import (
    cost_from_total_usd,
    review_from_object,
    tokens_from_model_usage,
)
from agentteam.harness.process import ProcessSpec, run_process
from agentteam.harness.rendering import (
    build_command_record,
    guard_argv_length,
    read_instruction_text,
    read_task_text,
    resolve_for_render,
)
from agentteam.harness.skills import write_skills
from agentteam.harness.types import (
    HarnessCapabilityReportV1,
    ParsedLegV1,
    RawInvocationV1,
    RenderContext,
    RenderedInvocationV1,
)
from agentteam.schema import vendor_schema_min

# Read-only review toolset (plan section 11: read-only review tools).
_ALLOWED_TOOLS = "Read,Grep,Glob,LS"
_DISALLOWED_TOOLS = "Write,Edit,NotebookEdit,Bash,WebFetch,WebSearch"


class ClaudeAdapter:
    harness = "claude-code"

    async def probe(self, context: object) -> HarnessCapabilityReportV1:
        raise NotImplementedError("capability probes arrive at G5")

    def render(self, ctx: RenderContext) -> RenderedInvocationV1:
        instructions = read_instruction_text(ctx)
        task = read_task_text(ctx)
        schema_min = vendor_schema_min("normalized-review-v1.schema.json")
        skill_writes = write_skills(ctx, ctx.config_root / "skills", "config-home-skills")

        env_values, env_record = build_environment(
            ctx.profile, ctx.parent_env, platform=ctx.platform
        )
        env_values[ctx.profile.environment.config_home_variable] = str(ctx.config_root)

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
            _ALLOWED_TOOLS,
            "--disallowedTools",
            _DISALLOWED_TOOLS,
            "--append-system-prompt",
            instructions,
            "--json-schema",
            schema_min,
        ]
        if ctx.requested.model is not None:
            rest += ["--model", ctx.requested.model]
        if ctx.requested.effort is not None:
            rest += ["--effort", ctx.requested.effort]

        argv, policy = resolve_for_render(ctx, rest)
        guard_argv_length(argv)

        parts = [
            RenderedPartV1(part="persona", channel="append-system-prompt-inline"),
            RenderedPartV1(part="principles", channel="append-system-prompt-inline"),
        ]
        if ctx.definition.methods is not None:
            parts.append(RenderedPartV1(part="methods", channel="append-system-prompt-inline"))
        parts.append(RenderedPartV1(part="task", channel="stdin"))
        parts.append(RenderedPartV1(part="output-schema", channel="argv-inline"))
        parts += [RenderedPartV1(part=write.role, channel=write.channel) for write in skill_writes]

        command, placeholders = build_command_record(
            ctx=ctx,
            profile=ctx.profile,
            argv=argv,
            policy=policy,
            substitutions={
                instructions: "<INSTRUCTIONS_TEXT>",
                schema_min: "<SCHEMA_JSON>",
                str(ctx.workspace): "<WORKSPACE>",
                str(ctx.config_root): "<CONFIG_HOME>",
                str(ctx.task_file): "<TASK_FILE>",
            },
        )
        return RenderedInvocationV1(
            harness=self.harness,
            argv=argv,
            cwd=ctx.workspace,
            env_values=env_values,
            stdin_text=task,
            output_file=None,
            files_written=skill_writes,
            injection=InjectionV1(render=parts),
            command=command,
            environment=env_record,
            placeholders=placeholders,
            schema_channel="argv-inline",
            timeout_seconds=ctx.timeout_seconds,
        )

    async def invoke(self, rendered: RenderedInvocationV1) -> RawInvocationV1:
        return await run_process(
            ProcessSpec(
                argv=rendered.argv,
                env=rendered.env_values,
                cwd=rendered.cwd,
                stdin_text=rendered.stdin_text,
                timeout_seconds=rendered.timeout_seconds,
                output_file=rendered.output_file,
            )
        )

    def parse(self, raw: RawInvocationV1) -> ParsedLegV1:
        problems: list[str] = []
        try:
            payload = json.loads(raw.stdout.decode("utf-8", errors="replace"))
        except json.JSONDecodeError as error:
            return ParsedLegV1(
                review=None,
                schema_outcome=SchemaOutcome.MISSING,
                usage=UsageV1(),
                observed=tokens_from_model_usage(None)[1],
                problems=[f"stdout is not JSON: {error}"],
            )
        structured = payload.get("structured_output")
        review, outcome, review_problems = review_from_object(structured)
        problems.extend(review_problems)
        usage, observed = tokens_from_model_usage(payload.get("modelUsage"))
        usage = cost_from_total_usd(usage, payload.get("total_cost_usd"))
        return ParsedLegV1(
            review=review,
            schema_outcome=outcome,
            usage=usage,
            observed=observed,
            problems=problems,
        )
