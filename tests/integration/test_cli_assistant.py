"""`atm assistant validate` (plan section 8)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from agentteam.cli import app

runner = CliRunner()
REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = REPO_ROOT / "examples" / "assistants" / "code-reviewer"


def test_validate_example_package_ok() -> None:
    result = runner.invoke(app, ["assistant", "validate", str(EXAMPLE)])
    assert result.exit_code == 0, result.output
    assert "valid" in result.output


def test_validate_json_includes_the_package_hash() -> None:
    result = runner.invoke(app, ["assistant", "validate", str(EXAMPLE), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["valid"] is True
    assert len(payload["package_hash"]) == 64
    assert payload["problems"] == []


def test_missing_package_exits_2() -> None:
    result = runner.invoke(app, ["assistant", "validate", "/nowhere/at/all"])
    assert result.exit_code == 2
    assert "assistant.yaml" in result.output


def test_reference_problem_exits_2_and_lists_it(tmp_path: Path) -> None:
    broken = tmp_path / "pkg"
    shutil.copytree(EXAMPLE, broken)
    skill = broken / "skills" / "code-review" / "SKILL.md"
    skill.rename(skill.with_name("NOT-SKILL.md"))  # dir stays non-empty
    result = runner.invoke(app, ["assistant", "validate", str(broken)])
    assert result.exit_code == 2
    assert "SKILL.md" in result.output


def test_strict_content_flags_violations(tmp_path: Path) -> None:
    broken = tmp_path / "pkg"
    shutil.copytree(EXAMPLE, broken)
    with open(broken / "principles.md", "a", encoding="utf-8") as fh:
        fh.write("\nUse the key sk-abcdefghijklmnopqrstuvwx to authenticate.\n")
    ok_without = runner.invoke(app, ["assistant", "validate", str(broken)])
    assert ok_without.exit_code == 0
    strict = runner.invoke(app, ["assistant", "validate", str(broken), "--strict-content"])
    assert strict.exit_code == 2
    assert "secrets" in strict.output
