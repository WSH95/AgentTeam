"""Runtime CLI never installs implicitly and doctor makes zero calls."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentteam.cli import app

runner = CliRunner()


def test_runtime_doctor_reports_uninstalled_without_installing(tmp_path: Path) -> None:
    env = {"AGENTTEAM_HOME": str(tmp_path)}
    result = runner.invoke(app, ["runtime", "doctor", "direct-acp", "--json"], env=env)
    assert result.exit_code == 1, result.output
    payload = json.loads(result.output)
    assert payload["status"] == "unsupported"
    assert payload["model_calls"] == 0


def test_runtime_rejects_unknown_id() -> None:
    result = runner.invoke(app, ["runtime", "doctor", "other"])
    assert result.exit_code == 2
    assert "unknown runtime" in result.output
