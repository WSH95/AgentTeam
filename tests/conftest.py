"""Shared builders: one minimal, valid instance of every V1 record."""

from __future__ import annotations

import shutil
import sys
from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

import pytest

if TYPE_CHECKING:
    from agentteam.harness.types import RenderContext

H64 = "a" * 64
NOW = datetime(2026, 8, 23, 12, 0, 0, tzinfo=UTC)


@pytest.fixture()
def assert_owner_only_tree() -> Callable[[Path], None]:
    """Recursive owner-only assertion shared by the G6.R3 tests: root and
    every descendant dir 0700, every file 0600; symlinks skipped (the
    production sweeps never chmod through a link)."""

    def check(root: Path) -> None:
        __tracebackhide__ = True
        assert root.stat().st_mode & 0o777 == 0o700, root
        for path in root.rglob("*"):
            if path.is_symlink():
                continue
            expected = 0o700 if path.is_dir() else 0o600
            assert path.stat().st_mode & 0o777 == expected, path

    return check


@pytest.fixture(scope="session", autouse=True)
def _fake_profile_homes() -> Iterator[None]:
    """The checked-in fake profile models persistent, but disposable, homes."""
    root = Path(__file__).resolve().parents[1] / "examples" / "profiles" / ".agentteam-local"
    for harness in ("claude-code", "codex", "grok"):
        home = root / "vendors" / harness
        home.mkdir(parents=True, exist_ok=True)
        if sys.platform != "win32":
            home.chmod(0o700)
    yield
    shutil.rmtree(root, ignore_errors=True)


