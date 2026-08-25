"""`atm team validate <template> [--json]` (M1b section 7)."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from agentteam.commands.common import EXIT_INVALID, emit, fail
from agentteam.resolution.team import (
    TeamTemplateError,
    check_team_template,
    hash_team_template,
    load_team_template,
)

team_app = typer.Typer(name="team", help="Portable Team templates.")


@team_app.command("validate")
def validate(
    template: Annotated[Path, typer.Argument(help="Path to a TeamTemplate YAML/JSON file.")],
    json_out: Annotated[bool, typer.Option("--json", help="Machine-readable output.")] = False,
) -> None:
    """Validate schema, composition, references, and prohibited content."""
    try:
        loaded = load_team_template(template)
    except TeamTemplateError as error:
        raise fail(str(error)) from None
    template_hash = hash_team_template(loaded)
    problems = check_team_template(loaded)
    payload = {
        "valid": not problems,
        "template_hash": template_hash,
        "problems": problems,
        "member_count": len(loaded.definition.members),
        "task_count": len(loaded.definition.workflow_skeleton),
    }
    if problems:
        emit(json_out, payload, "invalid: " + "; ".join(problems))
        raise typer.Exit(code=EXIT_INVALID)
    emit(
        json_out,
        payload,
        f"valid: {loaded.definition.id} v{loaded.definition.version} "
        f"(template hash {template_hash[:12]}...)",
    )
