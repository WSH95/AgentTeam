"""Small attended terminal shell over the shared interactive controller."""

from __future__ import annotations

import shlex
from collections.abc import Callable

from agentteam.domain.interactive import InteractiveRunOutcome, InteractiveRunPhase
from agentteam.execution.protocol import ProviderEvent
from agentteam.interactive.controller import InteractiveController, InteractiveControllerError
from agentteam.interactive.permissions import PermissionDecision

InputFn = Callable[[str], str]
OutputFn = Callable[[str], None]

HELP = """Commands:
  /to MEMBER       select the destination Member
  /members         show the fixed roster and current sessions
  /tasks           show the normalized work-item graph
  /reset [MEMBER]  close/dispose one generation and open a fresh one
  /cancel-turn     cancel the active turn, if any
  /proposal        show the pending completion proposal
  /accept          accept the pending proposal and close succeeded
  /continue        reject the pending proposal and continue the run
  /recover         prove strict provider continuity after attach
  /abort           cancel and close the run
  /close           abandon and close the run
  /detach          leave sessions retained and mark the run interrupted
  /help            show this help
"""


async def run_tty(
    controller: InteractiveController,
    *,
    input_fn: InputFn = input,
    output_fn: OutputFn = print,
) -> None:
    selected = controller.team.lead
    output_fn(f"interactive run {controller.record.run_id}; Lead: {controller.team.lead}")
    output_fn("Use /help for commands. Completion succeeds only after /accept.")
    while controller.record.phase is not InteractiveRunPhase.CLOSED:
        try:
            line = input_fn(f"[{selected}]> ")
        except EOFError:
            await controller.detach()
            output_fn("detached; the run is interrupted and its workspace remains reserved")
            return
        except KeyboardInterrupt:
            disposition = await controller.cancel_turn("terminal interrupt")
            output_fn(f"turn cancellation: {disposition}; run remains open")
            continue
        if not line.strip():
            continue
        if line.startswith("/"):
            try:
                selected, should_return = await _command(
                    controller,
                    line,
                    selected=selected,
                    output_fn=output_fn,
                )
            except (InteractiveControllerError, ValueError) as error:
                output_fn(f"error: {error}")
                continue
            if should_return:
                return
            continue

        async def approve(event: ProviderEvent, decision: PermissionDecision) -> bool:
            title = event.data.get("tool_title", event.data.get("tool_kind", "tool"))
            tool_input = event.data.get("tool_input")
            if tool_input:
                output_fn(f"requested input: {tool_input}")
            answer = input_fn(f"Allow once [{decision.classification.value}] {title}? [y/N] ")
            return answer.strip().lower() in {"y", "yes"}

        try:
            outcome = await controller.dispatch(
                selected,
                line,
                permission_approver=approve,
            )
        except KeyboardInterrupt:
            disposition = await controller.cancel_turn("terminal interrupt")
            output_fn(f"turn cancellation: {disposition}; run remains open")
            continue
        except InteractiveControllerError as error:
            output_fn(f"error: {error}")
            continue
        if outcome.text:
            output_fn(outcome.text)
        elif outcome.result.error:
            output_fn(f"turn failed: {outcome.result.error}")
        else:
            output_fn(f"turn {outcome.result.status.value}")


async def _command(
    controller: InteractiveController,
    line: str,
    *,
    selected: str,
    output_fn: OutputFn,
) -> tuple[str, bool]:
    try:
        words = shlex.split(line)
    except ValueError as error:
        raise ValueError(f"invalid command quoting: {error}") from None
    command = words[0].lower()
    arguments = words[1:]
    if command == "/help":
        output_fn(HELP.rstrip())
    elif command == "/to":
        if len(arguments) != 1 or arguments[0] not in controller.launches:
            raise ValueError("usage: /to MEMBER (Member must be in the roster)")
        selected = arguments[0]
    elif command == "/members":
        for member in controller.record.members:
            session = controller.session_records[member.name]
            marker = " Lead" if member.name == controller.team.lead else ""
            output_fn(
                f"{member.name}{marker}: {session.status.value}, "
                f"generation {session.generation}, provider {session.provider}"
            )
    elif command == "/tasks":
        if not controller.record.work_items:
            output_fn("no work items")
        for item_id in controller.record.work_items:
            item = controller.work_items[item_id]
            blockers = ",".join(item.blocked_by) or "-"
            output_fn(
                f"{item.id}: {item.status.value}; owner={item.owner}; "
                f"access={item.workspace_access.value}; blocked_by={blockers}; {item.subject}"
            )
    elif command == "/reset":
        if len(arguments) > 1:
            raise ValueError("usage: /reset [MEMBER]")
        reset_member_name = arguments[0] if arguments else selected
        session = await controller.reset_member(reset_member_name)
        output_fn(f"reset {reset_member_name}: generation {session.generation}")
    elif command == "/cancel-turn":
        output_fn(f"turn cancellation: {await controller.cancel_turn()}")
    elif command == "/proposal":
        pending = [item for item in controller.proposals.values() if item.status.value == "pending"]
        if not pending:
            output_fn("no pending completion proposal")
        else:
            proposal = pending[0]
            output_fn(f"{proposal.proposal_id}: {proposal.summary}")
            for criterion in proposal.criteria:
                evidence = ", ".join(criterion.evidence) or "no evidence"
                output_fn(f"- {criterion.criterion}: {evidence}")
    elif command == "/accept":
        record = await controller.decide_completion(accept=True)
        output_fn(f"run closed: {record.outcome.value if record.outcome else record.phase.value}")
        return selected, True
    elif command == "/continue":
        await controller.decide_completion(accept=False)
        output_fn("completion rejected; run is open")
    elif command == "/recover":
        result = await controller.recover()
        output_fn(
            "recovery: "
            + ", ".join(
                f"{member_name}={'ok' if ok else 'lost'}" for member_name, ok in result.items()
            )
        )
    elif command == "/abort":
        record = await controller.close(
            InteractiveRunOutcome.CANCELLED,
            reason="terminal user abort",
        )
        output_fn(f"run {record.phase.value}")
        return selected, True
    elif command == "/close":
        record = await controller.close(
            InteractiveRunOutcome.ABANDONED,
            reason="terminal user close",
        )
        output_fn(f"run {record.phase.value}")
        return selected, True
    elif command == "/detach":
        await controller.detach()
        output_fn("detached; the run is interrupted and its workspace remains reserved")
        return selected, True
    else:
        raise ValueError(f"unknown command: {command}")
    return selected, False
