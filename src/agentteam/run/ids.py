"""Identifiers minted for runs, legs, synthesis, and ensembles (plan section 7).

Deterministic per request where possible: leg ids derive from the harness so
records and attribution stay readable; only the run id carries entropy. All
ids are lowercase and colon-free so archive paths stay Windows-safe.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from agentteam.domain.common import HarnessId

SYNTHESIS_INVOCATION_ID = "inv-synthesis"
ENSEMBLE_ID = "ens-1"


def new_run_id(now: datetime | None = None) -> str:
    stamp = (now or datetime.now(tz=UTC)).astimezone(UTC).strftime("%Y%m%d-%H%M%S")
    return f"run-{stamp}-{uuid4().hex[:4]}"


def leg_invocation_id(harness: HarnessId) -> str:
    return f"inv-{harness.value}"
