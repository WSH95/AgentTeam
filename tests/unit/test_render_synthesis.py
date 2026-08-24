"""Synthesis rendering (plan section 12 steps 11): same adapters, no skills,
synthesis instructions instead of the definition, SynthesisReportV1 schema."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from agentteam.harness.claude import ClaudeAdapter
from agentteam.harness.codex import CodexAdapter
from agentteam.harness.grok import GrokAdapter
from agentteam.harness.rendering import RenderError
from agentteam.harness.types import SynthesisRenderV1
from agentteam.schema import vendor_schema, vendor_schema_text

Builder = Callable[..., Any]

INSTRUCTIONS = "Merge the labelled reviews; attribute by invocation id.\n"


def _synthesis_ctx(builder: Builder, harness: str, tmp_path: Path) -> Any:
    instructions = tmp_path / "instructions.md"
    instructions.write_text(INSTRUCTIONS, encoding="utf-8")
    return builder(
        harness,
        tmp_path,
        synthesis=SynthesisRenderV1(instructions_file=instructions),
        invocation_id="inv-synthesis",
    )


def test_claude_synthesis_render_swaps_schema_and_skips_skills(
    render_context_builder: Builder, tmp_path: Path
) -> None:
    ctx = _synthesis_ctx(render_context_builder, "claude-code", tmp_path)
    rendered = ClaudeAdapter().render(ctx)
    schema_arg = rendered.argv[rendered.argv.index("--json-schema") + 1]
    assert json.loads(schema_arg) == vendor_schema("synthesis-report-v1.schema.json")
    prompt_path = Path(rendered.argv[rendered.argv.index("--append-system-prompt-file") + 1])
    assert prompt_path.read_text(encoding="utf-8") == INSTRUCTIONS
    assert not (ctx.config_root / "skills").exists()
    parts = {part.part for part in rendered.injection.render}
    assert "synthesis-instructions" in parts
    assert "persona" not in parts
    assert not any(part.startswith("skill:") for part in parts)
    assert {write.role for write in rendered.files_written} == {"instructions"}


def test_codex_synthesis_render_swaps_schema_and_skips_skills(
    render_context_builder: Builder, tmp_path: Path
) -> None:
    ctx = _synthesis_ctx(render_context_builder, "codex", tmp_path)
    rendered = CodexAdapter().render(ctx)
    model_arg = next(arg for arg in rendered.argv if arg.startswith("model_instructions_file="))
    model_file = Path(model_arg.partition("=")[2].strip('"'))
    assert model_file.read_text(encoding="utf-8") == INSTRUCTIONS
    schema_file = ctx.scratch_dir / "output-schema.json"
    assert schema_file.read_text(encoding="utf-8") == vendor_schema_text(
        "synthesis-report-v1.schema.json"
    )
    assert not (ctx.workspace_root / ".agents" / "skills").exists()
    parts = {part.part for part in rendered.injection.render}
    assert "synthesis-instructions" in parts
    assert "persona" not in parts
    roles = {write.role for write in rendered.files_written}
    assert not any(role.startswith("skill:") for role in roles)


def test_grok_synthesis_render_swaps_schema_and_skips_skills(
    render_context_builder: Builder, tmp_path: Path
) -> None:
    ctx = _synthesis_ctx(render_context_builder, "grok", tmp_path)
    rendered = GrokAdapter().render(ctx)
    schema_arg = rendered.argv[rendered.argv.index("--json-schema") + 1]
    assert json.loads(schema_arg) == vendor_schema("synthesis-report-v1.schema.json")
    prompt_file = ctx.scratch_dir / "prompt.md"
    assert prompt_file.read_text(encoding="utf-8") == "Review the change in target.ts.\n"
    assert rendered.argv[rendered.argv.index("--rules") + 1] == INSTRUCTIONS
    assert not (ctx.workspace_root / ".grok" / "skills").exists()
    parts = {part.part for part in rendered.injection.render}
    assert "synthesis-instructions" in parts
    assert "persona" not in parts


def test_default_render_still_uses_the_review_schema(
    render_context_builder: Builder, tmp_path: Path
) -> None:
    ctx = render_context_builder("claude-code", tmp_path)
    rendered = ClaudeAdapter().render(ctx)
    schema_arg = rendered.argv[rendered.argv.index("--json-schema") + 1]
    assert json.loads(schema_arg) == vendor_schema("normalized-review-v1.schema.json")
    parts = {part.part for part in rendered.injection.render}
    assert "persona" in parts
    assert "synthesis-instructions" not in parts


def test_missing_synthesis_instructions_fail_before_launch(
    render_context_builder: Builder, tmp_path: Path
) -> None:
    ctx = render_context_builder(
        "claude-code",
        tmp_path,
        synthesis=SynthesisRenderV1(instructions_file=tmp_path / "absent.md"),
    )
    with pytest.raises(RenderError) as excinfo:
        ClaudeAdapter().render(ctx)
    assert any(
        part.part == "synthesis-instructions" for part in excinfo.value.undeliverable_required_parts
    )
