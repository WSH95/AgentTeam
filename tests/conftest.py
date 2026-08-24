"""Shared builders: one minimal, valid instance of every V1 record."""

from __future__ import annotations

import shutil
import sys
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

import pytest

if TYPE_CHECKING:
    from agentteam.harness.types import RenderContext

H64 = "a" * 64
NOW = datetime(2026, 8, 23, 12, 0, 0, tzinfo=UTC)


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


@pytest.fixture()
def payloads() -> dict[str, dict[str, Any]]:
    return minimal_payloads()


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
