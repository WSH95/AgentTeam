"""`extract_structured` — the vendor-specific candidate extraction that `parse`
now shares (plan section 12 step 12: synthesis validates a different schema
over the same extraction)."""

from __future__ import annotations

from pathlib import Path

from agentteam.domain.review import NormalizedReviewV1
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
        duration_ms=1,
    )


def test_claude_extraction_matches_parse() -> None:
    raw = _raw(stdout=(FIXTURES / "claude" / "ok.json").read_bytes())
    adapter = ClaudeAdapter()
    extracted = adapter.extract_structured(raw)
    parsed = adapter.parse(raw)
    assert parsed.review is not None
    assert NormalizedReviewV1.model_validate(extracted.candidate) == parsed.review
    assert extracted.usage == parsed.usage
    assert extracted.observed == parsed.observed
    assert extracted.hard_failure is False


def test_claude_non_json_stdout_is_a_hard_failure() -> None:
    raw = _raw(stdout=(FIXTURES / "claude" / "malformed.txt").read_bytes())
    extracted = ClaudeAdapter().extract_structured(raw)
    assert extracted.hard_failure is True
    assert extracted.candidate is None
    assert any("not JSON" in problem for problem in extracted.problems)


def test_codex_extraction_prefers_the_output_file() -> None:
    adapter = CodexAdapter()
    raw = _raw(
        stdout=(FIXTURES / "codex" / "jsonl-ok.jsonl").read_bytes(),
        output_file_text=(FIXTURES / "codex" / "final-message.json").read_text(encoding="utf-8"),
    )
    extracted = adapter.extract_structured(raw)
    parsed = adapter.parse(raw)
    assert parsed.review is not None
    assert NormalizedReviewV1.model_validate(extracted.candidate) == parsed.review
    assert extracted.usage == parsed.usage
    assert extracted.hard_failure is False


def test_codex_requires_the_authoritative_output_file() -> None:
    adapter = CodexAdapter()
    raw = _raw(stdout=(FIXTURES / "codex" / "jsonl-ok.jsonl").read_bytes())
    extracted = adapter.extract_structured(raw)
    assert extracted.candidate is None
    assert extracted.hard_failure is False
    assert any("authoritative" in problem for problem in extracted.problems)


def test_codex_reports_jsonl_agreement_and_disagreement_as_telemetry() -> None:
    adapter = CodexAdapter()
    stdout = (FIXTURES / "codex" / "jsonl-ok.jsonl").read_bytes()
    final = (FIXTURES / "codex" / "final-message.json").read_text(encoding="utf-8")
    agreement = adapter.extract_structured(_raw(stdout=stdout, output_file_text=final))
    assert any("agrees" in problem for problem in agreement.problems)
    altered = final.replace("One critical finding.", "Authoritative file wins.")
    disagreement = adapter.extract_structured(_raw(stdout=stdout, output_file_text=altered))
    assert disagreement.candidate is not None
    assert disagreement.candidate["summary"] == "Authoritative file wins."
    assert any("disagrees" in problem for problem in disagreement.problems)


def test_grok_reads_only_the_probe_selected_output_location() -> None:
    adapter = GrokAdapter()
    field_stdout = (FIXTURES / "grok" / "ok-structured-field.json").read_bytes()
    field = _raw(stdout=field_stdout).model_copy(
        update={"structured_output_channel": "structured-output-field"}
    )
    assert adapter.extract_structured(field).candidate is not None
    text_only = field.model_copy(update={"structured_output_channel": "structured-output-text"})
    assert adapter.extract_structured(text_only).candidate is None

    text_stdout = (FIXTURES / "grok" / "ok-text-as-json-cost-absent.json").read_bytes()
    text = _raw(stdout=text_stdout).model_copy(
        update={"structured_output_channel": "structured-output-text"}
    )
    assert adapter.extract_structured(text).candidate is not None


def test_grok_extraction_matches_parse_and_flags_vendor_errors() -> None:
    adapter = GrokAdapter()
    raw = _raw(stdout=(FIXTURES / "grok" / "ok-structured-field.json").read_bytes())
    extracted = adapter.extract_structured(raw)
    parsed = adapter.parse(raw)
    assert parsed.review is not None
    assert NormalizedReviewV1.model_validate(extracted.candidate) == parsed.review
    assert extracted.usage == parsed.usage
    error_raw = _raw(stdout=(FIXTURES / "grok" / "error.json").read_bytes())
    error_extracted = adapter.extract_structured(error_raw)
    assert error_extracted.hard_failure is True
    assert any("vendor error" in problem for problem in error_extracted.problems)
