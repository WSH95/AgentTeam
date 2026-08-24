"""Vendor-output parsing against reviewed, sanitized fixtures (plan sections 7 and 15).

The successful shapes were reconciled with owner-host G5 captures on 2026-08-24;
identifiers, prompts, markers, commands, reasoning, model names, and usage values
remain synthetic.
"""

from __future__ import annotations

from pathlib import Path

from agentteam.domain.run import CostSource, SchemaOutcome
from agentteam.harness.claude import ClaudeAdapter
from agentteam.harness.codex import CodexAdapter
from agentteam.harness.grok import GrokAdapter
from agentteam.harness.types import RawInvocationV1

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "vendor-output"


def _raw(stdout: bytes = b"", output_file_text: str | None = None) -> RawInvocationV1:
    return RawInvocationV1(
        exit_code=0,
        signal=None,
        stdout=stdout,
        stderr=b"",
        output_file_text=output_file_text,
        timed_out=False,
        duration_ms=5,
    )


def _read(rel: str) -> bytes:
    return (FIXTURES / rel).read_bytes()


# --- Claude -------------------------------------------------------------------


def test_claude_ok() -> None:
    leg = ClaudeAdapter().parse(_raw(stdout=_read("claude/ok.json")))
    assert leg.schema_outcome is SchemaOutcome.VALID
    assert leg.review is not None and leg.review.verdict.value == "request-changes"
    assert leg.review.findings[0].category == "command-injection"
    assert leg.usage.cost_source is CostSource.VENDOR
    assert leg.usage.cost_amount == 0.042 and leg.usage.cost_currency == "USD"
    assert leg.usage.input_tokens == 1200 and leg.usage.output_tokens == 300
    assert leg.observed.model == "claude-fable-5"
    assert leg.problems == []


def test_claude_missing_structured_output() -> None:
    leg = ClaudeAdapter().parse(_raw(stdout=_read("claude/missing-structured-output.json")))
    assert leg.review is None
    assert leg.schema_outcome is SchemaOutcome.MISSING
    assert leg.usage.cost_source is CostSource.VENDOR  # telemetry still parsed


def test_claude_schema_invalid() -> None:
    leg = ClaudeAdapter().parse(_raw(stdout=_read("claude/schema-invalid.json")))
    assert leg.review is None
    assert leg.schema_outcome is SchemaOutcome.INVALID
    assert any("verdict" in p for p in leg.problems)


def test_claude_malformed_stream_never_raises() -> None:
    leg = ClaudeAdapter().parse(_raw(stdout=_read("claude/malformed.txt")))
    assert leg.review is None
    assert leg.schema_outcome is SchemaOutcome.MISSING
    assert leg.usage.cost_source is CostSource.UNAVAILABLE
    assert leg.problems


# --- Codex --------------------------------------------------------------------


def test_codex_prefers_the_output_file_and_reads_turn_usage() -> None:
    leg = CodexAdapter().parse(
        _raw(
            stdout=_read("codex/jsonl-ok.jsonl"),
            output_file_text=(FIXTURES / "codex" / "final-message.json").read_text(),
        )
    )
    assert leg.schema_outcome is SchemaOutcome.VALID
    assert leg.review is not None
    assert leg.usage.input_tokens == 900 and leg.usage.output_tokens == 250
    assert leg.usage.cost_source is CostSource.UNAVAILABLE  # Codex never reports cost
    assert leg.usage.cost_amount is None
    assert leg.problems == []


def test_codex_does_not_promote_the_agent_message_event() -> None:
    leg = CodexAdapter().parse(_raw(stdout=_read("codex/jsonl-ok.jsonl")))
    assert leg.schema_outcome is SchemaOutcome.MISSING
    assert leg.review is None
    assert any("authoritative" in p for p in leg.problems)


def test_codex_no_agent_message_is_a_problem_not_a_crash() -> None:
    leg = CodexAdapter().parse(_raw(stdout=_read("codex/jsonl-no-agent-message.jsonl")))
    assert leg.review is None
    assert leg.schema_outcome is SchemaOutcome.MISSING
    assert any("authoritative" in p for p in leg.problems)


def test_codex_tolerates_noise_lines() -> None:
    leg = CodexAdapter().parse(
        _raw(
            stdout=_read("codex/jsonl-with-noise.jsonl"),
            output_file_text=(FIXTURES / "codex" / "final-message.json").read_text(),
        )
    )
    assert leg.schema_outcome is SchemaOutcome.VALID
    assert any("non-JSON event line" in p for p in leg.problems)


# --- Grok ---------------------------------------------------------------------


def test_grok_structured_output_field_with_cost() -> None:
    leg = GrokAdapter().parse(_raw(stdout=_read("grok/ok-structured-field.json")))
    assert leg.schema_outcome is SchemaOutcome.VALID
    assert leg.usage.cost_source is CostSource.VENDOR
    assert leg.usage.cost_amount == 0.01268905
    assert leg.usage.input_tokens == 7210 and leg.usage.output_tokens == 1893
    assert leg.observed.model == "grok-build"


def test_grok_snake_case_structured_output_field() -> None:
    leg = GrokAdapter().parse(_raw(stdout=_read("grok/ok-structured-field-snake.json")))
    assert leg.schema_outcome is SchemaOutcome.VALID
    assert leg.review is not None
    assert leg.review.findings[0].category == "input-validation"
    assert leg.problems == []


def test_grok_text_as_json_and_cost_absent_under_oauth() -> None:
    leg = GrokAdapter().parse(_raw(stdout=_read("grok/ok-text-as-json-cost-absent.json")))
    assert leg.schema_outcome is SchemaOutcome.VALID
    assert leg.review is not None
    assert leg.usage.cost_source is CostSource.UNAVAILABLE
    assert leg.usage.cost_amount is None


def test_grok_error_object() -> None:
    leg = GrokAdapter().parse(_raw(stdout=_read("grok/error.json")))
    assert leg.review is None
    assert leg.schema_outcome is SchemaOutcome.MISSING
    assert any("no auth" in p for p in leg.problems)


def test_grok_structured_null_error_fails_hard_and_never_reads_text() -> None:
    # The initial G6 cycle (2026-08-24): exit 0, `structuredOutput: null`, an
    # explanatory `structuredOutputError`, and decodable `text` that the
    # probe-verified field channel must not consume. The vendor's error string
    # is preserved on the record for diagnosis (G6.R2).
    raw = _raw(stdout=_read("grok/structured-null-error.json")).model_copy(
        update={"structured_output_channel": "structured-output-field"}
    )
    leg = GrokAdapter().parse(raw)
    assert leg.review is None
    assert leg.schema_outcome is SchemaOutcome.MISSING
    assert any("model did not produce structured output" in p for p in leg.problems)
    assert any("no structured output" in p for p in leg.problems)
    assert leg.usage.input_tokens == 7210 and leg.usage.output_tokens == 1893  # telemetry kept
