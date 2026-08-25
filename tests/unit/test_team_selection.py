"""Team preference precedence and exact team-member renderer grants."""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from agentteam.domain.assistant import HarnessPolicyV1
from agentteam.domain.common import HarnessId
from agentteam.domain.profile import (
    EnvironmentNamesV1,
    HarnessProfileSetV1,
    HarnessProfileV1,
)
from agentteam.domain.run import DecidedBy
from agentteam.domain.team import WorkspaceAccess
from agentteam.harness.claude import ClaudeAdapter
from agentteam.harness.codex import CodexAdapter
from agentteam.harness.grok import GrokAdapter
from agentteam.harness.rendering import RenderError
from agentteam.harness.types import InvocationScope, OutputContract
from agentteam.resolution.selection import SelectionError, select_harnesses
from agentteam.schema import vendor_schema, vendor_schema_text

Builder = Callable[..., Any]
CLAUDE = HarnessId.CLAUDE_CODE
CODEX = HarnessId.CODEX
GROK = HarnessId.GROK


def _profile(harness: HarnessId) -> HarnessProfileV1:
    return HarnessProfileV1(
        harness=harness,
        executable=harness.value,
        config_home=f"vendors/{harness.value}",
        environment=EnvironmentNamesV1(config_home_variable=f"{harness.value}_HOME"),
    )


def _profiles() -> HarnessProfileSetV1:
    return HarnessProfileSetV1(
        schema_version=1,
        kind="harness-profile-set",
        profiles=[_profile(CLAUDE), _profile(CODEX), _profile(GROK)],
        default_harness=GROK,
    )


def test_precedence_is_user_then_assistant_then_team_then_default() -> None:
    profiles = _profiles()

    def installed(_profile: HarnessProfileV1) -> bool:
        return True

    user = select_harnesses(
        requested=[CODEX],
        policy=HarnessPolicyV1(preferred=[CLAUDE]),
        profiles=profiles,
        installed=installed,
        team_preferred=[GROK],
    )
    assert user.chosen == [CODEX]
    assert user.selection.decided_by is DecidedBy.USER

    assistant = select_harnesses(
        requested=[],
        policy=HarnessPolicyV1(preferred=[CLAUDE]),
        profiles=profiles,
        installed=installed,
        team_preferred=[CODEX],
    )
    assert assistant.chosen == [CLAUDE]
    assert assistant.selection.decided_by is DecidedBy.ASSISTANT

    team = select_harnesses(
        requested=[],
        policy=HarnessPolicyV1(),
        profiles=profiles,
        installed=installed,
        team_preferred=[CODEX],
    )
    assert team.chosen == [CODEX]
    assert team.selection.decided_by is DecidedBy.TEAM

    default = select_harnesses(
        requested=[],
        policy=HarnessPolicyV1(),
        profiles=profiles,
        installed=installed,
    )
    assert default.chosen == [GROK]
    assert default.selection.decided_by is DecidedBy.DEFAULT


def test_team_preference_remains_fail_closed_under_hard_policy() -> None:
    profiles = _profiles().model_copy(update={"default_harness": None})
    with pytest.raises(SelectionError, match="no eligible"):
        select_harnesses(
            requested=[],
            policy=HarnessPolicyV1(allowed=[CLAUDE]),
            profiles=profiles.model_copy(update={"profiles": [_profile(CODEX)]}),
            installed=lambda _profile: True,
            team_preferred=[CODEX],
        )


@pytest.mark.parametrize(
    ("access", "allowed", "denied"),
    [
        (
            WorkspaceAccess.READ_ONLY,
            "Read,Grep,Glob,LS,Skill",
            "Write,Edit,NotebookEdit,Bash,WebFetch,WebSearch",
        ),
        (
            WorkspaceAccess.WORKSPACE_WRITE,
            "Read,Grep,Glob,LS,Skill,Write,Edit",
            "NotebookEdit,Bash,WebFetch,WebSearch",
        ),
    ],
)
def test_claude_team_grants_are_exact_and_disjoint(
    render_context_builder: Builder,
    tmp_path: Path,
    access: WorkspaceAccess,
    allowed: str,
    denied: str,
) -> None:
    ctx = render_context_builder(
        "claude-code",
        tmp_path,
        invocation_scope=InvocationScope.TEAM_MEMBER,
        workspace_access=access,
        output_contract=OutputContract.MEMBER_RESULT,
    )
    rendered = ClaudeAdapter().render(ctx)
    argv = rendered.argv
    assert argv[argv.index("--allowedTools") + 1] == allowed
    assert argv[argv.index("--disallowedTools") + 1] == denied
    assert set(allowed.split(",")).isdisjoint(denied.split(","))
    delivered = json.loads(argv[argv.index("--json-schema") + 1])
    assert delivered == vendor_schema("member-result-v1.schema.json")


