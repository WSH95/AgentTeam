"""Assistant package validation and immutable-library commands."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from agentteam.commands.common import EXIT_INVALID, emit, fail
from agentteam.commands.interactive import assistant_chat_service
from agentteam.domain.interactive import CatalogKind
from agentteam.library import LibraryError, LibraryStore, default_library_root
from agentteam.resolution.archive import ArchiveContractError, hash_package
from agentteam.resolution.package import PackageError, check_package, load_package

assistant_app = typer.Typer(name="assistant", help="Portable Assistant packages.")


@assistant_app.command("chat")
def chat(
    item_id: Annotated[str | None, typer.Argument(help="Catalog Assistant id.")] = None,
    version: Annotated[int | None, typer.Option("--version", min=1)] = None,
    path: Annotated[
        Path | None,
        typer.Option("--path", help="Explicit unmanaged Assistant package path."),
    ] = None,
    workspace: Annotated[Path, typer.Option("--workspace", help="Supplied project path.")] = Path(
        "."
    ),
    goal: Annotated[str, typer.Option("--goal", help="Bounded top-level goal.")] = "",
    done_when: Annotated[list[str] | None, typer.Option("--done-when")] = None,
    stream_json: Annotated[bool, typer.Option("--stream-json")] = False,
) -> None:
    """Start a fresh one-Member interactive run from an exact Assistant revision."""
    if not goal.strip():
        raise fail("--goal must be non-empty")
    assistant_chat_service(
        item_id=item_id,
        version=version,
        path=path,
        workspace=workspace,
        goal=goal,
        done_when=done_when or [],
        stream_json=stream_json,
    )


@assistant_app.command("import")
def import_package(
    package: Annotated[Path, typer.Argument(help="Assistant package directory.")],
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Atomically import one exact immutable Assistant revision."""
    try:
        entry = LibraryStore(default_library_root()).import_assistant(package)
    except LibraryError as error:
        raise fail(str(error)) from None
    payload = entry.model_dump(mode="json")
    emit(
        json_out,
        payload,
        f"imported assistant {entry.id}@{entry.version} ({entry.content_hash[:12]}...)",
    )


@assistant_app.command("list")
def list_packages(
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """List immutable Assistant revisions in the managed library."""
    try:
        entries = LibraryStore(default_library_root()).entries(kind=CatalogKind.ASSISTANT)
    except LibraryError as error:
        raise fail(str(error)) from None
    rows = [entry.model_dump(mode="json") for entry in entries]
    emit(
        json_out,
        {"entries": rows},
        "\n".join(
            f"{entry.id}@{entry.version} {entry.content_hash}{' active' if entry.active else ''}"
            for entry in entries
        )
        or "no Assistant revisions",
    )


@assistant_app.command("show")
def show_package(
    item_id: Annotated[str, typer.Argument(help="Assistant id.")],
    version: Annotated[int, typer.Option("--version", min=1)],
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Show one exact Assistant catalog entry."""
    try:
        entry = LibraryStore(default_library_root()).get(CatalogKind.ASSISTANT, item_id, version)
    except LibraryError as error:
        raise fail(str(error)) from None
    emit(
        json_out,
        entry.model_dump(mode="json"),
        f"assistant {entry.id}@{entry.version}\n"
        f"hash: {entry.content_hash}\nobject: {entry.object_path}",
    )


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
