"""The append-only run event log (plan section 13).

One JSON line per event under the archive root. Events carry ids, names, and
short detail strings only — never filesystem paths or environment values.
Emission is synchronous (one buffered write per line) and guarded by a lock so
the cancellation finalizer can share it with the event loop's tasks.
"""

from __future__ import annotations

import os
import threading
from datetime import UTC, datetime
from pathlib import Path

from pydantic import AwareDatetime

from agentteam.domain.common import RecordModel


class EventV1(RecordModel):
    ts: AwareDatetime
    event: str
    run_id: str
    invocation_id: str | None = None
    detail: str | None = None


class EventLog:
    def __init__(self, path: Path, *, run_id: str) -> None:
        self._path = path
        self._run_id = run_id
        self._lock = threading.Lock()

    def emit(
        self,
        event: str,
        *,
        invocation_id: str | None = None,
        detail: str | None = None,
    ) -> None:
        record = EventV1(
            ts=datetime.now(tz=UTC),
            event=event,
            run_id=self._run_id,
            invocation_id=invocation_id,
            detail=detail,
        )
        line = record.model_dump_json(exclude_none=True) + "\n"
        # 0600 from the first byte (G6.R3); the mode applies at creation only
        # and a permissive umask can never widen it.
        with (
            self._lock,
            open(self._path, "a", encoding="utf-8", opener=self._owner_only_opener) as handle,
        ):
            handle.write(line)

    @staticmethod
    def _owner_only_opener(path: str, flags: int) -> int:
        return os.open(path, flags, 0o600)