def minimal_payloads() -> dict[str, dict[str, Any]]:
    """Minimal valid JSON payloads keyed by schema file name."""
    member = {
        "name": "reviewer",
        "assistant": {"id": "code-reviewer", "version": 1, "package_hash": H64},
        "effective_definition_hash": H64,
        "execution": {"kind": "invocation", "ref": "inv-1"},
    }
    return {
        "assistant-definition-v1.schema.json": {
            "schema_version": 1,
            "kind": "assistant-definition",
            "id": "code-reviewer",
            "version": 1,
            "summary": "Reviews code.",
            "persona": "persona.md",
            "purpose": ["review changes"],
            "principles": "principles.md",
        },
        "harness-profile-set-v1.schema.json": {
            "schema_version": 1,
            "kind": "harness-profile-set",
            "profiles": [
                {
                    "harness": "codex",
                    "executable": "codex",
                    "config_home": "~/.agentteam/vendors/codex",
                    "environment": {"config_home_variable": "CODEX_HOME"},
                }
            ],
            "default_harness": "codex",
        },
        "run-request-v1.schema.json": {
            "schema_version": 1,
            "kind": "run-request",
            "assistant": "examples/assistants/code-reviewer",
            "workspace": "fixtures/review-target",
            "task_file": "task.md",
            "mode": "direct",
        },
        "team-template-v1.schema.json": {
            "schema_version": 1,
            "kind": "team-template",
            "id": "development",
            "version": 1,
            "summary": "Plans and implements a bounded goal.",
            "members": [
                {"name": "lead", "assistant": "../assistants/code-reviewer"},
                {"name": "implementer", "assistant": "../assistants/implementer"},
            ],
            "lead": "lead",
            "handoff": {"required_fields": [], "acks": []},
            "independence": [],
            "preferences": {},
            "workflow_skeleton": [
                {"id": "plan", "subject": "Plan {goal}", "owner": "lead"},
                {
                    "id": "implement",
                    "subject": "Implement {goal}",
                    "owner": "implementer",
                    "blocked_by": ["plan"],
                    "workspace_access": "workspace-write",
                },
            ],
        },
        "team-run-request-v1.schema.json": {
            "schema_version": 1,
            "kind": "team-run-request",
            "template": "../teams/development.yaml",
            "workspace": "../../fixtures/review-target",
            "task_file": "review-task.md",
            "goal": "improve the review target safely",
        },
        "member-result-v1.schema.json": {
            "schema_version": 1,
            "kind": "member-result",
            "summary": "Implemented the requested change.",
            "deliverables": ["src/change.py"],
            "risks": [],
        },
        "team-template-v2.schema.json": {
            "schema_version": 2,
            "kind": "team-template",
            "id": "interactive-development",
            "version": 1,
            "summary": "Interactive development team.",
            "members": [
                {
                    "name": "lead",
                    "assistant": {
                        "id": "code-reviewer",
                        "version": 1,
                        "content_hash": H64,
                    },
                }
            ],
            "lead": "lead",
            "handoff": {"required_fields": [], "acks": []},
            "independence": [],
            "preferences": {},
            "workspace_layout": "shared-supplied",
        },
        "interactive-run-request-v1.schema.json": {
            "schema_version": 1,
            "kind": "interactive-run-request",
            "target": {
                "kind": "team-template",
                "id": "interactive-development",
                "version": 1,
                "content_hash": H64,
            },
            "workspace": "fixtures/review-target",
            "goal": "implement the requested change",
        },
        "interactive-run-record-v1.schema.json": {
            "schema_version": 1,
            "kind": "interactive-run-record",
            "run_id": "run-interactive-1",
            "target": {
                "kind": "team-template",
                "id": "interactive-development",
                "version": 1,
                "content_hash": H64,
            },
            "goal": "implement the requested change",
            "done_when": [],
            "workspace": "/workspace",
            "workspace_layout": "shared-supplied",
            "phase": "open",
            "members": [
                {
                    "name": "lead",
                    "assistant": {
                        "id": "code-reviewer",
                        "version": 1,
                        "content_hash": H64,
                    },
                    "origin": "persistent",
                    "visibility": "visible",
                    "session_id": "session-lead-1",
                }
            ],
            "work_items": [],
            "sessions": ["session-lead-1"],
            "turns": [],
            "completion_proposals": [],
            "workspace_reservation": "locks/workspace.json",
            "events": "events.jsonl",
            "initial_checkpoint": {
                "canonical_path": "/workspace",
                "git_status_sha256": H64,
                "tree_sha256": H64,
                "observed_at": "2026-08-25T12:00:00Z",
            },
            "created_at": "2026-08-25T12:00:00Z",
            "updated_at": "2026-08-25T12:00:00Z",
        },
        "member-session-v1.schema.json": {
            "schema_version": 1,
            "kind": "member-session",
            "run_id": "run-interactive-1",
            "session_id": "session-lead-1",
            "member": "lead",
            "generation": 1,
            "provider": "direct-acp",
            "provider_session_ref": "opaque-session-1",
            "status": "open",
            "continuity_verified": True,
            "opened_at": "2026-08-25T12:00:00Z",
        },
        "turn-record-v1.schema.json": {
            "schema_version": 1,
            "kind": "turn-record",
            "run_id": "run-interactive-1",
            "turn_id": "turn-1",
            "member": "lead",
            "session_id": "session-lead-1",
            "generation": 1,
            "prompt_sha256": H64,
            "status": "queued",
            "events": "turns/turn-1/events.jsonl",
            "queued_at": "2026-08-25T12:00:00Z",
        },
        "work-item-v1.schema.json": {
            "schema_version": 1,
            "kind": "work-item",
            "run_id": "run-interactive-1",
            "id": "work-1",
            "subject": "Implement the change",
            "owner": "lead",
            "status": "pending",
        },
        "control-request-v1.schema.json": {
            "schema_version": 1,
            "kind": "control-request",
            "request_id": "control-1",
            "run_id": "run-interactive-1",
            "actor": "user",
            "action": "work.create",
            "work_item": {
                "schema_version": 1,
                "kind": "work-item",
                "run_id": "run-interactive-1",
                "id": "work-1",
                "subject": "Implement the change",
                "owner": "lead",
                "status": "pending",
            },
        },
        "control-receipt-v1.schema.json": {
            "schema_version": 1,
            "kind": "control-receipt",
            "request_id": "control-1",
            "run_id": "run-interactive-1",
            "status": "queued",
            "queued_at": "2026-08-25T12:00:00Z",
        },
        "completion-proposal-v1.schema.json": {
            "schema_version": 1,
            "kind": "completion-proposal",
            "run_id": "run-interactive-1",
            "proposal_id": "proposal-1",
            "proposed_by": "lead",
            "source_turn_id": "turn-1",
            "summary": "The requested change is complete.",
            "criteria": [],
            "work_items": ["work-1"],
            "proposed_at": "2026-08-25T12:00:00Z",
        },
        "run-event-v1.schema.json": {
            "schema_version": 1,
            "kind": "run-event",
            "run_id": "run-interactive-1",
            "sequence": 0,
            "event": "run-opened",
            "occurred_at": "2026-08-25T12:00:00Z",
        },
        "provider-capabilities-v1.schema.json": {
            "schema_version": 1,
            "kind": "provider-capabilities",
            "provider": "direct-acp",
            "version": "0.13.1",
            "persistent_turns": "supported",
            "recovery": "supported",
            "permission_events": "supported",
            "workspace_enforcement": "supported",
            "tool_filtering": "supported",
            "native_spawn_control": "unknown",
            "process_stop_observability": "supported",
            "local_state_deletion": "supported",
            "provider_history_deletion": "unknown",
        },
        "provider-doctor-v1.schema.json": {
            "schema_version": 1,
            "kind": "provider-doctor",
            "provider": "direct-acp",
            "checked_at": "2026-08-25T12:00:00Z",
            "status": "pass",
            "capabilities": {
                "schema_version": 1,
                "kind": "provider-capabilities",
                "provider": "direct-acp",
                "version": "0.13.1",
                "persistent_turns": "supported",
                "recovery": "supported",
                "permission_events": "supported",
                "workspace_enforcement": "supported",
                "tool_filtering": "supported",
                "native_spawn_control": "unknown",
                "process_stop_observability": "supported",
                "local_state_deletion": "supported",
                "provider_history_deletion": "unknown",
            },
            "checks": [],
        },
        "provider-live-attestation-v1.schema.json": {
            "schema_version": 1,
            "kind": "provider-live-attestation",
            "provider": "direct-acp",
            "harness": "claude-code",
            "target_fingerprint": H64,
            "runtime_lock_hash": H64,
            "native_version": "2.1.245",
            "platform": "linux",
            "status": "pass",
            "attempted_prompts": 5,
            "proofs": {
                "context_established": True,
                "strict_post_turn_resume": True,
                "recall": True,
                "reset_isolation": True,
                "new_run_isolation": True,
                "continuity_close": True,
            },
            "evidence": [
                {"run_id": "run-live-1", "manifest_sha256": H64},
                {"run_id": "run-live-2", "manifest_sha256": "b" * 64},
            ],
            "checked_at": "2026-08-25T12:00:00Z",
        },
        "catalog-index-v1.schema.json": {
            "schema_version": 1,
            "kind": "catalog-index",
            "generation": 0,
            "entries": [],
            "updated_at": "2026-08-25T12:00:00Z",
        },
        "bundle-manifest-v1.schema.json": {
            "schema_version": 1,
            "kind": "bundle-manifest",
            "assistant": {"id": "code-reviewer", "version": 1, "package_hash": H64},
            "effective_definition_hash": H64,
            "files": [{"path": "assistant.yaml", "size": 10, "sha256": H64}],
            "created_at": "2026-08-23T12:00:00Z",
        },
        "run-record-v1.schema.json": {
            "schema_version": 1,
            "kind": "run-record",
            "run_id": "run-1",
            "mode": "direct",
            "member": member,
            "timing": {"started_at": "2026-08-23T12:00:00Z"},
            "status": "pending",
        },
        "harness-invocation-v1.schema.json": {
            "schema_version": 1,
            "kind": "harness-invocation",
            "invocation_id": "inv-1",
            "run_id": "run-1",
            "requested": {"harness": "codex"},
            "selection": {"decided_by": "user", "candidates": ["codex"]},
            "effective_definition_hash": H64,
            "target": {"before": H64},
            "command": {
                "argv_redacted": ["codex", "exec", "<PROMPT_FILE>"],
                "launcher": "<CODEX>",
                "launcher_policy": "posix-direct",
                "cwd": "<WORKSPACE>",
            },
            "environment": {"config_home_variable": "CODEX_HOME"},
            "attendance": "attended",
            "auth_mode": "native-subscription",
            "timing": {"started_at": "2026-08-23T12:00:00Z"},
            "status": "pending",
        },
        "ensemble-record-v1.schema.json": {
            "schema_version": 1,
            "kind": "ensemble-record",
            "ensemble_id": "ens-1",
            "run_id": "run-1",
            "legs": ["inv-1"],
            "synthesis": {"instruction_hash": H64},
            "status": "pending",
        },
        "normalized-review-v1.schema.json": {
            "schema_version": 1,
            "kind": "normalized-review",
            "target_sha256": H64,
            "findings": [
                {
                    "id": "f1",
                    "severity": "high",
                    "category": "command-injection",
                    "file": "src/run.ts",
                    "line": 12,
                    "title": "Shell command built from input",
                    "rationale": "User input reaches exec().",
                }
            ],
            "summary": "One high finding.",
            "verdict": "request-changes",
        },
        "synthesis-report-v1.schema.json": {
            "schema_version": 1,
            "kind": "synthesis-report",
            "inputs": ["inv-1"],
            "agreements": [{"title": "Command injection", "sources": ["inv-1:f1"]}],
            "disagreements": [
                {"title": "Boundary read", "asserted_by": ["inv-1"], "not_asserted_by": []}
            ],
            "merged_findings": [
                {
                    "id": "m1",
                    "severity": "high",
                    "category": "command-injection",
                    "file": "src/run.ts",
                    "line": 12,
                    "title": "Shell command built from input",
                    "rationale": "User input reaches exec().",
                    "sources": ["inv-1:f1"],
                }
            ],
        },
    }


