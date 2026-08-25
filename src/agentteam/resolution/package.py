"""Assistant package loading and validation (plan sections 7-8).

`load_package` parses `assistant.yaml`/`assistant.json` into the closed
`AssistantDefinitionV1`. `check_package` verifies every referenced file exists
(and each agent-skill carries a `SKILL.md`); with `strict_content=True` it also
runs the prohibited-content heuristics of `assistant-domain-model.md` section 4
for the classes the definition enables. Heuristic findings are advisory
problems (the CLI exits 2 in strict mode); they never modify the package.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import ValidationError

from agentteam.domain.assistant import (
    ArtifactKind,
    AssistantDefinitionV1,
    ProhibitedContentCheck,
)


class PackageError(ValueError):
    """The package cannot be loaded as a V1 Assistant definition."""


@dataclass(frozen=True)
class LoadedPackage:
    definition: AssistantDefinitionV1
    root: Path


def load_package(root: Path) -> LoadedPackage:
    root = Path(root)
    yaml_path = root / "assistant.yaml"
    json_path = root / "assistant.json"
    if yaml_path.is_file() and json_path.is_file():
        raise PackageError(f"package has both assistant.yaml and assistant.json: {root}")
    path = yaml_path if yaml_path.is_file() else json_path
    if not path.is_file():
        raise PackageError(f"no assistant.yaml (or assistant.json) in {root}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise PackageError(f"{path.name}: not valid YAML/JSON: {error}") from None
    try:
        definition = AssistantDefinitionV1.model_validate(data)
    except ValidationError as error:
        details = "; ".join(
            f"{'.'.join(str(loc) for loc in item['loc'])}: {item['msg']}"
            for item in error.errors(include_url=False)
        )
        raise PackageError(f"{path.name}: {details}") from None
    return LoadedPackage(definition=definition, root=root)


# Prohibited-content heuristics (advisory; shapes from ADM section 4).
_HEURISTICS: dict[ProhibitedContentCheck, re.Pattern[str]] = {
    ProhibitedContentCheck.WORKSPACE_PATHS: re.compile(
        r"(?:^|[\s\"'(=])(?:/(?:home|Users|tmp|var|etc|opt|mnt)/|[A-Za-z]:\\|~/)"
    ),
    ProhibitedContentCheck.BRANCH_NAMES: re.compile(r"refs/heads/|checkpoint-\d|/step_\d"),
    ProhibitedContentCheck.SESSION_IDENTIFIERS: re.compile(
        r"(?i)(?:session|rollout)[^\n]{0,40}[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
        r"|rollout-20\d{2}"
    ),
    ProhibitedContentCheck.SURFACE_TOPOLOGY: re.compile(
        r"(?m)-100\d{6,}|^topic:\s|@[A-Za-z0-9_]+_bot\b"
    ),
    ProhibitedContentCheck.BOUND_HARNESS: re.compile(
        r"(?m)--dangerously-[a-z-]+|^\s*command:\s*\[?\s*(?:claude|codex|grok)\b"
    ),
    ProhibitedContentCheck.SECRETS: re.compile(
        r"\bsk-[A-Za-z0-9_-]{16,}|\bAKIA[0-9A-Z]{16}\b|\bgh[pos]_[A-Za-z0-9]{20,}"
        r"|\bxai-[A-Za-z0-9]{16,}|\bxox[baprs]-[A-Za-z0-9-]{10,}"
        r"|[A-Z0-9_]*(?:API_KEY|TOKEN|SECRET|PASSWORD)[A-Z0-9_]*\s*=\s*\S{8,}"
    ),
    ProhibitedContentCheck.RUNTIME_MEMORY: re.compile(r"\bMEMORY\.md\b|\bmemories/"),
}


def check_prohibited_text(
    source: str,
    text: str,
    *,
    enabled: Iterable[ProhibitedContentCheck] = ProhibitedContentCheck,
) -> list[str]:
    """Run the shared advisory content checks over one labelled text value."""
    selected = set(enabled)
    problems: list[str] = []
    for check, pattern in _HEURISTICS.items():
        if check not in selected:
            continue
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            problems.append(f"{source}:{line}: {check.value}: {match.group(0)[:60]!r}")
    return problems


def _instruction_files(loaded: LoadedPackage) -> list[str]:
    definition = loaded.definition
    files = [definition.persona, definition.principles]
    if definition.methods is not None:
        files.append(definition.methods)
    if definition.evolution is not None and definition.evolution.failure_modes is not None:
        files.append(definition.evolution.failure_modes)
    for artifact in definition.artifacts:
        if artifact.kind is ArtifactKind.AGENT_SKILL:
            files.append(f"{artifact.source.vendored}/SKILL.md")
    return files


def check_package(loaded: LoadedPackage, *, strict_content: bool) -> list[str]:
    """Problems as `path: class: detail` strings; empty means the package checks out."""
    problems: list[str] = []
    definition = loaded.definition
    root = loaded.root

    for rel in [definition.persona, definition.principles]:
        if not (root / rel).is_file():
            problems.append(f"{rel}: missing referenced instruction file")
    if definition.methods is not None and not (root / definition.methods).is_file():
        problems.append(f"{definition.methods}: missing referenced instruction file")
    if definition.evolution is not None and definition.evolution.failure_modes is not None:
        rel = definition.evolution.failure_modes
        if not (root / rel).is_file():
            problems.append(f"{rel}: missing referenced failure-modes file")
    for artifact in definition.artifacts:
        vendored = root / artifact.source.vendored
        if not vendored.exists():
            problems.append(f"{artifact.source.vendored}: missing vendored artifact source")
        elif artifact.kind is ArtifactKind.AGENT_SKILL and not (vendored / "SKILL.md").is_file():
            problems.append(f"{artifact.source.vendored}: agent-skill has no SKILL.md")

    if strict_content:
        for rel in _instruction_files(loaded):
            path = root / rel
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            problems.extend(check_prohibited_text(rel, text, enabled=definition.prohibited_content))
    return problems
