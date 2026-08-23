"""Grok adapter rendering (plan sections 9 and 11; fact sheet 2026-08-23)."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from agentteam.harness.grok import GrokAdapter

Builder = Callable[..., Any]


def _render(builder: Builder, tmp_path: Path, **overrides: object) -> Any:
    ctx = builder("grok", tmp_path, **overrides)
    return GrokAdapter().render(ctx), ctx


def test_golden_argv_and_prompt_file(render_context_builder: Builder, tmp_path: Path) -> None:
    rendered, ctx = _render(render_context_builder, tmp_path)
    argv = rendered.argv
    assert argv[0].endswith("grok")
    assert "-p" in argv
    prompt_index = argv.index("--prompt-file")
    prompt = Path(argv[prompt_index + 1])
    assert prompt.is_file()
    text = prompt.read_text(encoding="utf-8")
    # preamble carries the instructions, then the task
    assert "meticulous senior code reviewer" in text
    assert text.index("meticulous") < text.index("Review the change")
    assert argv >= ["--output-format", "json"]
    assert "--no-subagents" in argv
    assert argv >= ["--sandbox", "read-only"]
    schema_index = argv.index("--json-schema")
    assert json.loads(argv[schema_index + 1])["$id"].startswith("urn:agentteam")
    assert rendered.stdin_text is None
    assert rendered.env_values["GROK_HOME"] == str(ctx.config_root)
    assert rendered.env_values["GROK_MEMORY"] == "0"
    channels = {part.part: part.channel for part in rendered.injection.render}
    assert channels["persona"] == "prompt-file-preamble"
    assert channels["task"] == "prompt-file"


def test_skills_primary_and_fallback_channels(
    render_context_builder: Builder, tmp_path: Path
) -> None:
    rendered, ctx = _render(render_context_builder, tmp_path)
    for name in ("code-review", "security-review", "test-analysis"):
        assert (ctx.workspace_root / ".grok" / "skills" / name / "SKILL.md").is_file()
    channels = {part.part: part.channel for part in rendered.injection.render}
    assert channels["skill:code-review"] == "workspace-grok-skills"


def test_effort_flag(render_context_builder: Builder, tmp_path: Path) -> None:
    from agentteam.domain.common import HarnessId
    from agentteam.domain.run import RequestedV1

    rendered, _ = _render(
        render_context_builder,
        tmp_path,
        requested=RequestedV1(harness=HarnessId.GROK, model="grok-build", effort="high"),
    )
    argv = rendered.argv
    assert argv >= ["--model", "grok-build"]
    assert argv >= ["--reasoning-effort", "high"]