def run_record_variant_payloads() -> dict[str, dict[str, Any]]:
    """Valid direct and team variants for union and lifecycle tests."""
    direct = minimal_payloads()["run-record-v1.schema.json"]
    team = {
        "schema_version": 1,
        "kind": "run-record",
        "run_id": "run-team-1",
        "mode": "team",
        "template": {"ref": "examples/teams/development.yaml", "hash": H64},
        "members": [
            {
                "name": name,
                "assistant": {"id": assistant, "version": 1, "package_hash": H64},
                "effective_definition_hash": H64,
                "execution": execution,
                "origin": "persistent",
                "visibility": "visible",
                "selection": {"decided_by": decided_by, "candidates": ["codex"]},
            }
            for name, assistant, execution, decided_by in (
                ("lead", "code-reviewer", {"kind": "invocation", "ref": "inv-lead"}, "assistant"),
                ("implementer", "implementer", None, "team"),
            )
        ],
        "substrate": {"kind": "local", "namespace": None, "snapshot": None},
        "tasks": [
            {
                "id": "plan",
                "subject": "Plan the change",
                "status": "pending",
                "owner": "lead",
                "blocked_by": [],
                "workspace_access": "read-only",
                "substrate_id": None,
            },
            {
                "id": "implement",
                "subject": "Implement the change",
                "status": "blocked",
                "owner": "implementer",
                "blocked_by": ["plan"],
                "workspace_access": "workspace-write",
                "substrate_id": None,
            },
        ],
        "independence": {"declared": "advisory", "achieved": None},
        "events": "events.jsonl",
        "timing": {"started_at": "2026-08-23T12:00:00Z"},
        "status": "pending",
    }
    return {"direct": direct, "team": team}


