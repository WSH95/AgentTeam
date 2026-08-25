"""Negotiated, correlated bidirectional NDJSON for local interactive clients."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any

from agentteam.domain.interactive import (
    CompletionCriterionV1,
    ControlAction,
    ControlActor,
    ControlRequestV1,
    InteractiveRunOutcome,
    WorkItemV1,
)
from agentteam.domain.team import TeamTaskStatus
from agentteam.execution.protocol import ProviderEvent
from agentteam.interactive.controller import InteractiveController, InteractiveControllerError
from agentteam.interactive.permissions import PermissionDecision

PROTOCOL_VERSION = 1
MAX_FRAME_BYTES = 1024 * 1024
FrameWriter = Callable[[dict[str, Any]], Awaitable[None]]


class NdjsonDecodeError(ValueError):
    pass


class IncrementalNdjsonDecoder:
    def __init__(self, *, max_frame_bytes: int = MAX_FRAME_BYTES) -> None:
        self.buffer = b""
        self.max_frame_bytes = max_frame_bytes

    def feed(self, chunk: bytes) -> list[bytes]:
        self.buffer += chunk
        if len(self.buffer) > self.max_frame_bytes and b"\n" not in self.buffer:
            self.buffer = b""
            raise NdjsonDecodeError("fragmented frame exceeds maximum size")
        lines: list[bytes] = []
        while b"\n" in self.buffer:
            line, self.buffer = self.buffer.split(b"\n", 1)
            if len(line) > self.max_frame_bytes:
                raise NdjsonDecodeError("frame exceeds maximum size")
            if line.endswith(b"\r"):
                line = line[:-1]
            if line:
                lines.append(line)
        return lines

    def finish(self) -> None:
        if self.buffer:
            self.buffer = b""
            raise NdjsonDecodeError("input ended with a fragmented frame")


class StreamSession:
    def __init__(self, controller: InteractiveController, writer: FrameWriter) -> None:
        self.controller = controller
        self.writer = writer
        self.decoder = IncrementalNdjsonDecoder()
        self.negotiated = False
        self.expected_client_sequence = 0
        self.server_sequence = 0
        self.seen_ids: set[str] = set()
        self.attended_client = False
        self.turn_task: asyncio.Task[None] | None = None
        self.permission_waiters: dict[str, asyncio.Future[bool]] = {}
        self._write_lock = asyncio.Lock()
        self.closed = False

    async def feed(self, chunk: bytes) -> None:
        try:
            lines = self.decoder.feed(chunk)
        except NdjsonDecodeError as error:
            await self._error(None, "malformed", str(error))
            return
        for line in lines:
            await self.handle_line(line)

    async def finish(self) -> None:
        try:
            self.decoder.finish()
        except NdjsonDecodeError as error:
            await self._error(None, "malformed", str(error))
        for waiter in self.permission_waiters.values():
            if not waiter.done():
                waiter.set_result(False)
        if self.turn_task is not None and not self.turn_task.done():
            await self.controller.cancel_turn("stream input ended")
        if self.turn_task is not None:
            await asyncio.gather(self.turn_task, return_exceptions=True)
        if not self.closed and self.controller.record.phase.value != "closed":
            await self.controller.detach()
            self.closed = True

    async def handle_line(self, line: bytes) -> None:
        try:
            frame = json.loads(line)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            await self._error(None, "malformed", f"invalid JSON: {error}")
            return
        if not isinstance(frame, dict):
            await self._error(None, "malformed", "frame must be an object")
            return
        correlation = frame.get("id") if isinstance(frame.get("id"), str) else None
        schema = frame.get("schema")
        if schema != {"kind": "stream-command", "version": PROTOCOL_VERSION}:
            await self._error(correlation, "unsupported-schema", "unsupported schema identity")
            return
        command_id = frame.get("id")
        command = frame.get("command")
        sequence = frame.get("sequence")
        if not isinstance(command_id, str) or not command_id:
            await self._error(None, "malformed", "command id must be a non-empty string")
            return
        if not isinstance(command, str) or not command:
            await self._error(command_id, "malformed", "command must be a non-empty string")
            return
        if not isinstance(sequence, int) or isinstance(sequence, bool):
            await self._error(command_id, "malformed", "sequence must be an integer")
            return
        if sequence != self.expected_client_sequence:
            await self._error(
                command_id,
                "out-of-order",
                f"expected client sequence {self.expected_client_sequence}, got {sequence}",
            )
            return
        self.expected_client_sequence += 1
        if command_id in self.seen_ids:
            await self._error(command_id, "duplicate", "command id was already consumed")
            return
        self.seen_ids.add(command_id)
        if not self.negotiated:
            if command != "negotiate":
                await self._error(command_id, "negotiation-required", "negotiate before commands")
                return
            versions = frame.get("versions")
            if not isinstance(versions, list) or PROTOCOL_VERSION not in versions:
                await self._error(
                    command_id,
                    "unsupported-version",
                    "no supported protocol version",
                )
                return
            client_mode = frame.get("client_mode", "machine")
            if client_mode not in {"attended", "machine"}:
                await self._error(
                    command_id,
                    "unsupported-client-mode",
                    "client_mode must be attended or machine",
                )
                return
            self.attended_client = client_mode == "attended"
            self.negotiated = True
            await self._receipt(
                command_id,
                command,
                "ok",
                protocol_version=PROTOCOL_VERSION,
                client_mode=client_mode,
            )
            return
        if command == "negotiate":
            await self._error(command_id, "duplicate-negotiation", "protocol is already negotiated")
            return
        await self._dispatch(command_id, command, frame)

    async def _dispatch(self, command_id: str, command: str, frame: dict[str, Any]) -> None:
        try:
            if command == "status":
                await self._receipt(
                    command_id,
                    command,
                    "ok",
                    record=self.controller.record.model_dump(mode="json"),
                )
            elif command == "members":
                await self._receipt(
                    command_id,
                    command,
                    "ok",
                    members=[
                        item.model_dump(mode="json") for item in self.controller.record.members
                    ],
                )
            elif command == "tasks":
                await self._receipt(
                    command_id,
                    command,
                    "ok",
                    work_items=[
                        self.controller.work_items[item_id].model_dump(mode="json")
                        for item_id in self.controller.record.work_items
                    ],
                )
            elif command == "turn.start":
                await self._start_turn(command_id, frame)
            elif command == "turn.cancel":
                disposition = await self.controller.cancel_turn("stream client cancellation")
                await self._receipt(command_id, command, "ok", cancel_disposition=disposition)
            elif command == "permission.respond":
                await self._permission_response(command_id, command, frame)
            elif command == "member.reset":
                member = _required_string(frame, "member")
                session = await self.controller.reset_member(member)
                await self._receipt(
                    command_id,
                    command,
                    "ok",
                    session=session.model_dump(mode="json"),
                )
            elif command == "recover":
                recovery = await self.controller.recover()
                await self._receipt(command_id, command, "ok", recovery=recovery)
            elif command in {"work.create", "work.update", "work.assign"}:
                await self._work_control(command_id, command, frame)
            elif command == "completion.propose":
                await self._completion_propose(command_id, command, frame)
            elif command in {"completion.accept", "completion.reject"}:
                if command == "completion.accept" and not self.attended_client:
                    raise InteractiveControllerError(
                        "completion acceptance requires an attended client"
                    )
                record = await self.controller.decide_completion(
                    accept=command == "completion.accept"
                )
                await self._receipt(
                    command_id,
                    command,
                    "ok",
                    record=record.model_dump(mode="json"),
                )
                if record.phase.value == "closed":
                    self.closed = True
            elif command == "abort":
                record = await self.controller.close(
                    InteractiveRunOutcome.CANCELLED,
                    reason="stream client abort",
                )
                await self._receipt(
                    command_id,
                    command,
                    "ok",
                    record=record.model_dump(mode="json"),
                )
                if record.phase.value == "closed":
                    self.closed = True
            elif command == "close":
                record = await self.controller.close(
                    InteractiveRunOutcome.ABANDONED,
                    reason="stream client close",
                )
                await self._receipt(
                    command_id,
                    command,
                    "ok",
                    record=record.model_dump(mode="json"),
                )
                if record.phase.value == "closed":
                    self.closed = True
            elif command == "detach":
                await self.controller.detach()
                self.closed = True
                await self._receipt(command_id, command, "ok")
            elif command.startswith("dynamic."):
                await self._error(
                    command_id,
                    "dynamic-members-disabled",
                    "dynamic Member controls are denied until M1d",
                )
            else:
                await self._error(
                    command_id,
                    "unsupported-command",
                    f"unsupported command: {command}",
                )
        except (InteractiveControllerError, ValueError) as error:
            await self._error(command_id, "invalid-command", str(error))

    async def _start_turn(self, command_id: str, frame: dict[str, Any]) -> None:
        if self.turn_task is not None and not self.turn_task.done():
            raise InteractiveControllerError("one turn is already active")
        member = _required_string(frame, "member")
        text = _required_string(frame, "text")
        work_item = frame.get("work_item_id")
        if work_item is not None and not isinstance(work_item, str):
            raise ValueError("work_item_id must be a string")
        await self._receipt(command_id, "turn.start", "accepted")

        async def provider_event(event: ProviderEvent) -> None:
            await self._event(
                "provider-event",
                command_id,
                provider_event={
                    "event": event.event,
                    "text": event.text,
                    "data": dict(event.data),
                },
            )

        async def approve(event: ProviderEvent, decision: PermissionDecision) -> bool:
            permission_id = event.data.get("permission_id")
            if not isinstance(permission_id, str) or not permission_id:
                return False
            previous = self.permission_waiters.get(permission_id)
            if previous is not None and not previous.done():
                previous.set_result(False)
            waiter: asyncio.Future[bool] = asyncio.get_running_loop().create_future()
            self.permission_waiters[permission_id] = waiter
            await self._event(
                "permission-awaiting",
                command_id,
                permission_id=permission_id,
                classification=decision.classification.value,
                reasons=list(decision.reasons),
            )
            try:
                return await waiter
            finally:
                self.permission_waiters.pop(permission_id, None)

        async def run() -> None:
            try:
                outcome = await self.controller.dispatch(
                    member,
                    text,
                    work_item_id=work_item,
                    permission_approver=approve,
                    event_sink=provider_event,
                )
                await self._event(
                    "turn-terminal",
                    command_id,
                    turn=outcome.turn.model_dump(mode="json"),
                    result={
                        "status": outcome.result.status.value,
                        "text": outcome.text,
                        "stop_reason": outcome.result.stop_reason,
                        "error": outcome.result.error,
                    },
                )
            except asyncio.CancelledError:
                raise
            except Exception as error:
                await self._event(
                    "turn-terminal",
                    command_id,
                    result={"status": "failed", "error": str(error)},
                )

        self.turn_task = asyncio.create_task(run())

    async def _permission_response(
        self, command_id: str, command: str, frame: dict[str, Any]
    ) -> None:
        permission_id = _required_string(frame, "permission_id")
        approved = frame.get("approved")
        if not isinstance(approved, bool):
            raise ValueError("approved must be a boolean")
        attended = frame.get("attended", False)
        if approved and (not self.attended_client or attended is not True):
            approved = False
        waiter = self.permission_waiters.get(permission_id)
        if waiter is None or waiter.done():
            raise ValueError("permission request is not pending")
        waiter.set_result(approved)
        await self._receipt(command_id, command, "ok", permission_id=permission_id)

    async def _work_control(self, command_id: str, command: str, frame: dict[str, Any]) -> None:
        if command == "work.create":
            item = WorkItemV1.model_validate(frame.get("work_item"))
            request = ControlRequestV1(
                schema_version=1,
                kind="control-request",
                request_id=command_id,
                run_id=self.controller.record.run_id,
                actor=ControlActor.USER,
                action=ControlAction.WORK_CREATE,
                work_item=item,
            )
        elif command == "work.update":
            request = ControlRequestV1(
                schema_version=1,
                kind="control-request",
                request_id=command_id,
                run_id=self.controller.record.run_id,
                actor=ControlActor.USER,
                action=ControlAction.WORK_UPDATE,
                work_item_id=_required_string(frame, "work_item_id"),
                status=TeamTaskStatus(_required_string(frame, "status")),
            )
        else:
            request = ControlRequestV1(
                schema_version=1,
                kind="control-request",
                request_id=command_id,
                run_id=self.controller.record.run_id,
                actor=ControlActor.USER,
                action=ControlAction.WORK_ASSIGN,
                work_item_id=_required_string(frame, "work_item_id"),
                owner=_required_string(frame, "owner"),
            )
        receipt = await self.controller.queue_control(request)
        await self._receipt(
            command_id,
            command,
            "ok",
            control_receipt=receipt.model_dump(mode="json"),
        )

    async def _completion_propose(
        self, command_id: str, command: str, frame: dict[str, Any]
    ) -> None:
        criteria = [
            CompletionCriterionV1.model_validate(item) for item in frame.get("criteria", [])
        ]
        work_items = frame.get("work_items")
        if not isinstance(work_items, list) or not all(
            isinstance(item, str) for item in work_items
        ):
            raise ValueError("work_items must be a list of strings")
        receipt = await self.controller.propose_completion(
            proposed_by=self.controller.team.lead,
            source_turn_id=_required_string(frame, "source_turn_id"),
            summary=_required_string(frame, "summary"),
            criteria=criteria,
            work_items=work_items,
        )
        await self._receipt(
            command_id,
            command,
            "ok",
            control_receipt=receipt.model_dump(mode="json"),
        )

    async def _receipt(
        self,
        correlation_id: str,
        command: str,
        status: str,
        **data: Any,
    ) -> None:
        await self._write(
            {
                "schema": {"kind": "stream-receipt", "version": PROTOCOL_VERSION},
                "run_id": self.controller.record.run_id,
                "correlation_id": correlation_id,
                "command": command,
                "status": status,
                **data,
            }
        )

    async def _event(self, event: str, correlation_id: str | None, **data: Any) -> None:
        await self._write(
            {
                "schema": {"kind": "stream-event", "version": PROTOCOL_VERSION},
                "run_id": self.controller.record.run_id,
                "correlation_id": correlation_id,
                "event": event,
                **data,
            }
        )

    async def _error(self, correlation_id: str | None, code: str, message: str) -> None:
        await self._write(
            {
                "schema": {"kind": "stream-receipt", "version": PROTOCOL_VERSION},
                "run_id": self.controller.record.run_id,
                "correlation_id": correlation_id,
                "status": "error",
                "error": {"code": code, "message": message},
            }
        )

    async def _write(self, frame: dict[str, Any]) -> None:
        async with self._write_lock:
            frame["sequence"] = self.server_sequence
            self.server_sequence += 1
            await self.writer(frame)


def _required_string(frame: dict[str, Any], name: str) -> str:
    value = frame.get(name)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value
