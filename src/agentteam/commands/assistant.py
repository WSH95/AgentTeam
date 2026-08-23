"""`atm assistant validate <package> [--strict-content] [--json]` (plan section 8)."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from agentteam.commands.common import EXIT_INVALID, emit, fail
from agentteam.resolution.archive import ArchiveContractError, hash_package
from agentteam.resolution.package import PackageError, check_package, load_package

assistant_app = typer.Typer(name="assistant", help="Portable Assistant packages.")


@assistant_app.command("validate")
def validate(
    package: Annotated[Path, typer.Argument(help="Path to the Assistant package directory.")],
    strict_content: Annotated[
        bool, typer.Option("--strict-content", help="Also run prohibited-content heuristics.")
    ] = False,
    json_out: Annotated[bool, typer.Option("--json", help="Machine-readable output.")] = False,
) -> None:
    """Validate a package: closed schema, archive contract, references, content."""
    try:
        loaded = load_package(package)
        digest = hash_package(package)
    except (PackageError, ArchiveContractError) as error:
        raise fail(str(error)) from None
    problems = check_package(loaded, strict_content=strict_content)
    payload = {
        "valid": not problems,
        "package_hash": digest.package_hash,
        "problems": problems,
    }
    if problems:
        emit(
            json_out,
            payload,
            "invalid: " + "; ".join(problems),
        )
        raise typer.Exit(code=EXIT_INVALID)
    emit(
        json_out,
        payload,
        f"valid: {loaded.definition.id} v{loaded.definition.version} "
        f"(package hash {digest.package_hash[:12]}...)",
    )
