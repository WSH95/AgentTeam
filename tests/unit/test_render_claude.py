"""Claude adapter rendering (plan sections 9 and 11; fact sheet 2026-08-23)."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from agentteam.domain.run import LauncherPolicy
from agentteam.harness.claude import ClaudeAdapter
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


def _render(builder: Builder, tmp_path: Path, **overrides: object) -> Any:
    ctx = builder("claude-code", tmp_path, **overrides)
    return ClaudeAdapter().render(ctx), ctx


def test_golden_argv_and_channels(render_context_builder: Builder, tmp_path: Path) -> None:
    rendered, ctx = _render(render_context_builder, tmp_path)
    argv = rendered.argv
    exe = argv[0]
    assert exe.endswith("claude")
    flags = argv[1:]
    assert flags[:4] == ["-p", "--output-format", "json", "--no-session-persistence"]
    assert flags[4:6] == ["--setting-sources", "user"]
    mcp_index = flags.index("--mcp-config")
    assert json.loads(flags[mcp_index + 1]) == {"mcpServers": {}}
    assert "--strict-mcp-config" in flags
    assert flags >= ["--permission-mode", "dontAsk"]
    allowed_index = flags.index("--allowedTools")
    assert set(flags[allowed_index + 1].split(",")) == {"Read", "Grep", "Glob", "LS", "Skill"}
    disallowed_index = flags.index("--disallowedTools")
    assert set(flags[disallowed_index + 1].split(",")) == {
        "Write",
        "Edit",
        "NotebookEdit",
        "Bash",
        "WebFetch",
        "WebSearch",
    }
    assert "--safe-mode" not in flags
    assert "--bare" not in flags
    schema_index = flags.index("--json-schema")
    schema = json.loads(flags[schema_index + 1])
    assert schema["$id"] == "urn:agentteam:schema:normalized-review:v1"
    assert "\n" not in flags[schema_index + 1]  # minified single line
    prompt_index = flags.index("--append-system-prompt-file")
    prompt_file = Path(flags[prompt_index + 1])
    assert "meticulous senior code reviewer" in prompt_file.read_text(encoding="utf-8")
    assert rendered.stdin_text is not None and "Review the change" in rendered.stdin_text
    assert rendered.environment.config_home_variable == "CLAUDE_CONFIG_DIR"
    assert rendered.env_values["CLAUDE_CONFIG_DIR"] == str(ctx.config_root)
    assert rendered.schema_channel == "argv-inline"


def test_skills_are_written_into_the_config_home_channel(
    render_context_builder: Builder, tmp_path: Path
) -> None:
    rendered, ctx = _render(render_context_builder, tmp_path)
    for name in ("code-review", "security-review", "test-analysis"):
        skill = ctx.config_root / "skills" / name / "SKILL.md"
        assert skill.is_file(), name
    marker = ctx.config_root / "skills" / ".agentteam-managed"
    assert marker.is_file()
    channels = {part.part: part.channel for part in rendered.injection.render}
    assert channels["skill:code-review"] == "config-home-skills"
    assert channels["persona"] == "append-system-prompt-file"
    assert channels["task"] == "stdin"
    assert channels["output-schema"] == "argv-inline"
    assert rendered.injection.undeliverable_required_parts == []


def test_skill_channel_ladder_uses_plugin_then_workspace_fallbacks(
    render_context_builder: Builder, tmp_path: Path
) -> None:
    ctx = render_context_builder("claude-code", tmp_path)
    plugin_profile = _only_channels(
        ctx.profile, {"append-system-prompt", "skills-plugin-dir", "skills-workspace"}
    )
    plugin = ClaudeAdapter().render(ctx.model_copy(update={"profile": plugin_profile}))
    assert "--plugin-dir" in plugin.argv
    assert any(write.channel == "plugin-dir-skills" for write in plugin.files_written)

    workspace_profile = _only_channels(ctx.profile, {"append-system-prompt", "skills-workspace"})
    workspace = ClaudeAdapter().render(
        ctx.model_copy(
            update={
                "profile": workspace_profile,
                "workspace_root": tmp_path / "workspace-fallback",
                "scratch_dir": tmp_path / "scratch-fallback",
            }
        )
    )
    assert "--plugin-dir" not in workspace.argv
    assert any(write.channel == "workspace-claude-skills" for write in workspace.files_written)


def test_instruction_ladder_skips_a_stale_verified_primary(
    render_context_builder: Builder, tmp_path: Path
) -> None:
    ctx = render_context_builder("claude-code", tmp_path)
    profile = ctx.profile.model_copy(
        update={
            "capabilities": [
                row.model_copy(update={"cli_version": "stale-version"})
                if row.name == "append-system-prompt-file"
                else row
                for row in ctx.profile.capabilities
            ]
        }
    )
    rendered = ClaudeAdapter().render(ctx.model_copy(update={"profile": profile}))
    assert "--append-system-prompt-file" not in rendered.argv
    assert "--append-system-prompt" in rendered.argv


@pytest.mark.parametrize(
    ("channels", "match"),
    [
        ({"skills-config-home"}, "instruction channel"),
        ({"append-system-prompt-file"}, "Skill channel"),
    ],
)
def test_missing_current_channel_fails_at_the_adapter(
    render_context_builder: Builder,
    tmp_path: Path,
    channels: set[str],
    match: str,
) -> None:
    ctx = render_context_builder("claude-code", tmp_path)
    profile = _only_channels(ctx.profile, channels)
    with pytest.raises(RenderError, match=match) as error:
        ClaudeAdapter().render(ctx.model_copy(update={"profile": profile}))
    assert "atm profile doctor --probe" in str(error.value)


def test_model_and_effort_flags_appear_when_resolved(
    render_context_builder: Builder, tmp_path: Path
) -> None:
    from agentteam.domain.common import HarnessId
    from agentteam.domain.run import RequestedV1

    rendered, _ = _render(
        render_context_builder,
        tmp_path,
        requested=RequestedV1(harness=HarnessId.CLAUDE_CODE, model="claude-fable-5", effort="high"),
    )
    flags = rendered.argv
    assert flags >= ["--model", "claude-fable-5"]
    assert flags >= ["--effort", "high"]


def test_missing_required_skill_fails_before_launch(
    render_context_builder: Builder, tmp_path: Path
) -> None:
    # break the package copy: point the package at a copy without one SKILL.md
    import shutil

    ctx = render_context_builder("claude-code", tmp_path)
    broken = tmp_path / "broken-package"
    shutil.copytree(ctx.package_root, broken)
    (broken / "skills" / "security-review" / "SKILL.md").unlink()
    from agentteam.resolution.package import load_package

    loaded = load_package(broken)
    ctx2 = render_context_builder(
        "claude-code", tmp_path, package_root=broken, definition=loaded.definition
    )
    with pytest.raises(RenderError) as excinfo:
        ClaudeAdapter().render(ctx2)
    assert any("security-review" in p.part for p in excinfo.value.undeliverable_required_parts)


def test_argv_length_guard(render_context_builder: Builder, tmp_path: Path) -> None:
    import shutil

    ctx = render_context_builder("claude-code", tmp_path)
    huge = tmp_path / "huge-package"
    shutil.copytree(ctx.package_root, huge)
    (huge / "persona.md").write_text("x" * 40000, encoding="utf-8")
    from agentteam.resolution.package import load_package

    loaded = load_package(huge)
    from agentteam.domain.profile import Verification

    profile = ctx.profile.model_copy(
        update={
            "capabilities": [
                row.model_copy(
                    update={
                        "verification": (
                            Verification.UNVERIFIED
                            if row.name == "append-system-prompt-file"
                            else row.verification
                        )
                    }
                )
                for row in ctx.profile.capabilities
            ]
        }
    )
    ctx2 = render_context_builder(
        "claude-code",
        tmp_path,
        package_root=huge,
        definition=loaded.definition,
        profile=profile,
    )
    with pytest.raises(RenderError, match="argv length"):
        ClaudeAdapter().render(ctx2)


def test_command_record_is_redacted_and_launcher_resolved(
    render_context_builder: Builder, tmp_path: Path
) -> None:
    rendered, ctx = _render(render_context_builder, tmp_path)
    assert rendered.command.launcher_policy is LauncherPolicy.POSIX_DIRECT
    joined = " ".join(rendered.command.argv_redacted)
    assert str(ctx.workspace) not in joined
    assert str(ctx.scratch_dir) not in joined
    assert "<INSTRUCTIONS_FILE>" in joined and "<SCHEMA_JSON>" in joined
    assert rendered.command.cwd == "<WORKSPACE>"
    dumped = rendered.model_dump_json()
    assert "/home/u" not in dumped  # env values never serialise
