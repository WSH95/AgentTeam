"""Team template validation, migration, and immutable-library commands."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Annotated

import typer
import yaml

from agentteam.commands.common import EXIT_INVALID, emit, fail
from agentteam.commands.interactive import team_chat_service
from agentteam.domain.interactive import CatalogKind, WorkspaceLayout
from agentteam.library import LibraryError, LibraryStore, default_library_root
from agentteam.resolution.interactive import (
    load_team_template_v2,
    migrate_team_template_v1,
    write_team_migration,
)
from agentteam.resolution.package import check_prohibited_text
from agentteam.resolution.team import (
    TeamTemplateError,
    check_team_template,
    hash_team_template,
    load_team_template,
)

team_app = typer.Typer(name="team", help="Portable Team templates.")


@team_app.command("chat")
def chat(
    item_id: Annotated[str | None, typer.Argument(help="Catalog Team id.")] = None,
    version: Annotated[int | None, typer.Option("--version", min=1)] = None,
    path: Annotated[
        Path | None,
        typer.Option("--path", help="Explicit unmanaged TeamTemplateV2 path."),
    ] = None,
    workspace: Annotated[Path, typer.Option("--workspace", help="Supplied project path.")] = Path(
        "."
    ),
    goal: Annotated[str, typer.Option("--goal", help="Bounded top-level goal.")] = "",
    done_when: Annotated[list[str] | None, typer.Option("--done-when")] = None,
    stream_json: Annotated[bool, typer.Option("--stream-json")] = False,
) -> None:
    """Start a fresh interactive TeamRun from an exact Team revision."""
    if not goal.strip():
        raise fail("--goal must be non-empty")
    team_chat_service(
        item_id=item_id,
        version=version,
        path=path,
        workspace=workspace,
        goal=goal,
        done_when=done_when or [],
        stream_json=stream_json,
    )


@team_app.command("import")
def import_template(
    template: Annotated[Path, typer.Argument(help="TeamTemplateV2 YAML/JSON file.")],
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Atomically import a V2 Team after resolving every exact Assistant ref."""
    try:
        entry = LibraryStore(default_library_root()).import_team(template)
    except LibraryError as error:
        raise fail(str(error)) from None
    emit(
        json_out,
        entry.model_dump(mode="json"),
        f"imported team {entry.id}@{entry.version} ({entry.content_hash[:12]}...)",
    )


@team_app.command("list")
def list_templates(
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """List immutable TeamTemplate revisions in the managed library."""
    try:
        entries = LibraryStore(default_library_root()).entries(kind=CatalogKind.TEAM)
    except LibraryError as error:
        raise fail(str(error)) from None
    emit(
        json_out,
        {"entries": [entry.model_dump(mode="json") for entry in entries]},
        "\n".join(
            f"{entry.id}@{entry.version} {entry.content_hash}{' active' if entry.active else ''}"
            for entry in entries
        )
        or "no Team revisions",
    )


@team_app.command("show")
def show_template(
    item_id: Annotated[str, typer.Argument(help="Team id.")],
    version: Annotated[int, typer.Option("--version", min=1)],
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Show one exact Team catalog entry."""
    try:
        entry = LibraryStore(default_library_root()).get(CatalogKind.TEAM, item_id, version)
    except LibraryError as error:
        raise fail(str(error)) from None
    emit(
        json_out,
        entry.model_dump(mode="json"),
        f"team {entry.id}@{entry.version}\nhash: {entry.content_hash}\nobject: {entry.object_path}",
    )


@team_app.command("migrate")
def migrate(
    template: Annotated[Path, typer.Argument(help="Existing TeamTemplateV1 file.")],
    to_version: Annotated[int, typer.Option("--to")] = 2,
    output: Annotated[Path | None, typer.Option("--output")] = None,
    shared_supplied: Annotated[bool, typer.Option("--shared-supplied")] = False,
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Write a non-destructive V2 candidate and its semantic diff."""
    if to_version != 2:
        raise fail("only --to 2 is supported")
    destination = output or template.with_name(f"{template.stem}.v2{template.suffix or '.yaml'}")
    layout = (
        WorkspaceLayout.SHARED_SUPPLIED if shared_supplied else WorkspaceLayout.PER_MEMBER_WORKTREE
    )
    try:
        result = migrate_team_template_v1(template, workspace_layout=layout)
        write_team_migration(result, destination, input_path=template)
    except TeamTemplateError as error:
        raise fail(str(error)) from None
    payload = {
        "output": str(destination),
        "workspace_layout": layout.value,
        "diff": result.diff,
    }
    emit(
        json_out,
        payload,
        f"wrote V2 candidate: {destination}\nworkspace layout: {layout.value}\n{result.diff}",
    )


@team_app.command("validate")
def validate(
    template: Annotated[Path, typer.Argument(help="Path to a TeamTemplate YAML/JSON file.")],
    json_out: Annotated[bool, typer.Option("--json", help="Machine-readable output.")] = False,
) -> None:
    """Validate schema, composition shape, and prohibited content."""
    if _declared_schema_version(template) == 2:
        try:
            loaded_v2 = load_team_template_v2(template)
        except TeamTemplateError as error:
            raise fail(str(error)) from None
        template_hash = hashlib.sha256(loaded_v2.source.encode("utf-8")).hexdigest()
        problems = check_prohibited_text(loaded_v2.path.name, loaded_v2.source)
        payload = {
            "valid": not problems,
            "template_hash": template_hash,
            "problems": problems,
            "member_count": len(loaded_v2.definition.members),
            "task_count": len(loaded_v2.definition.workflow_skeleton),
        }
        if problems:
            emit(json_out, payload, "invalid: " + "; ".join(problems))
            raise typer.Exit(code=EXIT_INVALID)
        emit(
            json_out,
            payload,
            f"valid: {loaded_v2.definition.id} v{loaded_v2.definition.version} "
            f"(template hash {template_hash[:12]}...)",
        )
        return
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


def _declared_schema_version(path: Path) -> int | None:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return None
    if not isinstance(data, dict):
        return None
    value = data.get("schema_version")
    return value if isinstance(value, int) and not isinstance(value, bool) else None