@pytest.fixture()
def payloads() -> dict[str, dict[str, Any]]:
    return minimal_payloads()


@pytest.fixture()
def run_record_variants() -> dict[str, dict[str, Any]]:
    return run_record_variant_payloads()


# --- render-context builder for adapter tests -------------------------------


def make_render_context(
    harness_value: str, tmp_path: Path, **overrides: object
) -> RenderContext:  # imported lazily
    """A ready RenderContext against the example package and a seeded profile."""
    from agentteam.domain.common import HarnessId
    from agentteam.domain.run import DecidedBy, RequestedV1, SelectionV1
    from agentteam.harness.types import RenderContext
    from agentteam.resolution.archive import build_bundle_manifest, hash_package
    from agentteam.resolution.package import load_package
    from agentteam.resolution.profiles import seed_default_profiles

    repo_root = Path(__file__).resolve().parents[1]
    package_root = repo_root / "examples" / "assistants" / "code-reviewer"
    loaded = load_package(package_root)
    digest = hash_package(package_root)
    from agentteam.domain.bundle import AssistantRefV1

    bundle = build_bundle_manifest(
        assistant=AssistantRefV1(
            id=loaded.definition.id,
            version=loaded.definition.version,
            package_hash=digest.package_hash,
        ),
        digest=digest,
        created_at=NOW,
    )
    from agentteam.domain.profile import HarnessProfileV1, Verification

    profiles = {
        p.harness.value: p.model_copy(
            update={
                "capabilities": [
                    row.model_copy(
                        update={
                            "verification": Verification.VERIFIED,
                            "cli_version": "test-version",
                            "verified_at": NOW,
                        }
                    )
                    for row in p.capabilities
                ]
            }
        )
        for p in seed_default_profiles().profiles
    }
    workspace = tmp_path / "workspace"
    workspace.mkdir(exist_ok=True)
    (workspace / "target.ts").write_text("export const x = 1\n", encoding="utf-8")
    task_file = tmp_path / "task.md"
    task_file.write_text("Review the change in target.ts.\n", encoding="utf-8")
    values: dict[str, object] = {
        "profile": profiles[harness_value],
        "definition": loaded.definition,
        "package_root": package_root,
        "bundle": bundle,
        "selection": SelectionV1(decided_by=DecidedBy.USER, candidates=[]),
        "requested": RequestedV1(harness=HarnessId(harness_value)),
        "task_file": task_file,
        "workspace": workspace,
        "workspace_root": tmp_path / "write" / "workspace",
        "config_root": tmp_path / "write" / "config-home",
        "scratch_dir": tmp_path / "write" / "scratch",
        "parent_env": {"HOME": "/home/u", "PATH": "/usr/bin", "LANG": "C.UTF-8"},
        "platform": "linux",
        "run_id": "run-test",
        "invocation_id": "inv-test",
        "timeout_seconds": 900,
    }
    values.update(overrides)
    if "cli_version" not in overrides:
        selected_profile = HarnessProfileV1.model_validate(values["profile"])
        current_versions: set[str] = set()
        for row in selected_profile.capabilities:
            if (
                row.verification is Verification.VERIFIED
                and row.cli_version is not None
                and row.verified_at is not None
            ):
                current_versions.add(row.cli_version)
        values["cli_version"] = next(iter(current_versions)) if len(current_versions) == 1 else None
    return RenderContext.model_validate(values)


class RenderContextBuilder(Protocol):
    def __call__(
        self, harness_value: str, tmp_path: Path, **overrides: object
    ) -> RenderContext: ...


@pytest.fixture()
def render_context_builder() -> RenderContextBuilder:
    return make_render_context
