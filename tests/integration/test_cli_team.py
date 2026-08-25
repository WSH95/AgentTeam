"""`atm team validate` integration contract (M1b G1)."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentteam.cli import app

runner = CliRunner()
REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = REPO_ROOT / "examples" / "teams" / "development.yaml"


def test_validate_committed_template_ok() -> None:
    result = runner.invoke(app, ["team", "validate", str(EXAMPLE)])
    assert result.exit_code == 0, result.output
    assert "valid: development v1" in result.output


def test_validate_json_includes_hash_and_counts() -> None:
    result = runner.invoke(app, ["team", "validate", str(EXAMPLE), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload == {
        "valid": True,
        "template_hash": payload["template_hash"],
        "problems": [],
        "member_count": 3,
        "task_count": 3,
    }
    assert len(payload["template_hash"]) == 64


def test_missing_template_exits_2() -> None:
    result = runner.invoke(app, ["team", "validate", "/nowhere/team.yaml"])
    assert result.exit_code == 2
    assert "regular file" in result.output


def test_reference_problem_exits_2_and_names_member(tmp_path: Path) -> None:
    broken = tmp_path / "team.yaml"
    broken.write_text(
        EXAMPLE.read_text(encoding="utf-8").replace(
            "../assistants/implementer", "missing-assistant"
        ),
        encoding="utf-8",
    )
    result = runner.invoke(app, ["team", "validate", str(broken)])
    assert result.exit_code == 2
    assert "members.implementer.assistant" in result.output
