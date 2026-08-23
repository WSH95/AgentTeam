"""Shared CLI machinery: stable exit codes, error handling, output emission."""

from __future__ import annotations

import json
from typing import Any

import typer

# Stable exit codes (plan section 8).
EXIT_OK = 0
EXIT_RUNTIME = 1
EXIT_INVALID = 2
EXIT_SEMANTIC = 3
EXIT_CANCELLED = 130


class CommandError(Exception):
    """A user-reportable failure with a stable exit code."""

    def __init__(self, message: str, *, exit_code: int = EXIT_INVALID) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def fail(message: str, *, exit_code: int = EXIT_INVALID) -> typer.Exit:
    """Print a stable, greppable error line and return the Exit to raise."""
    typer.echo(f"error: {message}")
    return typer.Exit(code=exit_code)


def emit(json_mode: bool, payload: dict[str, Any], human: str) -> None:
    if json_mode:
        typer.echo(json.dumps(payload, indent=2))
    else:
        typer.echo(human)
