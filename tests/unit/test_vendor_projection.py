"""Vendor-delivery schema projection (PLAN G6.R1/R2).

The canonical checked-in documents keep their `$schema`/`$id` envelope; the
documents delivered to vendor structured-output flags are projected further
into the probe-proven dialect intersection — no meta-schema reference for a
vendor CLI to resolve (the initial G6 Claude failure), no `title` annotation
noise, and no change to validation semantics.
"""

from __future__ import annotations

import copy
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import jsonschema
import pytest

from agentteam.schema import (
    _NAMED_SUBSCHEMA_MAPS,
    _SCHEMA_DATA_KEYS,
    VENDOR_FACING,
    check_all,
    generate,
    vendor_schema_min,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _subschemas(node: Any) -> Iterator[dict[str, Any]]:
    """Every dict in schema position (never key maps or data lists)."""
    if isinstance(node, list):
        for item in node:
            yield from _subschemas(item)
        return
    if not isinstance(node, dict):
        return
    yield node
    for key, value in node.items():
        if key in _SCHEMA_DATA_KEYS:
            continue
        if key in _NAMED_SUBSCHEMA_MAPS and isinstance(value, dict):
            for sub in value.values():
                yield from _subschemas(sub)
        else:
            yield from _subschemas(value)


@pytest.mark.parametrize("name", sorted(VENDOR_FACING))
def test_vendor_delivered_schemas_carry_no_metadata_or_titles(name: str) -> None:
    document = json.loads(vendor_schema_min(name))
    for sub in _subschemas(document):
        assert "$schema" not in sub, name
        assert "$id" not in sub, name
        assert "title" not in sub, (name, sorted(sub))


def test_projection_preserves_title_named_properties_and_required_lists() -> None:
    # Both vendor-facing shapes have a *property named* `title`; the strip
    # must act in schema position only and never edit `required` data lists.
    from agentteam.schema import vendor_schema

    review = vendor_schema("normalized-review-v1.schema.json")
    finding = review["properties"]["findings"]["items"]
    assert "title" in finding["properties"]
    assert "title" in finding["required"]
    synthesis = vendor_schema("synthesis-report-v1.schema.json")
    for group in ("agreements", "disagreements", "merged_findings"):
        items = synthesis["properties"][group]["items"]
        assert "title" in items["properties"], group
        assert "title" in items["required"], group


@pytest.mark.parametrize("name", sorted(VENDOR_FACING))
def test_projection_is_pure_and_canonical_files_stay_stable(name: str) -> None:
    from agentteam.schema import vendor_projection

    document = generate(name)
    snapshot = copy.deepcopy(document)
    projected = vendor_projection(document)
    assert document == snapshot  # the canonical document is never mutated
    assert projected != snapshot  # the strip actually removed the envelope
    assert check_all(REPO_ROOT / "schemas") == []


@pytest.mark.parametrize("name", sorted(VENDOR_FACING))
def test_projected_schemas_validate_the_same_instances(
    name: str, payloads: dict[str, dict[str, Any]]
) -> None:
    from agentteam.schema import vendor_schema

    validator = jsonschema.Draft202012Validator(vendor_schema(name))
    validator.validate(payloads[name])
    with pytest.raises(jsonschema.ValidationError):
        validator.validate({**payloads[name], "unexpected_field": True})


@pytest.mark.parametrize("name", sorted(VENDOR_FACING))
def test_vendor_schema_min_and_text_render_the_projected_document(name: str) -> None:
    from agentteam.schema import vendor_schema, vendor_schema_text

    minified = vendor_schema_min(name)
    assert "\n" not in minified
    assert json.loads(minified) == vendor_schema(name)
    text = vendor_schema_text(name)
    assert text.endswith("\n") and not text.endswith("\n\n")
    assert json.loads(text) == vendor_schema(name)


@pytest.mark.parametrize("name", sorted(VENDOR_FACING))
def test_delivered_construct_set_is_probe_proven_plus_documented_residue(name: str) -> None:
    # G6.R2 diagnosis of record: the G5 probes proved every vendor's
    # structured output on exactly {type, properties, items, required,
    # additionalProperties}. The delivered full shapes add only the
    # semantically required residue {enum, anyOf, description}; anything else
    # must arrive as a named, reviewed decision, never keyword creep.
    from agentteam.schema import VENDOR_STRIP_KEYS, vendor_schema

    keywords: set[str] = set()
    for sub in _subschemas(vendor_schema(name)):
        keywords.update(sub)
    probe_proven = {"type", "properties", "items", "required", "additionalProperties"}
    residue = {"enum", "anyOf", "description"}
    assert keywords == probe_proven | residue, sorted(keywords)
    assert not (keywords & VENDOR_STRIP_KEYS)


def test_vendor_functions_reject_non_vendor_names() -> None:
    from agentteam.schema import vendor_schema, vendor_schema_text

    for reject in (vendor_schema_min, vendor_schema, vendor_schema_text):
        with pytest.raises(ValueError, match="not a vendor-facing schema"):
            reject("run-request-v1.schema.json")
