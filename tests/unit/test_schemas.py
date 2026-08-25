"""Checked-in versioned JSON Schema contract.

The schemas under `schemas/` are generated from the Pydantic models in
`agentteam.domain` and must reproduce byte-for-byte (after LF normalisation),
stay consumable by non-Python validators, and — for the three vendor-facing
files — stay inside the vendors' structured-output dialect intersection.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from collections.abc import Iterator
from copy import deepcopy
from pathlib import Path
from typing import Any

import jsonschema
import pytest
from pydantic import ValidationError

from agentteam import domain
from agentteam.schema import SCHEMA_FILES, SCHEMA_MODELS, check_all, export_all, write_all

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO_ROOT / "schemas"

PLANNED_FILES = {
    "assistant-definition-v1.schema.json": "assistant-definition",
    "harness-profile-set-v1.schema.json": "harness-profile-set",
    "run-request-v1.schema.json": "run-request",
    "run-record-v1.schema.json": "run-record",
    "bundle-manifest-v1.schema.json": "bundle-manifest",
    "harness-invocation-v1.schema.json": "harness-invocation",
    "ensemble-record-v1.schema.json": "ensemble-record",
    "normalized-review-v1.schema.json": "normalized-review",
    "synthesis-report-v1.schema.json": "synthesis-report",
    "team-template-v1.schema.json": "team-template",
    "team-run-request-v1.schema.json": "team-run-request",
    "member-result-v1.schema.json": "member-result",
    "team-template-v2.schema.json": "team-template",
    "interactive-run-request-v1.schema.json": "interactive-run-request",
    "interactive-run-record-v1.schema.json": "interactive-run-record",
    "member-session-v1.schema.json": "member-session",
    "turn-record-v1.schema.json": "turn-record",
    "work-item-v1.schema.json": "work-item",
    "control-request-v1.schema.json": "control-request",
    "control-receipt-v1.schema.json": "control-receipt",
    "completion-proposal-v1.schema.json": "completion-proposal",
    "run-event-v1.schema.json": "run-event",
    "provider-capabilities-v1.schema.json": "provider-capabilities",
    "provider-doctor-v1.schema.json": "provider-doctor",
    "catalog-index-v1.schema.json": "catalog-index",
}
VENDOR_FACING = {
    "normalized-review-v1.schema.json",
    "synthesis-report-v1.schema.json",
    "member-result-v1.schema.json",
}


def _scrubbed_env() -> dict[str, str]:
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)  # this host exports a Python 3.8 ROS path
    return env


def _load(name: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))
    return data


def _objects(node: Any) -> Iterator[dict[str, Any]]:
    """Yield every object-typed subschema (root, $defs, properties, items, anyOf...)."""
    if isinstance(node, dict):
        if node.get("type") == "object" or "properties" in node:
            yield node
        for key, value in node.items():
            if key in {"enum", "const", "default", "examples"}:
                continue
            yield from _objects(value)
    elif isinstance(node, list):
        for item in node:
            yield from _objects(item)


def _walk(node: Any) -> Iterator[dict[str, Any]]:
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk(item)


def _deref(schema: dict[str, Any], prop: dict[str, Any]) -> dict[str, Any]:
    """Follow a local `$ref` (one level) so enum values can be asserted."""
    ref = prop.get("$ref")
    if ref is None:
        return prop
    assert ref.startswith("#/$defs/"), ref
    target: dict[str, Any] = schema["$defs"][ref.rsplit("/", 1)[-1]]
    return target


def _enum(schema: dict[str, Any], prop: dict[str, Any]) -> list[Any]:
    values: list[Any] = _deref(schema, prop)["enum"]
    return values


def _single_value(prop: dict[str, Any]) -> Any:
    """The fixed value of a const/one-member-enum property."""
    if "const" in prop:
        return prop["const"]
    assert prop.get("enum") and len(prop["enum"]) == 1, prop
    return prop["enum"][0]


def _run_variant(schema: dict[str, Any], mode: str) -> dict[str, Any]:
    ref: str = schema["discriminator"]["mapping"][mode]
    variant: dict[str, Any] = schema["$defs"][ref.rsplit("/", 1)[-1]]
    return variant


# --- file set and reproduction -------------------------------------------------


def test_planned_schema_files_are_registered_and_checked_in() -> None:
    assert set(SCHEMA_FILES) == set(PLANNED_FILES)
    for name in PLANNED_FILES:
        assert (SCHEMA_DIR / name).is_file(), f"missing checked-in schema {name}"


def test_checked_in_schemas_reproduce_from_models() -> None:
    generated = export_all()
    assert set(generated) == set(PLANNED_FILES)
    for name, text in generated.items():
        on_disk = (SCHEMA_DIR / name).read_bytes().decode("utf-8").replace("\r\n", "\n")
        assert on_disk == text, f"{name} is stale: run `python -m agentteam.schema export`"


def test_checked_in_schemas_are_lf_on_disk() -> None:
    for name in PLANNED_FILES:
        raw = (SCHEMA_DIR / name).read_bytes()
        assert b"\r" not in raw, f"{name} contains CR bytes; .gitattributes should force LF"
        assert raw.endswith(b"\n") and not raw.endswith(b"\n\n"), name


def test_generated_text_is_lf_terminated_utf8_json() -> None:
    for name, text in export_all().items():
        assert "\r" not in text, name
        assert text.endswith("\n") and not text.endswith("\n\n"), name
        json.loads(text)


def test_check_all_accepts_a_crlf_checkout(tmp_path: Path) -> None:
    # A Windows checkout without .gitattributes applied must still verify
    # (plan section 6: "compared after LF normalisation").
    for name, text in export_all().items():
        (tmp_path / name).write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
    assert check_all(tmp_path) == []


def test_check_all_detects_missing_stale_content_change_and_orphans(tmp_path: Path) -> None:
    assert check_all(SCHEMA_DIR) == []
    written = write_all(tmp_path)
    assert {p.name for p in written} == set(PLANNED_FILES)
    assert check_all(tmp_path) == []
    # trailing-byte tamper
    victim = tmp_path / "run-request-v1.schema.json"
    victim.write_text(victim.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    # semantic content tamper (changed enum member)
    target = tmp_path / "run-record-v1.schema.json"
    target.write_text(
        target.read_text(encoding="utf-8").replace('"direct"', '"indirect"'), encoding="utf-8"
    )
    # missing file
    (tmp_path / "bundle-manifest-v1.schema.json").unlink()
    # orphan schema file
    (tmp_path / "left-over-v1.schema.json").write_text("{}", encoding="utf-8")
    problems = check_all(tmp_path)
    assert any("run-request-v1.schema.json" in p for p in problems)
    assert any("run-record-v1.schema.json" in p for p in problems)
    assert any("bundle-manifest-v1.schema.json" in p for p in problems)
    assert any("left-over-v1.schema.json" in p and "orphan" in p for p in problems)


def test_check_all_reports_a_missing_directory(tmp_path: Path) -> None:
    problems = check_all(tmp_path / "nowhere")
    assert len(problems) == 1
    assert "not a directory" in problems[0]


def test_schema_module_cli_check_and_export(tmp_path: Path) -> None:
    env_cmd = [sys.executable, "-m", "agentteam.schema"]
    kwargs: dict[str, Any] = {
        "capture_output": True,
        "text": True,
        "check": False,
        "env": _scrubbed_env(),
        "cwd": REPO_ROOT,
    }
    ok = subprocess.run([*env_cmd, "check", "--dir", str(SCHEMA_DIR)], **kwargs)
    assert ok.returncode == 0, ok.stdout + ok.stderr
    out = tmp_path / "out"
    exported = subprocess.run([*env_cmd, "export", "--dir", str(out)], **kwargs)
    assert exported.returncode == 0, exported.stdout + exported.stderr
    assert sorted(p.name for p in out.iterdir()) == sorted(PLANNED_FILES)
    stale = subprocess.run([*env_cmd, "check", "--dir", str(tmp_path / "missing")], **kwargs)
    assert stale.returncode == 1


# --- closed records with a fixed envelope -------------------------------------


@pytest.mark.parametrize("name", sorted(PLANNED_FILES))
def test_every_schema_is_a_closed_object_with_envelope(name: str) -> None:
    schema = _load(name)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    version = 2 if name.endswith("-v2.schema.json") else 1
    assert schema["$id"] == f"urn:agentteam:schema:{PLANNED_FILES[name]}:v{version}"
    roots = (
        [_run_variant(schema, "direct"), _run_variant(schema, "team")]
        if name == "run-record-v1.schema.json"
        else [schema]
    )
    for root in roots:
        assert root["type"] == "object"
        props = root["properties"]
        assert _single_value(props["schema_version"]) == version
        assert _single_value(props["kind"]) == PLANNED_FILES[name]
        assert {"schema_version", "kind"} <= set(root["required"])
    for obj in _objects(schema):
        if "properties" in obj:
            assert obj.get("additionalProperties") is False, (
                f"{name}: open record object {obj.get('title')}"
            )


@pytest.mark.parametrize("name", sorted(PLANNED_FILES))
def test_property_names_are_snake_case(name: str) -> None:
    for obj in _objects(_load(name)):
        for prop in obj.get("properties", {}):
            assert prop == prop.lower() and "-" not in prop and " " not in prop, (name, prop)


@pytest.mark.parametrize("name", sorted(PLANNED_FILES))
def test_no_lookaround_in_any_published_pattern(name: str) -> None:
    # RE2-based validators (Go/Rust) reject look-ahead/behind; the published
    # schemas must be consumable without Python (plan section 6).
    for node in _walk(_load(name)):
        pattern = node.get("pattern")
        if isinstance(pattern, str):
            assert not re.search(r"\(\?[=!<]", pattern), (name, pattern)


@pytest.mark.parametrize("name", sorted(VENDOR_FACING))
def test_vendor_facing_schemas_stay_in_the_dialect_intersection(name: str) -> None:
    text = (SCHEMA_DIR / name).read_text(encoding="utf-8")
    assert '"$ref"' not in text and '"$defs"' not in text, f"{name}: refs must be inlined"
    schema = _load(name)
    for obj in _objects(schema):
        props = obj.get("properties", {})
        assert sorted(obj.get("required", [])) == sorted(props), (name, obj.get("title"))
    for node in _walk(schema):
        assert "default" not in node, (name, node)
        assert "const" not in node, (name, node)  # single-value enums instead
        assert "pattern" not in node and "format" not in node, (name, node)


# --- external validation (plan section 15 "schema parity") ---------------------


@pytest.mark.parametrize("name", sorted(PLANNED_FILES))
def test_schema_is_valid_against_the_2020_12_metaschema(name: str) -> None:
    jsonschema.Draft202012Validator.check_schema(_load(name))


@pytest.mark.parametrize("name", sorted(PLANNED_FILES))
def test_minimal_instance_validates_and_unknown_field_fails(
    name: str, payloads: dict[str, dict[str, Any]]
) -> None:
    payload = payloads[name]
    schema = _load(name)
    validator = jsonschema.Draft202012Validator(schema)
    validator.validate(payload)
    # the model accepts the same payload
    model = SCHEMA_MODELS[name][1]
    instance = model.model_validate(payload)
    # the model's own JSON round-trip also validates against the checked-in file
    validator.validate(json.loads(instance.model_dump_json()))
    # unknown fields fail on both sides
    poisoned = {**payload, "unexpected_field": True}
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(poisoned)
    with pytest.raises(ValidationError):
        model.model_validate(poisoned)


def test_run_record_schema_is_a_closed_mode_discriminated_union(
    run_record_variants: dict[str, dict[str, Any]],
) -> None:
    schema = _load("run-record-v1.schema.json")
    assert schema["discriminator"]["propertyName"] == "mode"
    assert len(schema["oneOf"]) == 2
    direct = _run_variant(schema, "direct")
    team = _run_variant(schema, "team")
    direct_fields = [
        "schema_version",
        "kind",
        "run_id",
        "mode",
        "member",
        "timing",
        "status",
        "failure_reason",
    ]
    assert list(direct["properties"]) == direct_fields
    direct_record = domain.RunRecordV1.model_validate(run_record_variants["direct"])
    assert list(direct_record.model_dump()) == direct_fields
    assert "member" not in team["properties"]
    assert {"template", "members", "substrate", "tasks", "independence", "events"} <= set(
        team["properties"]
    )
    validator = jsonschema.Draft202012Validator(schema)
    for payload in run_record_variants.values():
        validator.validate(payload)
    team_json = json.dumps(run_record_variants["team"])
    parsed_team: object = domain.RunRecordV1.model_validate_json(team_json)
    assert isinstance(parsed_team, domain.TeamRunRecordV1)


def test_run_record_schema_rejects_cross_variant_and_team_shape_negatives(
    run_record_variants: dict[str, dict[str, Any]],
) -> None:
    schema = _load("run-record-v1.schema.json")
    validator = jsonschema.Draft202012Validator(schema)
    direct = run_record_variants["direct"]
    team = run_record_variants["team"]
    invalid = [
        {**direct, "template": {"ref": "x", "hash": "a" * 64}},
        {**team, "member": direct["member"]},
    ]
    one_member = deepcopy(team)
    one_member["members"] = one_member["members"][:1]
    invalid.append(one_member)
    bad_access = deepcopy(team)
    bad_access["tasks"][0]["workspace_access"] = "write-everywhere"
    invalid.append(bad_access)
    missing_access = deepcopy(team)
    del missing_access["tasks"][0]["workspace_access"]
    invalid.append(missing_access)
    bad_status = deepcopy(team)
    bad_status["tasks"][0]["status"] = "timed-out"
    invalid.append(bad_status)
    bad_decider = deepcopy(team)
    bad_decider["members"][0]["selection"]["decided_by"] = "forced"
    invalid.append(bad_decider)
    for payload in invalid:
        with pytest.raises(jsonschema.ValidationError):
            validator.validate(payload)


@pytest.mark.parametrize("status", ["failed", "cancelled", "abandoned"])
def test_run_record_schema_accepts_each_run_only_task_terminal(
    status: str, run_record_variants: dict[str, dict[str, Any]]
) -> None:
    payload = deepcopy(run_record_variants["team"])
    payload["tasks"][0]["status"] = status
    jsonschema.Draft202012Validator(_load("run-record-v1.schema.json")).validate(payload)


def test_reserved_arrays_fail_closed_at_schema_level(payloads: dict[str, dict[str, Any]]) -> None:
    cases = [
        ("team-template-v1.schema.json", "dynamic_members", [{"name": "later"}]),
        ("team-template-v1.schema.json", "constraints", ["must-use-codex"]),
        ("team-run-request-v1.schema.json", "overlay_refs", ["overlay-1"]),
    ]
    for name, field, value in cases:
        payload = {**payloads[name], field: value}
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(_load(name)).validate(payload)


def test_team_run_lifecycle_and_execution_binding_model_rules(
    run_record_variants: dict[str, dict[str, Any]],
) -> None:
    pending = run_record_variants["team"]
    record: object = domain.RunRecordV1.model_validate(pending)
    assert isinstance(record, domain.TeamRunRecordV1)

    terminal_time = {
        "started_at": "2026-08-23T12:00:00Z",
        "finished_at": "2026-08-23T12:01:00Z",
    }
    failed = deepcopy(pending)
    failed.update(status="failed", timing=terminal_time)
    domain.RunRecordV1.model_validate(failed)
    timed_out = deepcopy(failed)
    timed_out["status"] = "timed-out"
    domain.RunRecordV1.model_validate(timed_out)

    cancelled = deepcopy(failed)
    cancelled["status"] = "cancelled"
    cancelled["substrate"]["namespace"] = "space-1"
    cancelled["independence"]["achieved"] = "data-dir"
    domain.RunRecordV1.model_validate(cancelled)

    succeeded = deepcopy(cancelled)
    succeeded["status"] = "succeeded"
    succeeded["substrate"]["snapshot"] = {
        "id": "snapshot-1",
        "path": "coordination/snapshot.json",
        "sha256": "a" * 64,
    }
    succeeded["members"][1]["execution"] = {
        "kind": "invocation",
        "ref": "inv-implementer",
    }
    domain.RunRecordV1.model_validate(succeeded)

    for field in ("namespace", "snapshot"):
        invalid = deepcopy(succeeded)
        invalid["substrate"][field] = None
        if field == "namespace":
            invalid["independence"]["achieved"] = None
        with pytest.raises(ValidationError):
            domain.RunRecordV1.model_validate(invalid)
    null_achieved = deepcopy(succeeded)
    null_achieved["independence"]["achieved"] = None
    with pytest.raises(ValidationError):
        domain.RunRecordV1.model_validate(null_achieved)

    null_execution = deepcopy(succeeded)
    null_execution["members"][0]["execution"] = None
    with pytest.raises(ValidationError, match="every member"):
        domain.RunRecordV1.model_validate(null_execution)

    ensemble = deepcopy(pending)
    ensemble["members"][0]["execution"] = {"kind": "ensemble", "ref": "ens-1"}
    with pytest.raises(ValidationError, match="invocation"):
        domain.RunRecordV1.model_validate(ensemble)

    duplicate = deepcopy(succeeded)
    duplicate["members"][1]["execution"] = duplicate["members"][0]["execution"]
    with pytest.raises(ValidationError, match="unique"):
        domain.RunRecordV1.model_validate(duplicate)


def test_model_and_schema_agree_on_path_slug_and_id_patterns() -> None:
    schema = _load("bundle-manifest-v1.schema.json")
    file_entry = schema["$defs"]["FileEntryV1"]["properties"]
    path_pattern = re.compile(file_entry["path"]["pattern"])
    slug_pattern = re.compile(schema["$defs"]["AssistantRefV1"]["properties"]["id"]["pattern"])
    good_paths = ["a/b/c.md", ".hidden.md", "..foo.md", "persona.md", "skills/code-review/SKILL.md"]
    bad_paths = ["../x", "a/../b", "/abs", "a\\b", "dir/", "a//b", "x\n", ".", "..", "a/."]
    h64 = "a" * 64
    for value in good_paths:
        assert path_pattern.fullmatch(value), value
        domain.BundleManifestV1.model_validate(
            {
                "schema_version": 1,
                "kind": "bundle-manifest",
                "assistant": {"id": "x", "version": 1, "package_hash": h64},
                "effective_definition_hash": h64,
                "files": [{"path": value, "size": 1, "sha256": h64}],
                "created_at": "2026-08-23T12:00:00Z",
            }
        )
    for value in bad_paths:
        assert not path_pattern.fullmatch(value), value
        with pytest.raises(ValidationError):
            domain.BundleManifestV1.model_validate(
                {
                    "schema_version": 1,
                    "kind": "bundle-manifest",
                    "assistant": {"id": "x", "version": 1, "package_hash": h64},
                    "effective_definition_hash": h64,
                    "files": [{"path": value, "size": 1, "sha256": h64}],
                    "created_at": "2026-08-23T12:00:00Z",
                }
            )
    for value in ["code-reviewer", "x", "a-1"]:
        assert slug_pattern.fullmatch(value), value
    for value in ["-x", "x-", "X", "a_b", "a b", "x\n"]:
        assert not slug_pattern.fullmatch(value), value


# --- model behaviour the plan pins down ---------------------------------------


def test_models_reject_unknown_fields(payloads: dict[str, dict[str, Any]]) -> None:
    payload = payloads["normalized-review-v1.schema.json"]
    with pytest.raises(ValidationError):
        domain.NormalizedReviewV1.model_validate({**payload, "extra": True})


def test_member_result_requires_summary_and_explicit_result_lists(
    payloads: dict[str, dict[str, Any]],
) -> None:
    payload = payloads["member-result-v1.schema.json"]
    with pytest.raises(ValidationError, match="non-empty"):
        domain.MemberResultV1.model_validate({**payload, "summary": ""})
    for field in ("deliverables", "risks"):
        missing = dict(payload)
        del missing[field]
        with pytest.raises(ValidationError):
            domain.MemberResultV1.model_validate(missing)


def test_effective_definition_hash_is_computed_state_not_request_input() -> None:
    assert "effective_definition_hash" not in _load("run-request-v1.schema.json")["properties"]
    assert "effective_definition_hash" in _load("bundle-manifest-v1.schema.json")["properties"]
    assert "effective_definition_hash" in _load("harness-invocation-v1.schema.json")["properties"]
    run_record = _load("run-record-v1.schema.json")
    direct = _run_variant(run_record, "direct")
    assert "effective_definition_hash" not in direct["properties"]  # lives on the Member
    assert "effective_definition_hash" in run_record["$defs"]["MemberRecordV1"]["properties"]


def test_overlay_refs_are_reserved_in_request_and_bundle_manifest() -> None:
    for name in ("run-request-v1.schema.json", "bundle-manifest-v1.schema.json"):
        prop = _load(name)["properties"]["overlay_refs"]
        assert prop["type"] == "array", name


def test_run_record_member_is_bound_to_exactly_one_execution() -> None:
    schema = _load("run-record-v1.schema.json")
    member = schema["$defs"]["MemberRecordV1"]["properties"]
    execution = _deref(schema, member["execution"])["properties"]
    assert _enum(schema, execution["kind"]) == ["invocation", "ensemble"]
    assert _single_value(_run_variant(schema, "direct")["properties"]["mode"]) == "direct"


def test_harness_invocation_records_what_section_7_lists() -> None:
    schema = _load("harness-invocation-v1.schema.json")
    props = schema["properties"]
    defs = schema["$defs"]
    assert "attempt" not in props  # attempt identity = invocation_id + retry.attempt
    assert set(defs["TargetHashesV1"]["properties"]) == {"before", "after"}
    assert "target" in props
    assert "harness" in defs["ObservedV1"]["properties"]
    injection = defs["InjectionV1"]["properties"]
    assert {"render", "degraded", "undeliverable_required_parts"} <= set(injection)
    assert _enum(schema, defs["SelectionV1"]["properties"]["decided_by"]) == [
        "user",
        "assistant",
        "team",
        "default",
    ]
    assert _enum(schema, props["attendance"]) == ["attended", "unattended"]
    assert _enum(schema, props["auth_mode"]) == ["native-subscription"]
    assert props["problems"]["type"] == "array"
    assert "problems" not in schema["required"]  # omitted records default to an empty list
    assert _enum(schema, defs["UsageV1"]["properties"]["cost_source"]) == ["vendor", "unavailable"]
    launcher_policies = _enum(schema, defs["CommandV1"]["properties"]["launcher_policy"])
    assert "refused" in launcher_policies
    assert "python-script" in launcher_policies  # deterministic fakes are honest records


def test_harness_identifiers_are_the_three_first_pass_harnesses() -> None:
    schema = _load("run-request-v1.schema.json")
    assert schema["$defs"]["HarnessId"]["enum"] == ["claude-code", "codex", "grok"]


def test_run_request_overrides_use_harness_identifiers() -> None:
    schema = _load("run-request-v1.schema.json")
    override = schema["$defs"]["HarnessOverrideV1"]["properties"]
    assert set(override) == {"harness", "value"}
    assert schema["properties"]["model_overrides"]["type"] == "array"
    assert schema["properties"]["effort_overrides"]["type"] == "array"


def test_normalized_review_shape_matches_plan() -> None:
    schema = _load("normalized-review-v1.schema.json")
    assert set(schema["properties"]) == {
        "schema_version",
        "kind",
        "target_sha256",
        "findings",
        "summary",
        "verdict",
    }
    finding = schema["properties"]["findings"]["items"]["properties"]
    assert set(finding) == {"id", "severity", "category", "file", "line", "title", "rationale"}
    assert finding["severity"]["enum"] == ["critical", "high", "medium", "low", "info"]
    verdicts = ["approve", "request-changes", "reject"]
    assert schema["properties"]["verdict"]["enum"] == verdicts


def test_synthesis_report_shape_matches_plan() -> None:
    schema = _load("synthesis-report-v1.schema.json")
    assert set(schema["properties"]) == {
        "schema_version",
        "kind",
        "inputs",
        "agreements",
        "disagreements",
        "merged_findings",
    }
    agreement = schema["properties"]["agreements"]["items"]["properties"]
    assert set(agreement) == {"title", "sources"}
    disagreement = schema["properties"]["disagreements"]["items"]["properties"]
    assert set(disagreement) == {"title", "asserted_by", "not_asserted_by"}
    merged = schema["properties"]["merged_findings"]["items"]["properties"]
    assert set(merged) == {
        "id",
        "severity",
        "category",
        "file",
        "line",
        "title",
        "rationale",
        "sources",
    }


def test_assistant_definition_never_binds_a_concrete_harness_or_model() -> None:
    schema = _load("assistant-definition-v1.schema.json")
    assert "skills" not in schema["properties"]  # Skills are explicit agent-skill artifacts
    policy = schema["$defs"]["HarnessPolicyV1"]["properties"]
    assert {"preferred", "allowed", "forbidden", "required_capabilities", "model_hints"} <= set(
        policy
    )
    hints = schema["$defs"]["ModelHintsV1"]["properties"]
    assert set(hints) == {"tier", "reasoning"}  # abstract hints only, never a model id
    assert "model" not in schema["properties"]
    assert "provider" not in schema["properties"]


def test_profile_set_records_capability_verification_levels_and_defaults() -> None:
    schema = _load("harness-profile-set-v1.schema.json")
    assert "default_harness" in schema["properties"]
    cap = schema["$defs"]["CapabilityRecordV1"]["properties"]
    assert _enum(schema, cap["verification"]) == ["verified", "observed", "unverified"]
    assert {"cli_version", "verified_at"} <= set(cap)
    profile = schema["$defs"]["HarnessProfileV1"]["properties"]
    assert _enum(schema, profile["auth_mode"]) == ["native-subscription"]
    # api-test remains structurally possible; the M1a runner rejects it
    assert _enum(schema, profile["kind"]) == ["native", "api-test"]
    assert "effort_mappings" in profile
    effort_mapping = schema["$defs"]["EffortMappingV1"]["properties"]
    assert set(effort_mapping) == {"reasoning", "effort"}
