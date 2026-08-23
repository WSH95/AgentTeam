"""Checked-in JSON Schema generation and verification (plan sections 6-7).

The nine V1 schemas under `schemas/` are generated from the Pydantic models,
written with `\\n` newlines, and compared after LF normalisation so the files
reproduce identically on every operating system. External consumers need
neither Python nor AgentTeam to read or validate them; invariants a JSON
Schema cannot express are listed in `schemas/README.md`.

The two vendor-facing schemas (normalized review, synthesis report) are
post-processed into the vendors' structured-output dialect intersection:
`$defs`/`$ref` fully inlined, `const` rewritten as single-value `enum`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from agentteam.domain import (
    AssistantDefinitionV1,
    BundleManifestV1,
    EnsembleRecordV1,
    HarnessInvocationV1,
    HarnessProfileSetV1,
    NormalizedReviewV1,
    RunRecordV1,
    RunRequestV1,
    SynthesisReportV1,
)

JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"

# Default directory for `python -m agentteam.schema` - deliberately relative:
# the maintainer tooling runs from the repository root (CI does).
DEFAULT_SCHEMA_DIR = Path("schemas")

# file name -> (kind, model); the kind is the file stem without "-v1".
SCHEMA_MODELS: dict[str, tuple[str, type[BaseModel]]] = {
    "assistant-definition-v1.schema.json": ("assistant-definition", AssistantDefinitionV1),
    "harness-profile-set-v1.schema.json": ("harness-profile-set", HarnessProfileSetV1),
    "run-request-v1.schema.json": ("run-request", RunRequestV1),
    "run-record-v1.schema.json": ("run-record", RunRecordV1),
    "bundle-manifest-v1.schema.json": ("bundle-manifest", BundleManifestV1),
    "harness-invocation-v1.schema.json": ("harness-invocation", HarnessInvocationV1),
    "ensemble-record-v1.schema.json": ("ensemble-record", EnsembleRecordV1),
    "normalized-review-v1.schema.json": ("normalized-review", NormalizedReviewV1),
    "synthesis-report-v1.schema.json": ("synthesis-report", SynthesisReportV1),
}
SCHEMA_FILES: dict[str, type[BaseModel]] = {n: m for n, (_, m) in SCHEMA_MODELS.items()}

# The two files consumed directly by vendor structured-output flags.
VENDOR_FACING = {"normalized-review-v1.schema.json", "synthesis-report-v1.schema.json"}

# JSON Schema keywords whose value is a map of *names* to subschemas, not a
# subschema itself; the const rewrite must not descend into their keys.
_NAMED_SUBSCHEMA_MAPS = {"properties", "$defs", "patternProperties", "definitions"}


def _rewrite_const_as_enum(schema: Any) -> Any:
    """Rewrite `const: x` as `enum: [x]` in schema position only."""
    if isinstance(schema, list):
        return [_rewrite_const_as_enum(item) for item in schema]
    if not isinstance(schema, dict):
        return schema
    out: dict[str, Any] = {}
    for key, value in schema.items():
        if key == "const":
            out["enum"] = [value]
        elif key in _NAMED_SUBSCHEMA_MAPS and isinstance(value, dict):
            out[key] = {name: _rewrite_const_as_enum(sub) for name, sub in value.items()}
        elif key in {"enum", "default", "examples"}:
            out[key] = value
        else:
            out[key] = _rewrite_const_as_enum(value)
    return out


def _inline_refs(node: Any, defs: dict[str, Any]) -> Any:
    """Replace every local `$ref` with the referenced definition, merging any
    sibling keys (pydantic emits e.g. `{"$ref": ..., "description": ...}`)."""
    if isinstance(node, list):
        return [_inline_refs(item, defs) for item in node]
    if not isinstance(node, dict):
        return node
    if "$ref" in node:
        ref = node["$ref"]
        if not isinstance(ref, str) or not ref.startswith("#/$defs/"):
            raise ValueError(f"cannot inline non-local $ref: {ref!r}")
        target = defs[ref.rsplit("/", 1)[-1]]
        merged = {**_inline_refs(target, defs)}
        for key, value in node.items():
            if key != "$ref":
                merged[key] = _inline_refs(value, defs)
        return merged
    return {key: _inline_refs(value, defs) for key, value in node.items()}


def generate(name: str) -> dict[str, Any]:
    """The JSON Schema document for one checked-in file name."""
    kind, model = SCHEMA_MODELS[name]
    body: dict[str, Any] = model.model_json_schema(mode="validation")
    if "$schema" in body or "$id" in body:
        raise ValueError(f"{name}: model body must not supply $schema/$id")
    if name in VENDOR_FACING:
        defs = body.pop("$defs", {})
        body = _inline_refs(body, defs)
        body = _rewrite_const_as_enum(body)
    document: dict[str, Any] = {
        "$schema": JSON_SCHEMA_DIALECT,
        "$id": f"urn:agentteam:schema:{kind}:v1",
    }
    document.update(body)
    return document


def render(name: str) -> str:
    """Canonical text: 2-space indent, UTF-8, LF, one trailing newline."""
    return json.dumps(generate(name), indent=2, ensure_ascii=False) + "\n"


def export_all() -> dict[str, str]:
    return {name: render(name) for name in SCHEMA_MODELS}


def write_all(directory: Path) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, text in export_all().items():
        path = directory / name
        path.write_bytes(text.encode("utf-8"))
        written.append(path)
    return written


def check_all(directory: Path) -> list[str]:
    """One problem line per missing, stale, undecodable, or orphan schema file."""
    if not directory.is_dir():
        return [f"{directory} is not a directory - run from the repository root or pass --dir"]
    problems: list[str] = []
    for name, text in export_all().items():
        path = directory / name
        if not path.is_file():
            problems.append(f"{name}: missing (expected at {path})")
            continue
        try:
            on_disk = path.read_bytes().decode("utf-8").replace("\r\n", "\n")
        except UnicodeDecodeError as error:
            problems.append(f"{name}: not valid UTF-8 ({error})")
            continue
        if on_disk != text:
            problems.append(f"{name}: stale - regenerate with `python -m agentteam.schema export`")
    for path in sorted(directory.glob("*.schema.json")):
        if path.name not in SCHEMA_MODELS:
            problems.append(f"{path.name}: orphan schema file (not generated by any model)")
    return problems


def vendor_schema_min(name: str) -> str:
    """One-line minified text of a vendor-facing schema (argv-safe constant)."""
    if name not in VENDOR_FACING:
        raise ValueError(f"not a vendor-facing schema: {name}")
    return json.dumps(generate(name), separators=(",", ":"), ensure_ascii=False)


__all__ = [
    "DEFAULT_SCHEMA_DIR",
    "SCHEMA_FILES",
    "SCHEMA_MODELS",
    "VENDOR_FACING",
    "check_all",
    "export_all",
    "generate",
    "render",
    "vendor_schema_min",
    "write_all",
]
