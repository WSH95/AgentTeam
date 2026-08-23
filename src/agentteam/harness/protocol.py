"""The internal harness seam (plan section 9).

Recorded deviation from the plan's sketch: `parse` returns `ParsedLegV1`
(review + schema outcome + usage + observed) rather than the bare
`NormalizedReviewV1` — usage and observed facts can only come out of parsing.
"""

from __future__ import annotations

from typing import Protocol

from agentteam.harness.types import (
    HarnessCapabilityReportV1,
    ParsedLegV1,
    RawInvocationV1,
    RenderContext,
    RenderedInvocationV1,
)


class HarnessAdapter(Protocol):
    async def probe(self, context: object) -> HarnessCapabilityReportV1:
        """Bounded day-one capability probe (G5); not implemented in G3."""
        ...

    def render(self, context: RenderContext) -> RenderedInvocationV1:
        """Pure w.r.t. portable definitions; writes only run-scoped files."""
        ...

    async def invoke(self, rendered: RenderedInvocationV1) -> RawInvocationV1:
        """Delegates to the one shared process runner."""
        ...

    def parse(self, raw: RawInvocationV1) -> ParsedLegV1:
        """Validate vendor output into the normalized review model."""
        ...
