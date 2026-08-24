"""Codex adapter rendering (plan sections 9 and 11; fact sheet 2026-08-23)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from agentteam.harness.codex import CodexAdapter
from agentteam.harness.rendering import RenderError

Builder = Callable[..., Any]


def _only_channels(profile: Any, names: set[str]) -> Any:
    from agentteam.domain.profile import Verification

    return profile.model_copy(
        update={
            "capabilities": [
                row.model_copy(
                    update={
                        "verification": (
                            Verification.VERIFIED if row.name in names else Verification.UNVERIFIED
                        )
                    }
                )
                for row in profile.capabilities
            ]
        }
    )


def _only_instruction_channel(profile: Any, name: str) -> Any:
    return _only_channels(profile, {name, "skills-workspace"})


def _render(builder: Builder, tmp_path: Path, **overrides: object) -> Any:
    ctx = builder("codex", tmp_path, **overrides)
    return CodexAdapter().render(ctx), ctx


def test_golden_argv(render_context_builder: Builder, tmp_path: Path) -> None:
    rendered, ctx = _render(render_context_builder, tmp_path)
    argv = rendered.argv
    assert argv[0].endswith("codex")
    assert argv[1] == "exec"
    for flag in ("--ephemeral", "--ignore-user-config", "--ignore-rules", "--skip-git-repo-check"):
        assert flag in argv
    assert ["-C", str(ctx.workspace_root)] <= argv
    assert argv >= ["-s", "read-only"]
    assert argv >= ["-c", 'approval_policy="never"']
    schema_index = argv.index("--output-schema")
    schema_file = Path(argv[schema_index + 1])
    assert schema_file.is_file() and schema_file.name == "output-schema.json"
    out_index = argv.index("-o")
    assert Path(argv[out_index + 1]).name == "final-message.json"
    assert "--json" in argv
    assert argv >= ["--color", "never"]
    assert rendered.stdin_text is not None and "Review the change" in rendered.stdin_text
    assert rendered.schema_channel == "file"
    assert rendered.output_file is not None
    assert rendered.env_values["CODEX_HOME"] == str(ctx.config_root)


def test_instructions_use_the_verified_model_instructions_file(
    render_context_builder: Builder, tmp_path: Path
) -> None:
    rendered, _ctx = _render(render_context_builder, tmp_path)
    value = next(arg for arg in rendered.argv if arg.startswith("model_instructions_file="))
    path = Path(value.partition("=")[2].strip('"'))
    text = path.read_text(encoding="utf-8")
    assert "meticulous senior code reviewer" in text  # persona
    assert "Evidence over impression" in text  # principles
    channels = {part.part: part.channel for part in rendered.injection.render}
    assert channels["persona"] == "model-instructions-file"
    assert channels["task"] == "stdin"


def test_instruction_ladder_falls_back_to_developer_then_agents_md(
    render_context_builder: Builder, tmp_path: Path
) -> None:
    ctx = render_context_builder("codex", tmp_path)
    developer_profile = _only_instruction_channel(
        ctx.profile, "instructions-developer-instructions"
    )
    developer = CodexAdapter().render(ctx.model_copy(update={"profile": developer_profile}))
    assert any(arg.startswith("developer_instructions=") for arg in developer.argv)
    assert not (ctx.workspace_root / "AGENTS.md").exists()

    agents_profile = _only_instruction_channel(ctx.profile, "instructions-workspace-agents-md")
    agents_root = tmp_path / "agents-fallback"
    agents = CodexAdapter().render(
        ctx.model_copy(
            update={
                "profile": agents_profile,
                "workspace_root": agents_root,
                "scratch_dir": tmp_path / "agents-scratch",
            }
        )
    )
    assert (agents_root / "AGENTS.md").is_file()
    assert not any(arg.startswith("developer_instructions=") for arg in agents.argv)


def test_instruction_ladder_skips_a_stale_verified_primary(
    render_context_builder: Builder, tmp_path: Path
) -> None:
    ctx = render_context_builder("codex", tmp_path)
    profile = ctx.profile.model_copy(
        update={
            "capabilities": [
                row.model_copy(update={"cli_version": "stale-version"})
                if row.name == "instructions-model-instructions-file"
                else row
                for row in ctx.profile.capabilities
            ]
        }
    )
    rendered = CodexAdapter().render(ctx.model_copy(update={"profile": profile}))
    assert any(arg.startswith("developer_instructions=") for arg in rendered.argv)
    assert not any(arg.startswith("model_instructions_file=") for arg in rendered.argv)


@pytest.mark.parametrize(
    ("channels", "match"),
    [
        ({"skills-workspace"}, "instruction channel"),
        ({"instructions-model-instructions-file"}, "Skill channel"),
    ],
)
def test_missing_current_channel_fails_at_the_adapter(
    render_context_builder: Builder,
    tmp_path: Path,
    channels: set[str],
    match: str,
) -> None:
    ctx = render_context_builder("codex", tmp_path)
    profile = _only_channels(ctx.profile, channels)
    with pytest.raises(RenderError, match=match) as error:
        CodexAdapter().render(ctx.model_copy(update={"profile": profile}))
    assert "atm profile doctor --probe" in str(error.value)


def test_skills_go_to_workspace_agents_skills(
    render_context_builder: Builder, tmp_path: Path
) -> None:
    rendered, ctx = _render(render_context_builder, tmp_path)
    for name in ("code-review", "security-review", "test-analysis"):
        assert (ctx.workspace_root / ".agents" / "skills" / name / "SKILL.md").is_file()
    channels = {part.part: part.channel for part in rendered.injection.render}
    assert channels["skill:test-analysis"] == "workspace-agents-skills"


def test_model_and_effort_use_codex_forms(render_context_builder: Builder, tmp_path: Path) -> None:
    from agentteam.domain.common import HarnessId
    from agentteam.domain.run import RequestedV1

    rendered, _ = _render(
        render_context_builder,
        tmp_path,
        requested=RequestedV1(harness=HarnessId.CODEX, model="m-1", effort="high"),
    )
    argv = rendered.argv
    assert argv >= ["-m", "m-1"]
    assert argv >= ["-c", 'model_reasoning_effort="high"']


def test_redaction_covers_json_escaped_windows_paths(
    render_context_builder: Builder, tmp_path: Path
) -> None:
    """A path embedded via json.dumps carries doubled backslashes on Windows;
    the redaction must catch that spelling too (CI run 32723369374)."""
    import json

    from agentteam.domain.run import LauncherPolicy
    from agentteam.harness.rendering import build_command_record

    ctx = render_context_builder("codex", tmp_path)
    scratch = "C:\\Users\\owner\\scratch"
    element = "model_instructions_file=" + json.dumps(scratch + "\\model-instructions.md")
    assert "\\\\" in element  # the JSON spelling the raw needle used to miss
    command, _ = build_command_record(
        ctx=ctx,
        profile=ctx.profile,
        argv=["codex", "exec", "-c", element],
        policy=LauncherPolicy.POSIX_DIRECT,
        substitutions={scratch: "<SCRATCH>"},
        launcher_prefix=1,
    )
    joined = " ".join(command.argv_redacted)
    assert "<SCRATCH>" in joined
    assert "C:" not in joined and "Users" not in joined and "owner" not in joined
