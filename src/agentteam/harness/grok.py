"""Grok adapter (plan section 11; fact sheet 2026-08-23, grok 1.0.5).

Headless entry is `grok -p` with `--prompt-file` (never `grok agent headless`,
a WebSocket relay). `--rules`/`--system-prompt-override` are inline-only, so
the instructions travel as a prompt-file preamble ahead of the task (file
delivery, recorded as `prompt-file-preamble`). Where the structured output
lands under plain `--output-format json` is undocumented until the G5 probe:
the parser accepts a `structured_output` field or `text` that parses as the
review JSON. Cost is often absent under subscription OAuth; `cost_source` is
decided per run and never fabricated.
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
    FileWriteV1,
    HarnessCapabilityReportV1,
    ParsedLegV1,
    RawInvocationV1,
    RenderContext,
    RenderedInvocationV1,
)
from agentteam.schema import vendor_schema_min


class GrokAdapter:
    harness = "grok"

    async def probe(self, context: object) -> HarnessCapabilityReportV1:
        raise NotImplementedError("capability probes arrive at G5")

    def render(self, ctx: RenderContext) -> RenderedInvocationV1:
        instructions = read_instruction_text(ctx)
        task = read_task_text(ctx)
        schema_min = vendor_schema_min("normalized-review-v1.schema.json")

        ctx.scratch_dir.mkdir(parents=True, exist_ok=True)
        prompt_file = ctx.scratch_dir / "prompt.md"
        prompt_file.write_text(instructions + "\n---\n\n# Task\n\n" + task, encoding="utf-8")
        skill_writes = write_skills(
            ctx, ctx.workspace_root / ".grok" / "skills", "workspace-grok-skills"
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
            "-p",
            "--prompt-file",
            str(prompt_file),
            "--output-format",
            "json",
            "--no-subagents",
            "--sandbox",
            "read-only",
            "--json-schema",
            schema_min,
        ]
        if ctx.requested.model is not None:
            rest += ["--model", ctx.requested.model]
        if ctx.requested.effort is not None:
            rest += ["--reasoning-effort", ctx.requested.effort]

        argv, policy = resolve_for_render(ctx, rest)
        guard_argv_length(argv)

        parts = [
            RenderedPartV1(part="persona", channel="prompt-file-preamble"),
            RenderedPartV1(part="principles", channel="prompt-file-preamble"),
        ]
        if ctx.definition.methods is not None:
            parts.append(RenderedPartV1(part="methods", channel="prompt-file-preamble"))
        parts.append(RenderedPartV1(part="task", channel="prompt-file"))
        parts.append(RenderedPartV1(part="output-schema", channel="argv-inline"))
        parts += [RenderedPartV1(part=w.role, channel=w.channel) for w in skill_writes]

        command, placeholders = build_command_record(
            ctx=ctx,
            profile=ctx.profile,
            argv=argv,
            policy=policy,
            substitutions={
                schema_min: "<SCHEMA_JSON>",
                str(prompt_file): "<PROMPT_FILE>",
                str(ctx.workspace_root): "<WORKSPACE>",
                str(ctx.config_root): "<CONFIG_HOME>",
            },
        )
        files = [
            FileWriteV1(path=prompt_file, role="prompt", channel="prompt-file"),
            *skill_writes,
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
        if isinstance(payload, dict) and payload.get("type") == "error":
            return ParsedLegV1(
                review=None,
                schema_outcome=SchemaOutcome.MISSING,
                usage=UsageV1(),
                observed=tokens_from_model_usage(None)[1],
                problems=[f"vendor error: {payload.get('message', 'unknown')}"],
            )
        candidate = payload.get("structured_output")
        if candidate is None:
            text = payload.get("text")
            if isinstance(text, str):
                try:
                    candidate = json.loads(text)
                except json.JSONDecodeError:
                    candidate = None
        review, outcome, review_problems = review_from_object(candidate)
        problems.extend(review_problems)
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
        return ParsedLegV1(
            review=review,
            schema_outcome=outcome,
            usage=usage,
            observed=observed,
            problems=problems,
        )
