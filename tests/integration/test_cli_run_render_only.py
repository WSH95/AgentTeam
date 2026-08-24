"""`atm run --render-only` (plan section 8): render everything, launch nothing."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml
from typer.testing import CliRunner

from agentteam.cli import app

runner = CliRunner()
REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = REPO_ROOT / "examples" / "assistants" / "code-reviewer"
CI_FAKE = REPO_ROOT / "examples" / "profiles" / "ci-fake.yaml"


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            digest.update(path.as_posix().encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def _base_args(tmp_path: Path, out: Path) -> list[str]:
    workspace = tmp_path / "ws"
    workspace.mkdir(exist_ok=True)
    (workspace / "target.ts").write_text("export const x = 1\n", encoding="utf-8")
    task = tmp_path / "task.md"
    task.write_text("Review target.ts.\n", encoding="utf-8")
    return [
        "run",
        "--assistant",
        str(EXAMPLE),
        "--workspace",
        str(workspace),
        "--task-file",
        str(task),
        "--config",
        str(CI_FAKE),
        "--render-only",
        "--output-dir",
        str(out),
    ]


def test_render_only_renders_all_three_and_touches_nothing_outside(tmp_path: Path) -> None:
    out = tmp_path / "render"
    package_before = _tree_digest(EXAMPLE)
    args = _base_args(tmp_path, out)
    workspace = Path(args[args.index("--workspace") + 1])
    workspace_before = _tree_digest(workspace)
    result = runner.invoke(
        app, [*args, "--harness", "claude-code", "--harness", "codex", "--harness", "grok"]
    )
    assert result.exit_code == 0, result.output
    manifest = json.loads((out / "bundle-manifest.json").read_text(encoding="utf-8"))
    assert manifest["kind"] == "bundle-manifest"
    assert manifest["assistant"]["id"] == "code-reviewer"
    for harness in ("claude-code", "codex", "grok"):
        artifact = out / harness / "invocation.render.json"
        assert artifact.is_file(), harness
        payload = json.loads(artifact.read_text(encoding="utf-8"))
        assert payload["harness"] == harness
        assert "env_values" not in payload  # excluded by construction
        assert payload["command"]["launcher_policy"] == "python-script"
        if harness == "claude-code":
            skill_paths = [
                Path(item["path"])
                for item in payload["files_written"]
                if item["role"].startswith("skill:")
            ]
            assert skill_paths
            assert all(out / "claude-code" / "config-home" in path.parents for path in skill_paths)
    # nothing outside the output dir changed
    assert _tree_digest(EXAMPLE) == package_before
    assert _tree_digest(workspace) == workspace_before


def test_solo_default_harness_when_none_requested(tmp_path: Path) -> None:
    out = tmp_path / "render"
    result = runner.invoke(app, _base_args(tmp_path, out))
    assert result.exit_code == 0, result.output
    rendered = [p.name for p in out.iterdir() if p.is_dir()]
    assert rendered == ["claude-code"]  # ci-fake default_harness


def test_claude_alias_is_accepted(tmp_path: Path) -> None:
    out = tmp_path / "render"
    result = runner.invoke(app, [*_base_args(tmp_path, out), "--harness", "claude"])
    assert result.exit_code == 0, result.output
    assert (out / "claude-code" / "invocation.render.json").is_file()


def test_without_render_only_the_run_launches(tmp_path: Path) -> None:
    # The G3 refusal branch is gone: the same arguments now execute a real
    # solo run against the fakes (full coverage in test_run_execute.py).
    args = _base_args(tmp_path, tmp_path / "run-archive")
    args.remove("--render-only")
    result = runner.invoke(app, args, env={"FAKE_MODE": "ok"})
    assert result.exit_code == 0, result.output
    assert (tmp_path / "run-archive" / "run.json").is_file()


def test_live_run_uses_persistent_profile_home_and_cleans_managed_skills(
    tmp_path: Path,
) -> None:
    out = tmp_path / "run-archive"
    observed_path = tmp_path / "observed.json"
    args = _base_args(tmp_path, out)
    args.remove("--render-only")
    result = runner.invoke(
        app,
        args,
        env={"FAKE_MODE": "ok", "FAKE_OBSERVE": str(observed_path)},
    )
    assert result.exit_code == 0, result.output
    observed = json.loads(observed_path.read_text(encoding="utf-8"))
    persistent = (CI_FAKE.parent / ".agentteam-local/vendors/claude-code").resolve()
    assert observed["env"]["CLAUDE_CONFIG_DIR"] == str(persistent)
    assert not (out / "legs/inv-claude-code/config-home/skills").exists()
    skills = persistent / "skills"
    assert sorted(path.name for path in skills.iterdir()) == [".agentteam-managed"]


def test_missing_output_dir_exits_2(tmp_path: Path) -> None:
    args = _base_args(tmp_path, tmp_path / "render")
    index = args.index("--output-dir")
    del args[index : index + 2]
    result = runner.invoke(app, args)
    assert result.exit_code == 2
    assert "output" in result.output.lower()


def test_unknown_requested_harness_fails_hard(tmp_path: Path) -> None:
    result = runner.invoke(app, [*_base_args(tmp_path, tmp_path / "render"), "--harness", "hermes"])
    assert result.exit_code == 2


def test_request_file_merge_and_reserved_overlays(tmp_path: Path) -> None:
    out = tmp_path / "render"
    args = _base_args(tmp_path, out)
    request = {
        "schema_version": 1,
        "kind": "run-request",
        "assistant": args[args.index("--assistant") + 1],
        "workspace": args[args.index("--workspace") + 1],
        "task_file": args[args.index("--task-file") + 1],
        "mode": "direct",
        "harnesses": ["codex"],
        "output_dir": str(out),
    }
    request_file = tmp_path / "request.yaml"
    request_file.write_text(yaml.safe_dump(request), encoding="utf-8")
    result = runner.invoke(
        app, ["run", str(request_file), "--config", str(CI_FAKE), "--render-only"]
    )
    assert result.exit_code == 0, result.output
    assert (out / "codex" / "invocation.render.json").is_file()

    reserved = {**request, "overlay_refs": ["overlay-1"]}
    request_file.write_text(yaml.safe_dump(reserved), encoding="utf-8")
    result = runner.invoke(
        app, ["run", str(request_file), "--config", str(CI_FAKE), "--render-only"]
    )
    assert result.exit_code == 2
    assert "overlay" in result.output.lower()


def test_model_and_effort_overrides_reach_the_argv(tmp_path: Path) -> None:
    out = tmp_path / "render"
    result = runner.invoke(
        app,
        [
            *_base_args(tmp_path, out),
            "--harness",
            "codex",
            "--model",
            "codex=my-model",
            "--effort",
            "codex=high",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads((out / "codex" / "invocation.render.json").read_text(encoding="utf-8"))
    joined = " ".join(payload["argv"])
    assert "my-model" in joined
    assert 'model_reasoning_effort="high"' in joined


def test_bad_override_format_exits_2(tmp_path: Path) -> None:
    result = runner.invoke(app, [*_base_args(tmp_path, tmp_path / "o"), "--model", "just-a-model"])
    assert result.exit_code == 2
    assert "harness=value" in result.output


def test_json_summary(tmp_path: Path) -> None:
    out = tmp_path / "render"
    result = runner.invoke(app, [*_base_args(tmp_path, out), "--json", "--harness", "grok"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["render_only"] is True
    assert payload["harnesses"] == ["grok"]
    assert payload["decided_by"] == "user"
    assert payload["effective_definition_hash"] == payload["package_hash"]