@pytest.mark.parametrize(
    ("access", "sandbox"),
    [
        (WorkspaceAccess.READ_ONLY, "read-only"),
        (WorkspaceAccess.WORKSPACE_WRITE, "workspace-write"),
    ],
)
def test_codex_team_sandbox_and_output_contract(
    render_context_builder: Builder,
    tmp_path: Path,
    access: WorkspaceAccess,
    sandbox: str,
) -> None:
    ctx = render_context_builder(
        "codex",
        tmp_path,
        invocation_scope=InvocationScope.TEAM_MEMBER,
        workspace_access=access,
        output_contract=OutputContract.MEMBER_RESULT,
    )
    rendered = CodexAdapter().render(ctx)
    assert rendered.argv[rendered.argv.index("-s") + 1] == sandbox
    network = "sandbox_workspace_write.network_access=false"
    assert (network in rendered.argv) is (access is WorkspaceAccess.WORKSPACE_WRITE)
    schema = Path(rendered.argv[rendered.argv.index("--output-schema") + 1])
    assert schema.read_text(encoding="utf-8") == vendor_schema_text("member-result-v1.schema.json")


@pytest.mark.parametrize(
    ("access", "suffix", "extends"),
    [
        (WorkspaceAccess.READ_ONLY, "ro", "read-only"),
        (WorkspaceAccess.WORKSPACE_WRITE, "rw", "workspace"),
    ],
)
def test_grok_team_profile_is_project_local_guarded_and_network_denied(
    render_context_builder: Builder,
    tmp_path: Path,
    access: WorkspaceAccess,
    suffix: str,
    extends: str,
) -> None:
    ctx = render_context_builder("grok", tmp_path)
    persistent = tmp_path / "persistent-grok"
    persistent.mkdir()
    profile = ctx.profile.model_copy(update={"config_home": str(persistent)})
    team = ctx.model_copy(
        update={
            "profile": profile,
            "invocation_scope": InvocationScope.TEAM_MEMBER,
            "workspace_access": access,
            "output_contract": OutputContract.MEMBER_RESULT,
        }
    )
    rendered = GrokAdapter(token_hex=lambda _size: "a" * 32).render(team)
    name = f"agentteam_{'a' * 32}_{suffix}"
    assert rendered.argv[rendered.argv.index("--sandbox") + 1] == name
    project_file = team.workspace_root / ".grok" / "sandbox.toml"
    assert project_file.read_text(encoding="utf-8") == (
        f'[profiles.{name}]\nextends = "{extends}"\nrestrict_network = true\n'
    )
    assert not (persistent / "sandbox.toml").exists()
    assert any(write.path == project_file for write in rendered.files_written)


def test_grok_team_profile_refuses_windows_collisions_and_malformed_global_state(
    render_context_builder: Builder, tmp_path: Path
) -> None:
    ctx = render_context_builder(
        "grok",
        tmp_path,
        invocation_scope=InvocationScope.TEAM_MEMBER,
        output_contract=OutputContract.MEMBER_RESULT,
    )
    with pytest.raises(RenderError, match="Windows"):
        GrokAdapter(token_hex=lambda _size: "b" * 32).render(
            ctx.model_copy(update={"platform": "win32"})
        )

    persistent = tmp_path / "persistent"
    persistent.mkdir()
    (persistent / "sandbox.toml").write_text("not = [valid", encoding="utf-8")
    malformed = ctx.model_copy(
        update={"profile": ctx.profile.model_copy(update={"config_home": str(persistent)})}
    )
    with pytest.raises(RenderError, match="malformed"):
        GrokAdapter(token_hex=lambda _size: "c" * 32).render(malformed)


