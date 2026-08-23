"""Shared builders: one minimal, valid instance of every V1 record."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

H64 = "a" * 64
NOW = datetime(2026, 8, 23, 12, 0, 0, tzinfo=UTC)


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
