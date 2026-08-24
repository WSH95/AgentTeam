"""The upgraded deterministic fakes: oracle-matching finding sets, per-leg
modes, retry/mutation/semantic fixtures, and label-driven synthesis."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from agentteam.domain.common import HarnessId
from agentteam.domain.review import NormalizedReviewV1, SynthesisReportV1
from agentteam.domain.run import SchemaOutcome
from agentteam.harness import get_adapter
from agentteam.harness.protocol import StructuredExtractor
from agentteam.harness.types import SynthesisRenderV1
from agentteam.resolution.profiles import load_profile_set, resolve_profile_path
from agentteam.run.synthesis import build_synthesis_task, validate_synthesis

Builder = Callable[..., Any]

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_FAKE = REPO_ROOT / "examples" / "profiles" / "ci-fake.yaml"

EXPECTED_SECOND_FINDING = {
    HarnessId.CLAUDE_CODE: ("off-by-one", "src/changelog.ts", 4),
    HarnessId.CODEX: ("input-mutation", "src/notes.ts", 8),
    HarnessId.GROK: ("off-by-one", "src/changelog.ts", 4),
}


def _fake_ctx(
    builder: Builder,
    tmp_path: Path,
    harness: HarnessId,
    env: dict[str, str],
    **overrides: Any,
) -> Any:
    profile_set = load_profile_set(CI_FAKE)
    profile = next(p for p in profile_set.profiles if p.harness is harness)
    executable = resolve_profile_path(CI_FAKE, profile.executable)
    profile = profile.model_copy(update={"executable": str(executable)})
    parent_env = {
        "HOME": str(tmp_path),
        "PATH": "/usr/bin:/bin",
        "LANG": "C.UTF-8",
        **env,
    }
    return builder(harness.value, tmp_path, profile=profile, parent_env=parent_env, **overrides)


@pytest.mark.parametrize("harness", [HarnessId.CLAUDE_CODE, HarnessId.CODEX, HarnessId.GROK])
async def test_ok_finding_sets_cover_injection_plus_one_other(
    render_context_builder: Builder, tmp_path: Path, harness: HarnessId
) -> None:
    ctx = _fake_ctx(render_context_builder, tmp_path, harness, {"FAKE_MODE": "ok"})
    adapter = get_adapter(harness)
    raw = await adapter.invoke(adapter.render(ctx))
    leg = adapter.parse(raw)
    assert leg.review is not None, leg.problems
    first, second = leg.review.findings
    assert first.category == "command-injection"
    assert first.file == "src/publish.ts"
    assert first.line == 5
    category, file, line = EXPECTED_SECOND_FINDING[harness]
    assert (second.category, second.file, second.line) == (category, file, line)
    assert first.severity in ("critical", "high")


async def test_per_leg_mode_overrides_only_its_own_vendor(
    render_context_builder: Builder, tmp_path: Path
) -> None:
    env = {"FAKE_MODE": "ok", "FAKE_MODE_CODEX": "rate-limit"}
    (tmp_path / "codex").mkdir()
    (tmp_path / "claude").mkdir()
    codex_ctx = _fake_ctx(render_context_builder, tmp_path / "codex", HarnessId.CODEX, env)
    codex_adapter = get_adapter(HarnessId.CODEX)
    codex_raw = await codex_adapter.invoke(codex_adapter.render(codex_ctx))
    assert codex_raw.exit_code == 1
    assert b"429" in codex_raw.stderr
    claude_ctx = _fake_ctx(render_context_builder, tmp_path / "claude", HarnessId.CLAUDE_CODE, env)
    claude_adapter = get_adapter(HarnessId.CLAUDE_CODE)
    claude_raw = await claude_adapter.invoke(claude_adapter.render(claude_ctx))
    assert claude_raw.exit_code == 0


async def test_fake_claude_rejects_a_meta_schema_reference_like_the_real_cli(
    render_context_builder: Builder, tmp_path: Path
) -> None:
    # The initial G6 cycle proved Claude 2.1.241 rejects a `--json-schema`
    # document carrying a `$schema` meta-reference before any inference; the
    # fake mirrors that, so a delivery-path regression fails deterministically.
    ctx = _fake_ctx(render_context_builder, tmp_path, HarnessId.CLAUDE_CODE, {"FAKE_MODE": "ok"})
    adapter = get_adapter(HarnessId.CLAUDE_CODE)
    rendered = adapter.render(ctx)
    index = rendered.argv.index("--json-schema") + 1
    unprojected = dict(json.loads(rendered.argv[index]))
    unprojected["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    tampered = rendered.model_copy(
        update={
            "argv": [*rendered.argv[:index], json.dumps(unprojected), *rendered.argv[index + 1 :]]
        }
    )
    raw = await adapter.invoke(tampered)
    assert raw.exit_code == 1
    assert (
        b"--json-schema is not a valid JSON Schema: no schema with key or ref "
        b'"https://json-schema.org/draft/2020-12/schema"' in raw.stderr
    )


async def test_rate_limit_once_fails_then_succeeds_with_a_shared_config_home(
    render_context_builder: Builder, tmp_path: Path
) -> None:
    ctx = _fake_ctx(
        render_context_builder,
        tmp_path,
        HarnessId.CLAUDE_CODE,
        {"FAKE_MODE": "rate-limit-once"},
    )
    adapter = get_adapter(HarnessId.CLAUDE_CODE)
    rendered = adapter.render(ctx)
    first = await adapter.invoke(rendered)
    assert first.exit_code == 1
    assert b"429" in first.stderr
    second = await adapter.invoke(rendered)
    assert second.exit_code == 0
    assert adapter.parse(second).schema_outcome is SchemaOutcome.VALID


async def test_mutate_target_writes_exactly_one_file_into_the_workspace(
    render_context_builder: Builder, tmp_path: Path
) -> None:
    ctx = _fake_ctx(
        render_context_builder, tmp_path, HarnessId.CODEX, {"FAKE_MODE": "mutate-target"}
    )
    adapter = get_adapter(HarnessId.CODEX)
    rendered = adapter.render(ctx)
    before = {p.relative_to(ctx.workspace_root) for p in ctx.workspace_root.rglob("*")}
    raw = await adapter.invoke(rendered)
    assert raw.exit_code == 0
    after = {p.relative_to(ctx.workspace_root) for p in ctx.workspace_root.rglob("*")}
    new_files = after - before
    assert [str(path) for path in new_files] == ["fake-mutation.txt"]
    assert adapter.parse(raw).schema_outcome is SchemaOutcome.VALID


async def test_invent_critical_adds_one_finding_outside_any_oracle(
    render_context_builder: Builder, tmp_path: Path
) -> None:
    ctx = _fake_ctx(
        render_context_builder, tmp_path, HarnessId.CODEX, {"FAKE_MODE": "invent-critical"}
    )
    adapter = get_adapter(HarnessId.CODEX)
    leg = adapter.parse(await adapter.invoke(adapter.render(ctx)))
    assert leg.review is not None
    assert len(leg.review.findings) == 3
    invented = leg.review.findings[-1]
    assert invented.severity == "critical"
    assert invented.file == "src/extra.ts"


async def test_fake_grok_structured_null_mode_reproduces_the_live_failure(
    render_context_builder: Builder, tmp_path: Path
) -> None:
    # Live 1.0.5 shape from the initial G6 cycle: exit 0, camelCase
    # `structuredOutput: null` + `structuredOutputError`, decodable `text`.
    ctx = _fake_ctx(
        render_context_builder, tmp_path, HarnessId.GROK, {"FAKE_MODE": "structured-null"}
    )
    adapter = get_adapter(HarnessId.GROK)
    raw = await adapter.invoke(adapter.render(ctx))
    assert raw.exit_code == 0
    leg = adapter.parse(raw)
    assert leg.review is None
    assert leg.schema_outcome is SchemaOutcome.MISSING
    assert any("model did not produce structured output" in p for p in leg.problems)


async def test_semantic_miss_keeps_only_the_injection_finding(
    render_context_builder: Builder, tmp_path: Path
) -> None:
    ctx = _fake_ctx(
        render_context_builder, tmp_path, HarnessId.GROK, {"FAKE_MODE": "semantic-miss"}
    )
    adapter = get_adapter(HarnessId.GROK)
    leg = adapter.parse(await adapter.invoke(adapter.render(ctx)))
    assert leg.review is not None
    assert [finding.category for finding in leg.review.findings] == ["command-injection"]


def _labelled_reviews(payloads: dict[str, Any]) -> dict[str, NormalizedReviewV1]:
    base = payloads["normalized-review-v1.schema.json"]

    def review(finding_updates: list[dict[str, Any]]) -> NormalizedReviewV1:
        data = dict(base)
        data["findings"] = [dict(base["findings"][0], **update) for update in finding_updates]
        return NormalizedReviewV1.model_validate(data)

    return {
        "inv-claude-code": review([{"id": "c1"}]),
        "inv-codex": review(
            [{"id": "x1"}, {"id": "x2", "category": "input-mutation", "severity": "medium"}]
        ),
    }


@pytest.mark.parametrize("harness", [HarnessId.CLAUDE_CODE, HarnessId.CODEX, HarnessId.GROK])
async def test_synthesis_shaped_invocation_yields_label_derived_report(
    render_context_builder: Builder,
    tmp_path: Path,
    harness: HarnessId,
    payloads: dict[str, Any],
) -> None:
    legs = _labelled_reviews(payloads)
    document = build_synthesis_task(
        [
            ("inv-claude-code", "claude-code", legs["inv-claude-code"]),
            ("inv-codex", "codex", legs["inv-codex"]),
        ]
    )
    task_file = tmp_path / "synthesis-task.md"
    task_file.write_text(document, encoding="utf-8")
    instructions = tmp_path / "instructions.md"
    instructions.write_text("Merge the labelled reviews.\n", encoding="utf-8")
    ctx = _fake_ctx(
        render_context_builder,
        tmp_path,
        harness,
        {"FAKE_MODE": "ok"},
        synthesis=SynthesisRenderV1(instructions_file=instructions),
        task_file=task_file,
        invocation_id="inv-synthesis",
    )
    adapter = get_adapter(harness)
    raw = await adapter.invoke(adapter.render(ctx))
    assert raw.exit_code == 0, raw.stderr
    assert isinstance(adapter, StructuredExtractor)
    extracted = adapter.extract_structured(raw)
    report = SynthesisReportV1.model_validate(extracted.candidate)
    attribution = validate_synthesis(report, legs)
    assert set(report.inputs) == {"inv-claude-code", "inv-codex"}
    agreement_titles = [agreement.sources for agreement in report.agreements]
    assert any(len({s.partition(":")[0] for s in srcs}) == 2 for srcs in agreement_titles)
    assert any(disagreement.asserted_by == ["inv-codex"] for disagreement in report.disagreements)
    assert attribution