@pytest.mark.skipif(sys.platform == "win32", reason="symlink privilege varies")
def test_grok_team_profile_refuses_project_parent_and_leaf_collisions(
    render_context_builder: Builder, tmp_path: Path
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    symlink_root = tmp_path / "symlink-case"
    symlink_root.mkdir()
    symlink_ctx = render_context_builder(
        "grok",
        symlink_root,
        invocation_scope=InvocationScope.TEAM_MEMBER,
        output_contract=OutputContract.MEMBER_RESULT,
    )
    symlink_ctx.workspace_root.mkdir(parents=True)
    (symlink_ctx.workspace_root / ".grok").symlink_to(outside, target_is_directory=True)
    with pytest.raises(RenderError, match="real directory"):
        GrokAdapter(token_hex=lambda _size: "d" * 32).render(symlink_ctx)
    assert not list(outside.iterdir())

    leaf_root = tmp_path / "leaf-case"
    leaf_root.mkdir()
    leaf_ctx = render_context_builder(
        "grok",
        leaf_root,
        invocation_scope=InvocationScope.TEAM_MEMBER,
        output_contract=OutputContract.MEMBER_RESULT,
    )
    project = leaf_ctx.workspace_root / ".grok"
    project.mkdir(parents=True)
    (project / "sandbox.toml").write_text("owner content\n", encoding="utf-8")
    with pytest.raises(RenderError, match="already exists"):
        GrokAdapter(token_hex=lambda _size: "e" * 32).render(leaf_ctx)
    assert (project / "sandbox.toml").read_text(encoding="utf-8") == "owner content\n"


def test_grok_team_profile_refuses_global_name_collision_and_invalid_nonce(
    render_context_builder: Builder, tmp_path: Path
) -> None:
    collision_root = tmp_path / "collision-case"
    collision_root.mkdir()
    ctx = render_context_builder(
        "grok",
        collision_root,
        invocation_scope=InvocationScope.TEAM_MEMBER,
        output_contract=OutputContract.MEMBER_RESULT,
    )
    persistent = tmp_path / "global-home"
    persistent.mkdir()
    name = f"agentteam_{'f' * 32}_ro"
    (persistent / "sandbox.toml").write_text(
        f'[profiles.{name}]\nextends = "read-only"\n',
        encoding="utf-8",
    )
    colliding = ctx.model_copy(
        update={"profile": ctx.profile.model_copy(update={"config_home": str(persistent)})}
    )
    with pytest.raises(RenderError, match="already exists"):
        GrokAdapter(token_hex=lambda _size: "f" * 32).render(colliding)

    invalid_root = tmp_path / "invalid-token"
    invalid_root.mkdir()
    invalid = render_context_builder(
        "grok",
        invalid_root,
        invocation_scope=InvocationScope.TEAM_MEMBER,
        output_contract=OutputContract.MEMBER_RESULT,
    )
    with pytest.raises(RenderError, match="nonce"):
        GrokAdapter(token_hex=lambda _size: "NOT-HEX").render(invalid)


def test_standalone_render_defaults_are_byte_compatible(
    render_context_builder: Builder, tmp_path: Path
) -> None:
    for harness, adapter in (
        ("claude-code", ClaudeAdapter()),
        ("codex", CodexAdapter()),
        ("grok", GrokAdapter()),
    ):
        first_root = tmp_path / f"{harness}-first"
        second_root = tmp_path / f"{harness}-second"
        first_root.mkdir()
        second_root.mkdir()
        first = render_context_builder(harness, first_root)
        second = render_context_builder(
            harness,
            second_root,
            invocation_scope=InvocationScope.STANDALONE,
            workspace_access=WorkspaceAccess.READ_ONLY,
            output_contract=OutputContract.NORMALIZED_REVIEW,
        )
        # Normalize caller-specific roots through the already-redacted public record.
        one = adapter.render(first).model_dump(mode="json", exclude={"files_written"})
        two = adapter.render(second).model_dump(mode="json", exclude={"files_written"})
        assert one["command"] == two["command"]
        assert one["injection"] == two["injection"]
