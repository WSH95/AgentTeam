"""The ClawTeam anti-corruption seam (plan section 10) — not a second runtime.

Containments, mapped to the section-10 contract and verified against the
pinned revision's source (2026-08-23):

1. Importable only when the `clawteam` extra is installed; a missing package
   raises `ClawTeamUnavailableError` and the direct core is untouched.
2. One data root per process, fixed before the first coordination operation
   (`CLAWTEAM_DATA_DIR` is set so `get_data_dir()` never consults the config
   file); a second root raises `DataRootFixedError`. The owner's default
   `~/.clawteam` is refused outright.
3. Opaque AgentTeam team names (`atm-<hex8>`) and the explicit file
   primitives only: `FileTaskStore` and a `FileTransport` passed explicitly
   to `MailboxManager`, so the config's transport choice can never activate
   (p2p/redis stay dark).
4. The global event bus is replaced with a fresh `EventBus` and the
   config-hook loader is marked spent *before any operation* — user-configured
   shell/python hooks (loaded from the always-`~/.clawteam/config.json`
   `load_config()` on first `get_event_bus()`) can never execute here.
5. Never the subprocess/tmux/wsh backends, the template launcher, the
   keepalive wrapper, or the CLI adapter chain: only team/store/mailbox/
   snapshot primitives are imported.
6. The exact package version and pinned revision travel in `info()` with the
   achieved isolation level, which is `namespace` — nothing mechanical.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar
from uuid import uuid4

PINNED_REVISION = "01198332ef9270c32c5460b8a178f964fc0df451"


class ClawTeamUnavailableError(RuntimeError):
    """The optional `clawteam` extra is not installed."""


class DataRootFixedError(RuntimeError):
    """The process-wide ClawTeam data root is already fixed (or unsafe)."""


@dataclass(frozen=True)
class SeamInfo:
    version: str
    revision: str
    isolation: str


@dataclass(frozen=True)
class HookContainmentReport:
    bus_replaced: bool
    subscriber_count: int
    config_hook_loader_disarmed: bool


def _import_clawteam() -> Any:
    try:
        import clawteam
    except ImportError as error:
        raise ClawTeamUnavailableError(
            "the clawteam extra is not installed; run "
            "`uv sync --frozen --all-groups --extra clawteam`"
        ) from error
    return clawteam


class ClawTeamCompat:
    _fixed_root: ClassVar[Path | None] = None
    _bus: ClassVar[Any] = None

    def __init__(self, data_root: Path) -> None:
        clawteam = _import_clawteam()
        root = data_root.resolve()
        owner_default = (Path.home() / ".clawteam").resolve()
        if root == owner_default or owner_default in root.parents:
            raise DataRootFixedError("refusing to operate against the owner's ~/.clawteam state")
        fixed = type(self)._fixed_root
        if fixed is not None and fixed != root:
            raise DataRootFixedError(
                f"the ClawTeam data root is already fixed to {fixed}; one root per process"
            )
        os.environ["CLAWTEAM_DATA_DIR"] = str(root)
        self._disarm_hooks()
        type(self)._fixed_root = root
        self._clawteam = clawteam
        self._root = root

    # -- containment ----------------------------------------------------------

    @classmethod
    def _disarm_hooks(cls) -> None:
        """Replace the global bus and mark the config-hook loader spent."""
        from clawteam.events import global_bus
        from clawteam.events.bus import EventBus

        global_bus.reset_event_bus()
        fresh = EventBus()
        global_bus._bus = fresh
        global_bus._initialized = True  # get_event_bus() will never load hooks
        cls._bus = fresh

    def hook_containment_report(self) -> HookContainmentReport:
        from clawteam.events import global_bus

        current = global_bus.get_event_bus()
        subscribers = getattr(current, "_subscribers", None)
        count = len(subscribers) if subscribers is not None else -1
        return HookContainmentReport(
            bus_replaced=current is type(self)._bus,
            subscriber_count=count,
            config_hook_loader_disarmed=bool(global_bus._initialized),
        )

    def info(self) -> SeamInfo:
        version = getattr(self._clawteam, "__version__", "0.3.0")
        return SeamInfo(version=version, revision=PINNED_REVISION, isolation="namespace")

    # -- team lifecycle -------------------------------------------------------

    def create_space(self, *, leader: str) -> str:
        from clawteam.team.manager import TeamManager

        name = f"atm-{uuid4().hex[:8]}"
        # user stays empty: a user name prefixes inbox directories
        # ("{user}_{agent}"), which would desynchronise send and receive.
        TeamManager.create_team(
            name,
            leader_name=leader,
            leader_id=uuid4().hex,
            description="AgentTeam compatibility qualification",
            user="",
            leader_agent_type="general-purpose",
        )
        return name

    def add_member(self, space: str, member: str) -> None:
        from clawteam.team.manager import TeamManager

        TeamManager.add_member(space, member, uuid4().hex)

    def members(self, space: str) -> list[str]:
        from clawteam.team.manager import TeamManager

        return [member.name for member in TeamManager.list_members(space)]

    def cleanup(self, space: str) -> None:
        from clawteam.team.manager import TeamManager

        TeamManager.cleanup(space)

    # -- tasks ----------------------------------------------------------------

    def create_task(self, space: str, subject: str, *, blocked_by: list[str] | None = None) -> str:
        from clawteam.store.file import FileTaskStore

        task = FileTaskStore(space).create(subject=subject, blocked_by=blocked_by or [])
        return str(task.id)

    def task(self, space: str, task_id: str) -> dict[str, Any]:
        from clawteam.store.file import FileTaskStore

        task = FileTaskStore(space).get(task_id)
        if task is None:
            raise KeyError(task_id)
        payload = task.model_dump(mode="json")
        assert isinstance(payload, dict)
        return payload

    def tasks(self, space: str) -> list[dict[str, Any]]:
        from clawteam.store.file import FileTaskStore

        return [task.model_dump(mode="json") for task in FileTaskStore(space).list_tasks()]

    def update_task(self, space: str, task_id: str, status: str, *, caller: str) -> None:
        from clawteam.store.file import FileTaskStore
        from clawteam.team.models import TaskStatus

        FileTaskStore(space).update(task_id, status=TaskStatus(status), caller=caller)

    # -- mailbox --------------------------------------------------------------

    def _mailbox(self, space: str) -> Any:
        from clawteam.team.mailbox import MailboxManager
        from clawteam.transport.file import FileTransport

        return MailboxManager(space, transport=FileTransport(space))

    def send(self, space: str, sender: str, recipient: str, body: str) -> None:
        self._mailbox(space).send(sender, recipient, content=body)

    def receive(self, space: str, recipient: str, *, limit: int = 10) -> list[dict[str, Any]]:
        messages = self._mailbox(space).receive(recipient, limit=limit)
        return [message.model_dump(mode="json") for message in messages]

    # -- snapshots ------------------------------------------------------------

    def snapshot(self, space: str, tag: str = "") -> str:
        from clawteam.team.snapshot import SnapshotManager

        meta = SnapshotManager(space).create(tag)
        return str(meta.id)

    def read_snapshot(self, space: str, snapshot_id: str) -> dict[str, Any]:
        from clawteam.team.snapshot import SnapshotManager

        bundle = SnapshotManager(space).load_bundle(snapshot_id)
        assert isinstance(bundle, dict)
        return bundle

    def restore(self, space: str, snapshot_id: str) -> dict[str, Any]:
        from clawteam.team.snapshot import SnapshotManager

        result = SnapshotManager(space).restore(snapshot_id)
        assert isinstance(result, dict)
        return result

    # -- test escape hatch ----------------------------------------------------

    @classmethod
    def _reset_for_tests(cls) -> None:
        """Re-arm the one-root-per-process contract (tests only)."""
        cls._fixed_root = None
        cls._bus = None
        os.environ.pop("CLAWTEAM_DATA_DIR", None)
