"""Shared vendor-output parsing helpers (plan section 7; fact sheet 2026-08-23).

Cost is never fabricated: `cost_source` becomes `vendor` only when the vendor
reported a cost value (with currency USD); Codex has no cost channel at all.
"""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from agentteam.domain.review import NormalizedReviewV1
from agentteam.domain.run import CostSource, ObservedV1, SchemaOutcome, UsageV1


def review_from_object(
    payload: Any,
) -> tuple[NormalizedReviewV1 | None, SchemaOutcome, list[str]]:
    """Validate a candidate structured-output object into the review model."""
    if payload is None:
        return None, SchemaOutcome.MISSING, ["no structured output in the vendor result"]
    try:
        return NormalizedReviewV1.model_validate(payload), SchemaOutcome.VALID, []
    except ValidationError as error:
        details = "; ".join(
            f"{'.'.join(str(loc) for loc in item['loc'])}: {item['msg']}"
            for item in error.errors(include_url=False)[:5]
        )
        return None, SchemaOutcome.INVALID, [f"structured output failed validation: {details}"]


def tokens_from_model_usage(model_usage: Any) -> tuple[UsageV1, ObservedV1]:
    """Claude/Grok `modelUsage`: totals per model; the model name is observed."""
    if not isinstance(model_usage, dict) or not model_usage:
        return UsageV1(), ObservedV1()
    input_tokens = 0
    output_tokens = 0
    observed_model: str | None = None
    for model_name, stats in model_usage.items():
        observed_model = observed_model or str(model_name)
        if isinstance(stats, dict):
            input_tokens += int(stats.get("inputTokens", 0) or 0)
            output_tokens += int(stats.get("outputTokens", 0) or 0)
    return (
        UsageV1(input_tokens=input_tokens, output_tokens=output_tokens),
        ObservedV1(model=observed_model),
    )


def cost_from_total_usd(usage: UsageV1, total_cost_usd: Any) -> UsageV1:
    """Attach a vendor-reported USD cost when (and only when) it exists."""
    if isinstance(total_cost_usd, int | float):
        return usage.model_copy(
            update={
                "cost_amount": float(total_cost_usd),
                "cost_currency": "USD",
                "cost_source": CostSource.VENDOR,
            }
        )
    return usage
