"""Shared building blocks for versioned AgentTeam records.

Every persistent record is a closed object (`additionalProperties: false`),
carries a fixed `(kind, schema_version)` identity, and serialises to snake_case
JSON. Unknown fields fail validation.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

SCHEMA_VERSION = 1
SchemaVersion = Literal[1]
SchemaVersionV2 = Literal[2]


class RecordModel(BaseModel):
    """Base for every AgentTeam record: closed, strict, snake_case.

    Every pattern below is look-around-free so the published JSON Schemas
    compile under RE2-based validators (Go/Rust) as well as ECMA-262 and
    Python `re`; pydantic-core's default Rust engine treats `$` as strict
    end-of-text, closing the trailing-newline hole Python `re` would leave.
    """

    model_config = ConfigDict(extra="forbid")


class HarnessId(StrEnum):
    """Harness identifiers used in records and profiles (plan section 2)."""

    CLAUDE_CODE = "claude-code"
    CODEX = "codex"
    GROK = "grok"


# A lowercase identifier: 1-64 chars of [a-z0-9-], no leading/trailing hyphen.
Slug = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$"),
]

# One path segment: not `.` or `..`, no `/`, `\`, or control characters.
# Alternatives: starts with a non-dot; `.` + non-dot tail; `..` + non-empty tail.
_SEGMENT = (
    r"(?:[^./\\\x00-\x1f\x7f][^/\\\x00-\x1f\x7f]*"
    r"|\.[^./\\\x00-\x1f\x7f][^/\\\x00-\x1f\x7f]*"
    r"|\.\.[^/\\\x00-\x1f\x7f]+)"
)

# A path relative to a package/archive root: `/`-separated, no `.`/`..`
# segments, no leading/trailing/double `/`, no backslash, no control
# characters (V1 archive contract, plan section 7). NFC normalisation,
# case-fold-collision rejection, and code-point ordering are manifest-level
# model validators (see BundleManifestV1 and schemas/README.md).
RelPath = Annotated[
    str,
    StringConstraints(pattern=rf"^{_SEGMENT}(?:/{_SEGMENT})*$", min_length=1, max_length=1024),
]

# SHA-256 digest as 64 lowercase hex characters.
Sha256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]

# Identifiers minted by AgentTeam for runs, ensembles, and invocations:
# prefixed, lowercase, hyphen-separated, no trailing hyphen, bounded length.
_ID_BODY = r"[0-9a-z](?:[0-9a-z-]{0,78}[0-9a-z])?"
RunId = Annotated[str, StringConstraints(pattern=rf"^run-{_ID_BODY}$")]
EnsembleId = Annotated[str, StringConstraints(pattern=rf"^ens-{_ID_BODY}$")]
InvocationId = Annotated[str, StringConstraints(pattern=rf"^inv-{_ID_BODY}$")]

NonNegativeInt = Annotated[int, Field(ge=0)]
PositiveInt = Annotated[int, Field(ge=1)]


class RunStatus(StrEnum):
    """Lifecycle status; a record is created `pending` before the first side effect."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed-out"


TERMINAL_STATUSES = frozenset(
    {RunStatus.SUCCEEDED, RunStatus.FAILED, RunStatus.CANCELLED, RunStatus.TIMED_OUT}
)
