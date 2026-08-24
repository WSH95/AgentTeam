"""Codex adapter (plan section 11; fact sheet 2026-08-23, codex-cli 0.149.0).

`codex exec` has no `-a/--ask-for-approval` in 0.149.0, so approval is pinned
with `-c approval_policy="never"` (recorded deviation). The structured-output
schema travels by file (`--output-schema`); the final message is read from the
`-o` file because the JSONL event carrying it is not documented — the event
stream is telemetry. Instructions use the workspace `AGENTS.md` channel
(file-delivered) until the G5 probe settles the ladder. Cost is always
`cost_source: unavailable` (plan section 7).
"""

from __future__ import annotations

import json
from typing import Any

from agentteam.domain.run import InjectionV1, ObservedV1, RenderedPartV1, UsageV1
from agentteam.harness.environment import build_environment
from agentteam.harness.parsing import review_from_object
from agentteam.harness.process import ProcessSpec, run_process
from agentteam.harness.rendering import (
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
    ParsedLegV1,
    RawInvocationV1,
    RenderContext,
    RenderedInvocationV1,
)
from agentteam.schema import render as render_schema


class CodexAdapter:
    harness = "codex"

    async def probe(self, context: object) -> HarnessCapabilityReportV1:
        raise NotImplementedError("capability probes arrive at G5")

    def render(self, ctx: RenderContext) -> RenderedInvocationV1:
        instructions = read_instruction_text(ctx)
        task = read_task_text(ctx)

        ctx.workspace_root.mkdir(parents=True, exist_ok=True)
        agents_md = ctx.workspace_root / "AGENTS.md"
        agents_md.write_text(instructions, encoding="utf-8")
        skill_writes: list[FileWriteV1] = (
            []
            if ctx.synthesis is not None
            else write_skills(
                ctx, ctx.workspace_root / ".agents" / "skills", "workspace-agents-skills"
            )
        )

        ctx.scratch_dir.mkdir(parents=True, exist_ok=True)
        schema_file = ctx.scratch_dir / "output-schema.json"
        schema_file.write_text(render_schema(schema_name_for(ctx)), encoding="utf-8")
        output_file = ctx.scratch_dir / "final-message.json"

        env_values, env_record = build_environment(
            ctx.profile, ctx.parent_env, platform=ctx.platform
        )
        env_values[ctx.profile.environment.config_home_variable] = str(ctx.config_root)

        rest = [
            "exec",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--skip-git-repo-check",
            "-C",
            str(ctx.workspace_root),
            "-s",
            "read-only",
            "-c",
            'approval_policy="never"',
            "--output-schema",
            str(schema_file),
            "-o",
            str(output_file),
            "--json",
            "--color",
            "never",
        ]
        if ctx.requested.model is not None:
            rest += ["-m", ctx.requested.model]
        if ctx.requested.effort is not None:
            rest += ["-c", f'model_reasoning_effort="{ctx.requested.effort}"']

        argv, policy = resolve_for_render(ctx, rest)
        guard_argv_length(argv)

        parts = instruction_parts(ctx, "workspace-agents-md")
        parts.append(RenderedPartV1(part="task", channel="stdin"))
        parts.append(RenderedPartV1(part="output-schema", channel="file"))
        parts += [RenderedPartV1(part=w.role, channel=w.channel) for w in skill_writes]

        command, placeholders = build_command_record(
            ctx=ctx,
            profile=ctx.profile,
            argv=argv,
            policy=policy,
            launcher_prefix=len(argv) - len(rest),
            substitutions={
                str(ctx.workspace_root): "<WORKSPACE>",
                str(schema_file): "<SCHEMA_FILE>",
                str(output_file): "<OUT_FILE>",
                str(ctx.config_root): "<CONFIG_HOME>",
                str(ctx.task_file): "<TASK_FILE>",
            },
        )
        from agentteam.harness.types import FileWriteV1

        files = [
            FileWriteV1(path=agents_md, role="instructions", channel="workspace-agents-md"),
            FileWriteV1(path=schema_file, role="output-schema", channel="file"),
            *skill_writes,
        ]
        return RenderedInvocationV1(
            harness=self.harness,
            argv=argv,
            cwd=ctx.workspace_root,
            env_values=env_values,
            stdin_text=task,
            output_file=output_file,
            files_written=files,
            injection=InjectionV1(render=parts),
            command=command,
            environment=env_record,
            placeholders=placeholders,
            schema_channel="file",
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

    def extract_structured(self, raw: RawInvocationV1) -> ExtractedStructured:
        problems: list[str] = []
        usage = UsageV1()  # cost stays unavailable for Codex, always
        observed = ObservedV1()
        events = _parse_jsonl(raw.stdout, problems)
        for event in events:
            if event.get("type") == "turn.completed":
                usage_obj = event.get("usage")
                if isinstance(usage_obj, dict):
                    usage = usage.model_copy(
                        update={
                            "input_tokens": int(usage_obj.get("input_tokens", 0) or 0),
                            "output_tokens": int(usage_obj.get("output_tokens", 0) or 0),
                        }
                    )
        candidate: Any = None
        if raw.output_file_text is not None:
            text = raw.output_file_text.strip()
            try:
                candidate = json.loads(text)
            except json.JSONDecodeError:
                problems.append("final-message file is not JSON")
        else:
            candidate = _final_agent_message(events)
            if candidate is None:
                problems.append("no -o file and no agent_message event found")
        return ExtractedStructured(
            candidate=candidate,
            usage=usage,
            observed=observed,
            problems=problems,
        )

    def parse(self, raw: RawInvocationV1) -> ParsedLegV1:
        extracted = self.extract_structured(raw)
        review, outcome, review_problems = review_from_object(extracted.candidate)
        return ParsedLegV1(
            review=review,
            schema_outcome=outcome,
            usage=extracted.usage,
            observed=extracted.observed,
            problems=extracted.problems + review_problems,
        )


def _parse_jsonl(stdout: bytes, problems: list[str]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in stdout.decode("utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            problems.append(f"non-JSON event line ignored: {line[:60]!r}")
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def _final_agent_message(events: list[dict[str, Any]]) -> Any:
    for event in reversed(events):
        if event.get("type") == "item.completed":
            item = event.get("item")
            if isinstance(item, dict) and item.get("type") == "agent_message":
                text = item.get("text")
                if isinstance(text, str):
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        return None
    return None
