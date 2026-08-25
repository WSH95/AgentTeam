"""Coordination protocol vocabulary, DTO, and error invariants (M1b G2)."""

from __future__ import annotations

import ast
from dataclasses import fields, is_dataclass
from pathlib import Path

import pytest

from agentteam.coordination.local import LocalCoordinationProvider
from agentteam.coordination.protocol import (
    CleanupOutcome,
    CleanupWarningCode,
    CoordinationError,
    CoordinationSubstrate,
    SnapshotState,
    SpaceUnavailableError,
    SubstrateInfo,
    SubstrateMessage,
    SubstrateTask,
    SubstrateTaskStatus,
    TaskClaimError,
    TaskCycleError,
    UnknownRecipientError,
    UnknownTaskError,
    WaitTimeoutError,
    wait_for_tasks,
)
from agentteam.domain.team import TeamTaskStatus

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_protocol_status_is_run_vocabulary_minus_run_only_terminals() -> None:
    protocol = {status.value for status in SubstrateTaskStatus}
    run = {status.value for status in TeamTaskStatus}
    assert protocol == run - {"failed", "cancelled", "abandoned"}


def test_frozen_dtos_have_exact_fields() -> None:
    expected = {
        SubstrateTask: ["id", "subject", "status", "blocked_by"],
        SubstrateMessage: ["sender", "recipient", "body"],
        SubstrateInfo: ["kind", "version", "revision", "achieved_isolation"],
        CleanupOutcome: ["space_closed", "snapshot_state", "warning_codes"],
    }
    for dto, names in expected.items():
        assert is_dataclass(dto)
        assert [field.name for field in fields(dto)] == names
        assert vars(dto)["__dataclass_params__"].frozen


def test_error_taxonomy_and_closed_cleanup_vocabularies() -> None:
    for error in (
        SpaceUnavailableError,
        TaskCycleError,
        TaskClaimError,
        UnknownTaskError,
        UnknownRecipientError,
        WaitTimeoutError,
    ):
        assert issubclass(error, CoordinationError)
    assert {state.value for state in SnapshotState} == {
        "none",
        "retained",
        "removed",
        "unknown",
    }
    assert {warning.value for warning in CleanupWarningCode} == {
        "upstream-cleanup-failed",
        "snapshot-deletion-failed",
    }


def test_local_provider_structurally_implements_protocol(tmp_path: Path) -> None:
    assert isinstance(LocalCoordinationProvider(tmp_path / "coordination"), CoordinationSubstrate)


def test_wait_helper_rejects_unbounded_configuration(tmp_path: Path) -> None:
    provider = LocalCoordinationProvider(tmp_path / "coordination")
    space = provider.create_space(lead="lead")
    with pytest.raises(ValueError, match="non-negative"):
        wait_for_tasks(provider, space, lambda _tasks: False, timeout_seconds=-1)
    with pytest.raises(ValueError, match="positive"):
        wait_for_tasks(
            provider,
            space,
            lambda _tasks: False,
            timeout_seconds=1,
            poll_interval_seconds=0,
        )


def test_local_provider_has_no_background_runtime_imports() -> None:
    path = REPO_ROOT / "src" / "agentteam" / "coordination" / "local.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".", 1)[0])
    assert imported.isdisjoint({"asyncio", "threading", "multiprocessing"})
