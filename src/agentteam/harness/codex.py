"""Codex adapter (plan section 11; fact sheet 2026-08-23, codex-cli 0.149.0).

`codex exec` has no `-a/--ask-for-approval` in 0.149.0, so approval is pinned
with `-c approval_policy="never"` (recorded deviation). The structured-output
schema travels by file (`--output-schema`); the final message is read from the
authoritative `-o` file and the final JSONL agent-message is agreement
telemetry only. Instructions use the first probe-verified channel. Cost is always
`cost_source: unavailable` (plan section 7).
"""

from __future__ import annotations

import json
from typing import Any

from agentteam.domain.run import InjectionV1, ObservedV1, RenderedPartV1, UsageV1
from agentteam.harness.capabilities import (
    CODEX_INSTRUCTION_LADDER,
    CODEX_SKILL_LADDER,
    select_verified,
)
from agentteam.harness.environment import build_environment
from agentteam.harness.parsing import review_from_object
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
    ParsedLegV1,
    RawInvocationV1,
    RenderContext,
    RenderedInvocationV1,
)
from agentteam.schema import render as render_schema


class CodexAdapter:
    harness = "codex"

    async def probe(self, context: object) -> HarnessCapabilityReportV1:
        raise NotImplementedError("profile doctor owns attended capability probes")

    def render(self, ctx: RenderContext) -> RenderedInvocationV1:
        instructions = read_instruction_text(ctx)
        task = read_task_text(ctx)
        instruction_channel = select_verified(ctx.profile, CODEX_INSTRUCTION_LADDER)
        if instruction_channel is None:
            raise RenderError(
                "Codex has no probe-verified instruction channel; run `atm profile doctor --probe`"
            )
        skill_channel = (
            None if ctx.synthesis is not None else select_verified(ctx.profile, CODEX_SKILL_LADDER)
        )
        if ctx.synthesis is None and skill_channel is None:
            raise RenderError(
                "Codex has no probe-verified Skill channel; run `atm profile doctor --probe`"
            )

        ctx.workspace_root.mkdir(parents=True, exist_ok=True)
        ctx.scratch_dir.mkdir(parents=True, exist_ok=True)
        files: list[FileWriteV1] = []
        instruction_config: list[str] = []
        instruction_path: str | None = None
        developer_literal: str | None = None
        if instruction_channel == "instructions-model-instructions-file":
            model_instructions = ctx.scratch_dir / "model-instructions.md"
            model_instructions.write_text(instructions, encoding="utf-8")
            instruction_path = str(model_instructions)
            instruction_config = [
                "-c",
                "model_instructions_file=" + json.dumps(str(model_instructions)),
            ]
            files.append(
                FileWriteV1(
                    path=model_instructions,
                    role="instructions",
                    channel="model-instructions-file",
                )
            )
        elif instruction_channel == "instructions-developer-instructions":
            developer_literal = json.dumps(instructions)
            instruction_config = ["-c", "developer_instructions=" + developer_literal]
        else:
            agents_md = ctx.workspace_root / "AGENTS.md"
            agents_md.write_text(instructions, encoding="utf-8")
            instruction_path = str(agents_md)
            files.append(
                FileWriteV1(
                    path=agents_md,
                    role="instructions",
                    channel="workspace-agents-md",
                )
            )
        skill_writes: list[FileWriteV1] = (
            []
            if ctx.synthesis is not None
            else write_skills(
                ctx, ctx.workspace_root / ".agents" / "skills", "workspace-agents-skills"
            )
        )
        files.extend(skill_writes)

        schema_file = ctx.scratch_dir / "output-schema.json"
        schema_file.write_text(render_schema(schema_name_for(ctx)), encoding="utf-8")
        files.append(FileWriteV1(path=schema_file, role="output-schema", channel="file"))
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
            *instruction_config,
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

        rendered_instruction_channel = {
            "instructions-model-instructions-file": "model-instructions-file",
            "instructions-developer-instructions": "developer-instructions-inline",
            "instructions-workspace-agents-md": "workspace-agents-md",
        }[instruction_channel]
        parts = instruction_parts(ctx, rendered_instruction_channel)
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
                **({instruction_path: "<INSTRUCTIONS_FILE>"} if instruction_path else {}),
                **(
                    {developer_literal: "<INSTRUCTIONS_TEXT_JSON>"}
                    if developer_literal is not None
                    else {}
                ),
            },
        )
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
        event_candidate = _final_agent_message(events)
        if raw.output_file_text is not None:
            text = raw.output_file_text.strip()
            try:
                candidate = json.loads(text)
            except json.JSONDecodeError:
                problems.append("final-message file is not JSON")
            if candidate is not None and event_candidate is not None:
                if event_candidate == candidate:
                    problems.append("JSONL final agent_message agrees with the -o file")
                else:
                    problems.append(
                        "JSONL final agent_message disagrees with the authoritative -o file"
                    )
        else:
            problems.append("authoritative -o final-message file is missing")
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
