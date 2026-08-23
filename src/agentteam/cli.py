"""`atm` - the AgentTeam command-line interface.

M1a plan section 8 defines the public contract. At gate G2 only the
product-level options exist; `assistant`, `profile`, and `run` commands arrive
with the gates that implement them (G3-G4) so `--help` never lists a command
that does nothing.
"""

from __future__ import annotations

import typer

from agentteam import __version__

HELP = (
    "AgentTeam - portable, harness-independent Assistant definitions executed as "
    "fresh runs over existing coding-agent harnesses. Alpha: the command set grows "
    "gate by gate with the approved M1a plan."
)

app = typer.Typer(
    name="atm",
    help=HELP,
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"atm {__version__}")
        raise typer.Exit(code=0)


@app.callback(invoke_without_command=True)
def root(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        help="Print the AgentTeam version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """AgentTeam command-line interface."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit(code=0)


def main() -> None:
    """Console-script entry point (`atm = "agentteam.cli:main"`)."""
    app()


if __name__ == "__main__":
    main()
