"""CLI contract tests (M1a plan section 8): `atm --help` and `atm --version`."""

from __future__ import annotations

import importlib.metadata
import os
import shutil
import subprocess

from typer.testing import CliRunner

from agentteam import __version__
from agentteam.cli import app

runner = CliRunner()


def _scrubbed_env() -> dict[str, str]:
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)  # this host exports a Python 3.8 ROS path
    return env


def test_version_flag_prints_name_and_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0, result.output
    assert result.output.strip() == f"atm {__version__}"


def test_version_is_the_planned_alpha_version_and_matches_metadata() -> None:
    assert __version__ == "0.1.0a0"  # plan section 5 pins the M1a version
    assert importlib.metadata.version("agentteam") == __version__


def test_help_exits_zero_and_names_the_product() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0, result.output
    assert "AgentTeam" in result.output
    assert "atm" in result.output


def test_no_arguments_shows_help_and_exits_zero() -> None:
    result = runner.invoke(app, [])
    assert result.exit_code == 0, result.output
    assert "Usage" in result.output


def test_unknown_option_exits_nonzero() -> None:
    result = runner.invoke(app, ["--nosuchflag"])
    assert result.exit_code != 0


def test_console_script_atm_reports_version() -> None:
    # The real `atm` entry point installed by uv into the environment's bin.
    atm = shutil.which("atm")
    assert atm is not None, "console script `atm` not on PATH (run tests via `uv run pytest`)"
    proc = subprocess.run(
        [atm, "--version"], capture_output=True, text=True, check=False, env=_scrubbed_env()
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == f"atm {__version__}"
