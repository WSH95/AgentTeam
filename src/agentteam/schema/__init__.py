"""Checked-in JSON Schema registry, generation, and verification.

Schemas under `schemas/` are generated from the Pydantic models,
written with `\\n` newlines, and compared after LF normalisation so the files
reproduce identically on every operating system. External consumers need
neither Python nor AgentTeam to read or validate them; invariants a JSON
Schema cannot express are listed in `schemas/README.md`.

The three vendor-facing schemas (normalized review, synthesis report, member result) are
post-processed into the vendors' structured-output dialect intersection:
`$defs`/`$ref` fully inlined, `const` rewritten as single-value `enum`.
The checked-in documents keep the `$schema`/`$id` envelope; the documents
actually delivered to vendor flags are additionally projected through
`vendor_projection` (no meta-schema reference, no `title` annotations) —
Claude's CLI rejects a `$schema` it cannot resolve (observed live 2026-08-24).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from agentteam.domain import (
    AssistantDefinitionV1,
    BundleManifestV1,
    CatalogIndexV1,
    CompletionProposalV1,
    ControlReceiptV1,
    ControlRequestV1,
    EnsembleRecordV1,
    HarnessInvocationV1,
    HarnessProfileSetV1,
    InteractiveRunRecordV1,
    InteractiveRunRequestV1,
    MemberResultV1,
    MemberSessionV1,
    NormalizedReviewV1,
    ProviderCapabilitiesV1,
    ProviderDoctorV1,
    ProviderLiveAttestationV1,
    RunEventV1,
    RunRecordV1,
    RunRequestV1,
    SynthesisReportV1,
    TeamRunRequestV1,
    TeamTemplateV1,
    TeamTemplateV2,
    TurnRecordV1,
    WorkItemV1,
)
from agentteam.domain.run import run_record_json_schema

JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"

# Default directory for `python -m agentteam.schema` - deliberately relative:
# the maintainer tooling runs from the repository root (CI does).
DEFAULT_SCHEMA_DIR = Path("schemas")

# file name -> (kind, schema version, model). The separate registry is the
# runtime authority; filenames are an export concern only.
SCHEMA_ENTRIES: dict[str, tuple[str, int, type[BaseModel]]] = {
    "assistant-definition-v1.schema.json": ("assistant-definition", 1, AssistantDefinitionV1),
    "harness-profile-set-v1.schema.json": ("harness-profile-set", 1, HarnessProfileSetV1),
    "run-request-v1.schema.json": ("run-request", 1, RunRequestV1),
    "run-record-v1.schema.json": ("run-record", 1, RunRecordV1),
    "bundle-manifest-v1.schema.json": ("bundle-manifest", 1, BundleManifestV1),
    "harness-invocation-v1.schema.json": ("harness-invocation", 1, HarnessInvocationV1),
    "ensemble-record-v1.schema.json": ("ensemble-record", 1, EnsembleRecordV1),
    "normalized-review-v1.schema.json": ("normalized-review", 1, NormalizedReviewV1),
    "synthesis-report-v1.schema.json": ("synthesis-report", 1, SynthesisReportV1),
    "team-template-v1.schema.json": ("team-template", 1, TeamTemplateV1),
    "team-run-request-v1.schema.json": ("team-run-request", 1, TeamRunRequestV1),
    "member-result-v1.schema.json": ("member-result", 1, MemberResultV1),
    "team-template-v2.schema.json": ("team-template", 2, TeamTemplateV2),
    "interactive-run-request-v1.schema.json": (
        "interactive-run-request",
        1,
        InteractiveRunRequestV1,
    ),
    "interactive-run-record-v1.schema.json": (
        "interactive-run-record",
        1,
        InteractiveRunRecordV1,
    ),
    "member-session-v1.schema.json": ("member-session", 1, MemberSessionV1),
    "turn-record-v1.schema.json": ("turn-record", 1, TurnRecordV1),
    "work-item-v1.schema.json": ("work-item", 1, WorkItemV1),
    "control-request-v1.schema.json": ("control-request", 1, ControlRequestV1),
    "control-receipt-v1.schema.json": ("control-receipt", 1, ControlReceiptV1),
    "completion-proposal-v1.schema.json": (
        "completion-proposal",
        1,
        CompletionProposalV1,
    ),
    "run-event-v1.schema.json": ("run-event", 1, RunEventV1),
    "provider-capabilities-v1.schema.json": (
        "provider-capabilities",
        1,
        ProviderCapabilitiesV1,
    ),
    "provider-doctor-v1.schema.json": ("provider-doctor", 1, ProviderDoctorV1),
    "provider-live-attestation-v1.schema.json": (
        "provider-live-attestation",
        1,
        ProviderLiveAttestationV1,
    ),
    "catalog-index-v1.schema.json": ("catalog-index", 1, CatalogIndexV1),
}

# Kept as a public compatibility view used by existing schema tooling/tests.
SCHEMA_MODELS: dict[str, tuple[str, type[BaseModel]]] = {
    name: (kind, model) for name, (kind, _version, model) in SCHEMA_ENTRIES.items()
}
SCHEMA_FILES: dict[str, type[BaseModel]] = {n: m for n, (_, m) in SCHEMA_MODELS.items()}
SCHEMA_REGISTRY: dict[tuple[str, int], type[BaseModel]] = {
    (kind, version): model for kind, version, model in SCHEMA_ENTRIES.values()
}
if len(SCHEMA_REGISTRY) != len(SCHEMA_ENTRIES):
    raise RuntimeError("duplicate (kind, schema_version) registration")

# The three files consumed directly by vendor structured-output flags.
VENDOR_FACING = {
    "normalized-review-v1.schema.json",
    "synthesis-report-v1.schema.json",
    "member-result-v1.schema.json",
}

# JSON Schema keywords whose value is a map of *names* to subschemas, not a
# subschema itself; schema-position traversals must not treat their keys as
# schema keywords.
_NAMED_SUBSCHEMA_MAPS = {"properties", "$defs", "patternProperties", "definitions"}

# Keywords whose values are data, not subschemas; traversals copy them
# verbatim (a `required` list may name a property called `title`). Shared by
# the const rewrite and the vendor projection so the two walks cannot drift.
_SCHEMA_DATA_KEYS = frozenset({"enum", "required", "default", "examples"})


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
        elif key in _SCHEMA_DATA_KEYS:
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
    kind, version, model = SCHEMA_ENTRIES[name]
    body: dict[str, Any] = (
        run_record_json_schema()
        if name == "run-record-v1.schema.json"
        else model.model_json_schema(mode="validation")
    )
    if "$schema" in body or "$id" in body:
        raise ValueError(f"{name}: model body must not supply $schema/$id")
    if name in VENDOR_FACING:
        defs = body.pop("$defs", {})
        body = _inline_refs(body, defs)
        body = _rewrite_const_as_enum(body)
    document: dict[str, Any] = {
        "$schema": JSON_SCHEMA_DIALECT,
        "$id": f"urn:agentteam:schema:{kind}:v{version}",
    }
    document.update(body)
    return document


def render(name: str) -> str:
    """Canonical text: 2-space indent, UTF-8, LF, one trailing newline."""
    return json.dumps(generate(name), indent=2, ensure_ascii=False) + "\n"


def export_all() -> dict[str, str]:
    return {name: render(name) for name in SCHEMA_MODELS}


def record_model(kind: str, schema_version: int) -> type[BaseModel]:
    """Resolve a persistent record model by its full schema identity."""
    try:
        return SCHEMA_REGISTRY[(kind, schema_version)]
    except KeyError:
        raise ValueError(
            f"unsupported schema identity: kind={kind!r}, schema_version={schema_version!r}"
        ) from None


def validate_record(payload: Any) -> BaseModel:
    """Validate an untrusted mapping after closed kind/version dispatch."""
    if not isinstance(payload, dict):
        raise ValueError("record must be an object")
    kind = payload.get("kind")
    version = payload.get("schema_version")
    if not isinstance(kind, str) or not isinstance(version, int) or isinstance(version, bool):
        raise ValueError("record requires string kind and integer schema_version")
    return record_model(kind, version).model_validate(payload)


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


# Keys stripped from vendor-delivered documents, in schema position only:
# the meta-schema reference and identity envelope (Claude's CLI fails on an
# unresolvable `$schema`) and pure `title` annotations. The checked-in
# canonical documents keep all three.
VENDOR_STRIP_KEYS = frozenset({"$schema", "$id", "title"})


def vendor_projection(schema: Any) -> Any:
    """A copy with `VENDOR_STRIP_KEYS` removed in schema position only.

    Keys of named-subschema maps (e.g. a *property* called `title`) and the
    values of data keywords (`enum`, `required`, `default`, `examples`) pass
    through verbatim. `$defs`/`$ref` inlining and the `const` rewrite already
    happen at canonical generation time.
    """
    if isinstance(schema, list):
        return [vendor_projection(item) for item in schema]
    if not isinstance(schema, dict):
        return schema
    out: dict[str, Any] = {}
    for key, value in schema.items():
        if key in VENDOR_STRIP_KEYS:
            continue
        if key in _NAMED_SUBSCHEMA_MAPS and isinstance(value, dict):
            out[key] = {name: vendor_projection(sub) for name, sub in value.items()}
        elif key in _SCHEMA_DATA_KEYS:
            out[key] = value
        else:
            out[key] = vendor_projection(value)
    return out


def vendor_schema(name: str) -> dict[str, Any]:
    """The vendor-delivered projection of one vendor-facing schema."""
    if name not in VENDOR_FACING:
        raise ValueError(f"not a vendor-facing schema: {name}")
    projected: dict[str, Any] = vendor_projection(generate(name))
    return projected


def vendor_schema_min(name: str) -> str:
    """One-line minified vendor projection (argv-safe constant)."""
    return json.dumps(vendor_schema(name), separators=(",", ":"), ensure_ascii=False)


def vendor_schema_text(name: str) -> str:
    """Pretty vendor projection for file-channel delivery (Codex)."""
    return json.dumps(vendor_schema(name), indent=2, ensure_ascii=False) + "\n"


__all__ = [
    "DEFAULT_SCHEMA_DIR",
    "SCHEMA_ENTRIES",
    "SCHEMA_FILES",
    "SCHEMA_MODELS",
    "SCHEMA_REGISTRY",
    "VENDOR_FACING",
    "VENDOR_STRIP_KEYS",
    "check_all",
    "export_all",
    "generate",
    "record_model",
    "render",
    "validate_record",
    "vendor_projection",
    "vendor_schema",
    "vendor_schema_min",
    "vendor_schema_text",
    "write_all",
]
