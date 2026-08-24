"""Codex adapter rendering (plan sections 9 and 11; fact sheet 2026-08-23)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from agentteam.harness.codex import CodexAdapter

Builder = Callable[..., Any]


def _only_instruction_channel(profile: Any, name: str) -> Any:
    from agentteam.domain.profile import Verification

    return profile.model_copy(
        update={
            "capabilities": [
                row.model_copy(
                    update={
                        "verification": (
                            Verification.VERIFIED
                            if row.name in {name, "skills-workspace"}
                            else Verification.UNVERIFIED
                        )
                    }
                )
                for row in profile.capabilities
            ]
        }
    )


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
