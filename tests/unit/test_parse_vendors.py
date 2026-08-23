"""Vendor-output parsing against hand-authored fixtures (plan sections 7 and 15).

Fixtures are authored from the 2026-08-23 fact sheet / vendor documentation
shapes; after G5 they are updated only by reviewed promotion of sanitized
captures.
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


def test_codex_falls_back_to_the_agent_message_event() -> None:
    leg = CodexAdapter().parse(_raw(stdout=_read("codex/jsonl-ok.jsonl")))
    assert leg.schema_outcome is SchemaOutcome.VALID
    assert leg.review is not None


def test_codex_no_agent_message_is_a_problem_not_a_crash() -> None:
    leg = CodexAdapter().parse(_raw(stdout=_read("codex/jsonl-no-agent-message.jsonl")))
    assert leg.review is None
    assert leg.schema_outcome is SchemaOutcome.MISSING
    assert any("agent_message" in p for p in leg.problems)


def test_codex_tolerates_noise_lines() -> None:
    leg = CodexAdapter().parse(_raw(stdout=_read("codex/jsonl-with-noise.jsonl")))
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
