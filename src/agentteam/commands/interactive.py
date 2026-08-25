"""Interactive chat and durable run-management command services."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Annotated

import typer

from agentteam.commands.common import EXIT_RUNTIME, emit, fail
from agentteam.interactive.archive import (
    InteractiveArchive,
    InteractiveArchiveError,
    InteractiveRunStore,
)
from agentteam.interactive.controller import (
    InteractiveController,
    InteractiveControllerError,
    InteractiveInitializationError,
)
from agentteam.interactive.resolution import (
    InteractiveResolutionError,
    PreparedChat,
    default_interactive_roots,
    prepare_assistant_chat,
    prepare_attach,
    prepare_team_chat,
)
from agentteam.interactive.stream import MAX_FRAME_BYTES, StreamSession
from agentteam.interactive.tty import run_tty

runs_app = typer.Typer(name="runs", help="Durable interactive TeamRuns.")


def assistant_chat_service(
    *,
    item_id: str | None,
    version: int | None,
    path: Path | None,
    workspace: Path,
    goal: str,
    done_when: list[str],
    stream_json: bool,
) -> None:
    try:
        prepared = prepare_assistant_chat(
            item_id=item_id,
            version=version,
            path=path,
            workspace=workspace,
            goal=goal,
            done_when=done_when,
        )
    except InteractiveResolutionError as error:
        raise fail(str(error), exit_code=EXIT_RUNTIME) from None
    _run_prepared(prepared, stream_json=stream_json)


def team_chat_service(
    *,
    item_id: str | None,
    version: int | None,
    path: Path | None,
    workspace: Path,
    goal: str,
    done_when: list[str],
    stream_json: bool,
) -> None:
    try:
        prepared = prepare_team_chat(
            item_id=item_id,
            version=version,
            path=path,
            workspace=workspace,
            goal=goal,
            done_when=done_when,
        )
    except InteractiveResolutionError as error:
        raise fail(str(error), exit_code=EXIT_RUNTIME) from None
    _run_prepared(prepared, stream_json=stream_json)


def _run_prepared(prepared: PreparedChat, *, stream_json: bool) -> None:
    try:
        asyncio.run(_create_and_run(prepared, stream_json=stream_json))
    except InteractiveInitializationError as error:
        raise fail(str(error), exit_code=EXIT_RUNTIME) from None
    except InteractiveControllerError as error:
        raise fail(str(error), exit_code=EXIT_RUNTIME) from None


async def _create_and_run(prepared: PreparedChat, *, stream_json: bool) -> None:
    controller = await InteractiveController.create(
        request=prepared.request,
        team=prepared.team,
        team_source=prepared.team_source,
        launches=prepared.launches,
        runs_root=prepared.runs_root,
        reservations_root=prepared.reservations_root,
    )
    if stream_json:
        await _run_stream(controller)
    else:
        await run_tty(controller)


async def _run_stream(controller: InteractiveController) -> None:
    async def write(frame: dict[str, object]) -> None:
        sys.stdout.write(json.dumps(frame, separators=(",", ":"), ensure_ascii=False) + "\n")
        sys.stdout.flush()

    session = StreamSession(controller, write)
    while not session.closed:
        line = await asyncio.to_thread(sys.stdin.buffer.readline, MAX_FRAME_BYTES + 2)
        if not line:
            break
        await session.feed(line)
    await session.finish()


@runs_app.command("list")
def list_runs(json_out: bool = typer.Option(False, "--json")) -> None:
    """List durable interactive runs without attaching to a provider."""
    runs_root, _reservations = default_interactive_roots()
    try:
        records = InteractiveRunStore(runs_root).list_records()
    except InteractiveArchiveError as error:
        raise fail(str(error), exit_code=EXIT_RUNTIME) from None
    payload = {"runs": [record.model_dump(mode="json") for record in records]}
    human = (
        "\n".join(
            f"{record.run_id} {record.phase.value} "
            f"{record.outcome.value if record.outcome else '-'} "
            f"{record.target.kind.value}:{record.target.id}@{record.target.version}"
            for record in records
        )
        or "no interactive runs"
    )
    emit(json_out, payload, human)


@runs_app.command("status")
def run_status(
    run_id: str = typer.Argument(..., help="Interactive run id."),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Read one durable run record; never establish provider continuity."""
    runs_root, _reservations = default_interactive_roots()
    try:
        archive = InteractiveRunStore(runs_root).archive(run_id)
        record = archive.load_run()
        manifest = archive.verify_manifest() if record.phase.value == "closed" else None
    except InteractiveArchiveError as error:
        raise fail(str(error), exit_code=EXIT_RUNTIME) from None
    payload = record.model_dump(mode="json")
    if manifest is not None:
        payload["manifest_problems"] = manifest
    emit(
        json_out,
        payload,
        f"{record.run_id}: {record.phase.value}\n"
        f"outcome: {record.outcome.value if record.outcome else '-'}\n"
        f"workspace: {record.workspace}\n"
        f"members: {', '.join(member.name for member in record.members)}\n"
        f"turns: {len(record.turns)}; work items: {len(record.work_items)}",
    )


@runs_app.command("attach")
def attach_run(
    run_id: str = typer.Argument(..., help="Nonterminal interactive run id."),
    stream_json: bool = typer.Option(False, "--stream-json"),
) -> None:
    """Acquire the recovery shell; prompting stays disabled until strict recovery."""
    runs_root, _reservations = default_interactive_roots()
    try:
        archive = InteractiveRunStore(runs_root).archive(run_id)
        prepared = prepare_attach(archive)
        asyncio.run(_attach_and_run(archive, prepared, stream_json=stream_json))
    except (InteractiveArchiveError, InteractiveResolutionError) as error:
        raise fail(str(error), exit_code=EXIT_RUNTIME) from None
    except InteractiveControllerError as error:
        raise fail(str(error), exit_code=EXIT_RUNTIME) from None


async def _attach_and_run(
    archive: InteractiveArchive,
    prepared: PreparedChat,
    *,
    stream_json: bool,
) -> None:
    controller = InteractiveController.attach(
        archive=archive,
        team=prepared.team,
        launches=prepared.launches,
        reservations_root=prepared.reservations_root,
    )
    if stream_json:
        await _run_stream(controller)
    else:
        await run_tty(controller)


@runs_app.command("export")
def export_run(
    run_id: Annotated[str, typer.Argument(help="Interactive run id.")],
    destination: Annotated[Path, typer.Argument(help="Empty audit-export directory.")],
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Export definitions and audit records while excluding transcripts/runtime state."""
    runs_root, _reservations = default_interactive_roots()
    try:
        archive = InteractiveRunStore(runs_root).archive(run_id)
        exported = archive.export_audit(destination)
    except InteractiveArchiveError as error:
        raise fail(str(error), exit_code=EXIT_RUNTIME) from None
    emit(
        json_out,
        {"run_id": run_id, "destination": str(exported)},
        f"exported audit records for {run_id}: {exported}",
    )


@runs_app.command("cleanup")
def cleanup_run(
    run_id: str = typer.Argument(..., help="Closed interactive run id."),
    json_out: bool = typer.Option(False, "--json"),
) -> None:
    """Permanently remove exactly one closed local interactive archive."""
    runs_root, _reservations = default_interactive_roots()
    try:
        InteractiveRunStore(runs_root).cleanup_closed(run_id)
    except InteractiveArchiveError as error:
        raise fail(str(error), exit_code=EXIT_RUNTIME) from None
    emit(
        json_out,
        {"run_id": run_id, "removed": True, "recoverable": False},
        f"removed closed run {run_id}; the local archive is not recoverable",
    )
