"""Fail-closed intersection policy for provider permission events."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from agentteam.domain.assistant import PermissionsV1
from agentteam.domain.interactive import CapabilityLevel, ProviderCapabilitiesV1
from agentteam.domain.team import WorkspaceAccess
from agentteam.execution.protocol import PermissionOutcome, ProviderEvent


class PermissionClass(StrEnum):
    WORKSPACE_READ = "workspace-read"
    WORKSPACE_WRITE = "workspace-write"
    NETWORK = "network"
    OUTSIDE_WORKSPACE = "outside-workspace"
    NATIVE_SPAWN = "native-spawn"
    FULL_ACCESS = "full-access"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class PermissionDecision:
    classification: PermissionClass
    outcome: PermissionOutcome
    attended_approval_required: bool
    reasons: tuple[str, ...]

    @property
    def allowed(self) -> bool:
        return self.outcome is PermissionOutcome.ALLOW_ONCE


def decide_permission(
    event: ProviderEvent,
    *,
    workspace: Path,
    assistant: PermissionsV1,
    member_access: WorkspaceAccess,
    provider: ProviderCapabilitiesV1,
    attended_approval: bool,
) -> PermissionDecision:
    classification = classify_permission(event, workspace=workspace)
    reasons: list[str] = []
    requires_attended = classification is not PermissionClass.WORKSPACE_READ

    if provider.permission_events is not CapabilityLevel.SUPPORTED:
        reasons.append("provider does not prove permission-event control")
    if (
        classification in {PermissionClass.WORKSPACE_READ, PermissionClass.WORKSPACE_WRITE}
        and provider.workspace_enforcement is not CapabilityLevel.SUPPORTED
    ):
        reasons.append("provider does not prove workspace enforcement")

    if classification is PermissionClass.WORKSPACE_READ:
        pass
    elif classification is PermissionClass.WORKSPACE_WRITE:
        if assistant.filesystem != "read-write-workspace":
            reasons.append("Assistant filesystem ceiling is read-only")
        if member_access is not WorkspaceAccess.WORKSPACE_WRITE:
            reasons.append("Member/work-item ceiling does not grant workspace-write")
        if not attended_approval:
            reasons.append("workspace mutation needs attended user approval")
    elif classification is PermissionClass.NETWORK:
        if assistant.network != "allow":
            reasons.append("Assistant network ceiling denies access")
        reasons.append("run policy has no approved network grant")
    elif classification is PermissionClass.NATIVE_SPAWN:
        if provider.native_spawn_control is not CapabilityLevel.SUPPORTED:
            reasons.append("provider cannot prove native-spawn control")
        reasons.append("run policy has no approved native-spawn grant")
    elif classification is PermissionClass.OUTSIDE_WORKSPACE:
        reasons.append("outside-workspace access is not approved")
    elif classification is PermissionClass.FULL_ACCESS:
        if assistant.shell != "allow":
            reasons.append("Assistant shell ceiling denies access")
        if assistant.network != "allow":
            reasons.append("full-access needs the Assistant network ceiling")
        if member_access is not WorkspaceAccess.WORKSPACE_WRITE:
            reasons.append("full-access needs a workspace-write work-item ceiling")
        if not attended_approval:
            reasons.append("full-access needs attended one-time user approval")
        reasons.append("run policy has no approved full-access grant")
    else:
        reasons.append("tool classification is unknown")

    return PermissionDecision(
        classification=classification,
        outcome=PermissionOutcome.REJECT_ONCE if reasons else PermissionOutcome.ALLOW_ONCE,
        attended_approval_required=requires_attended,
        reasons=tuple(reasons),
    )


def classify_permission(event: ProviderEvent, *, workspace: Path) -> PermissionClass:
    explicit = event.data.get("classification")
    if explicit is not None:
        try:
            classification = PermissionClass(explicit)
        except ValueError:
            return PermissionClass.UNKNOWN
        if classification in {
            PermissionClass.WORKSPACE_READ,
            PermissionClass.WORKSPACE_WRITE,
        }:
            paths = _input_paths(event.data.get("tool_input"))
            if not paths:
                return PermissionClass.UNKNOWN
            if any(not _inside_workspace(path, workspace) for path in paths):
                return PermissionClass.OUTSIDE_WORKSPACE
        return classification

    kind = event.data.get("tool_kind", "").lower().replace("_", "-")
    if kind in {"fetch", "network", "web"}:
        return PermissionClass.NETWORK
    if kind in {"spawn", "delegate", "subagent"}:
        return PermissionClass.NATIVE_SPAWN
    if kind in {"full-access", "admin"}:
        return PermissionClass.FULL_ACCESS
    if kind in {"execute", "terminal", "shell"}:
        return PermissionClass.FULL_ACCESS
    if kind in {"other", ""}:
        return PermissionClass.UNKNOWN

    paths = _input_paths(event.data.get("tool_input"))
    if not paths:
        return PermissionClass.UNKNOWN
    if any(not _inside_workspace(path, workspace) for path in paths):
        return PermissionClass.OUTSIDE_WORKSPACE
    if kind in {"read", "search", "list"}:
        return PermissionClass.WORKSPACE_READ
    if kind in {"edit", "write", "delete", "move", "create"}:
        return PermissionClass.WORKSPACE_WRITE
    return PermissionClass.UNKNOWN


def _input_paths(raw: str | None) -> list[Path]:
    if raw is None:
        return []
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return []
    values: list[str] = []

    def visit(value: Any, key: str | None = None) -> None:
        if isinstance(value, dict):
            for child_key, child in value.items():
                visit(child, str(child_key))
        elif isinstance(value, list):
            for child in value:
                visit(child, key)
        elif (
            isinstance(value, str)
            and key is not None
            and any(token in key.lower() for token in ("path", "file", "directory", "cwd"))
        ):
            values.append(value)

    visit(payload)
    return [Path(value).expanduser() for value in values]


def _inside_workspace(path: Path, workspace: Path) -> bool:
    root = workspace.resolve()
    candidate = path if path.is_absolute() else root / path
    normalized = Path(os.path.abspath(candidate)).resolve(strict=False)
    return normalized == root or root in normalized.parents
