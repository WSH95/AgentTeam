"""Grok adapter rendering (plan sections 9 and 11; fact sheet 2026-08-23)."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from agentteam.harness.grok import GrokAdapter
from agentteam.harness.rendering import RenderError

Builder = Callable[..., Any]


def _only_channels(profile: Any, selected: set[str]) -> Any:
    from agentteam.domain.profile import Verification

    return profile.model_copy(
        update={
            "capabilities": [
                row.model_copy(
                    update={
                        "verification": (
                            Verification.VERIFIED
                            if row.name in selected
                            else Verification.UNVERIFIED
                        )
                    }
                )
                for row in profile.capabilities
            ]
        }
    )


def _fallback_profile(profile: Any) -> Any:
    return _only_channels(
        profile,
        {
            "instructions-system-prompt-override",
            "skills-workspace-agents",
            "structured-output-text",
        },
    )


def _render(builder: Builder, tmp_path: Path, **overrides: object) -> Any:
    ctx = builder("grok", tmp_path, **overrides)
    return GrokAdapter().render(ctx), ctx


def test_golden_argv_and_prompt_file(render_context_builder: Builder, tmp_path: Path) -> None:
    rendered, ctx = _render(render_context_builder, tmp_path)
    argv = rendered.argv
    assert argv[0].endswith("grok")
    assert "-p" not in argv
    prompt_index = argv.index("--prompt-file")
    prompt = Path(argv[prompt_index + 1])
    assert prompt.is_file()
    text = prompt.read_text(encoding="utf-8")
    assert "Review the change" in text
    assert "meticulous senior code reviewer" not in text
    rules_index = argv.index("--rules")
    assert "meticulous senior code reviewer" in argv[rules_index + 1]
    assert argv >= ["--output-format", "json"]
    assert "--no-subagents" in argv
    assert argv >= ["--sandbox", "read-only"]
    schema_index = argv.index("--json-schema")
    assert json.loads(argv[schema_index + 1])["$id"].startswith("urn:agentteam")
    assert rendered.stdin_text is None
    assert rendered.env_values["GROK_HOME"] == str(ctx.config_root)
    assert rendered.env_values["GROK_MEMORY"] == "0"
    channels = {part.part: part.channel for part in rendered.injection.render}
    assert channels["persona"] == "rules-inline"
    assert channels["task"] == "prompt-file"


def test_skills_primary_and_fallback_channels(
    render_context_builder: Builder, tmp_path: Path
) -> None:
    rendered, ctx = _render(render_context_builder, tmp_path)
    for name in ("code-review", "security-review", "test-analysis"):
        assert (ctx.workspace_root / ".grok" / "skills" / name / "SKILL.md").is_file()
    channels = {part.part: part.channel for part in rendered.injection.render}
    assert channels["skill:code-review"] == "workspace-grok-skills"


def test_grok_uses_system_prompt_agents_skills_and_text_location_fallbacks(
    render_context_builder: Builder, tmp_path: Path
) -> None:
    ctx = render_context_builder("grok", tmp_path)
    workspace = tmp_path / "fallback-workspace"
    rendered = GrokAdapter().render(
        ctx.model_copy(
            update={
                "profile": _fallback_profile(ctx.profile),
                "workspace_root": workspace,
                "scratch_dir": tmp_path / "fallback-scratch",
            }
        )
    )
    assert "--system-prompt-override" in rendered.argv
    assert "--rules" not in rendered.argv
    assert (workspace / ".agents" / "skills" / "code-review" / "SKILL.md").is_file()
    assert rendered.structured_output_channel == "structured-output-text"


def test_ladders_skip_stale_verified_primary_channels(
    render_context_builder: Builder, tmp_path: Path
) -> None:
    ctx = render_context_builder("grok", tmp_path)
    stale = {
        "instructions-rules",
        "skills-workspace-grok",
        "structured-output-field",
    }
    profile = ctx.profile.model_copy(
        update={
            "capabilities": [
                row.model_copy(update={"cli_version": "stale-version"})
                if row.name in stale
                else row
                for row in ctx.profile.capabilities
            ]
        }
    )
    workspace = tmp_path / "currency-workspace"
    rendered = GrokAdapter().render(
        ctx.model_copy(
            update={
                "profile": profile,
                "workspace_root": workspace,
                "scratch_dir": tmp_path / "currency-scratch",
            }
        )
    )
    assert "--system-prompt-override" in rendered.argv
    assert "--rules" not in rendered.argv
    assert (workspace / ".agents/skills/code-review/SKILL.md").is_file()
    assert rendered.structured_output_channel == "structured-output-text"


@pytest.mark.parametrize(
    ("channels", "match"),
    [
        (
            {"structured-output-field", "skills-workspace-grok"},
            "instruction channel",
        ),
        ({"instructions-rules", "skills-workspace-grok"}, "structured-output location"),
        ({"instructions-rules", "structured-output-field"}, "Skill channel"),
    ],
)
def test_missing_current_channel_fails_at_the_adapter(
    render_context_builder: Builder,
    tmp_path: Path,
    channels: set[str],
    match: str,
) -> None:
    ctx = render_context_builder("grok", tmp_path)
    profile = _only_channels(ctx.profile, channels)
    with pytest.raises(RenderError, match=match) as error:
        GrokAdapter().render(ctx.model_copy(update={"profile": profile}))
    assert "atm profile doctor --probe" in str(error.value)


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
