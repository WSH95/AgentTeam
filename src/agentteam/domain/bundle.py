"""`BundleManifestV1` — the resolved definition bundle (plan section 7).

Records the Base package hash, the reserved `overlay_refs`, the computed
`effective_definition_hash` (equal to the Base hash in M1a), and every file the
hash covers so integrity can be re-checked before and after a run.
"""

from __future__ import annotations

import unicodedata
from typing import Literal

from pydantic import AwareDatetime, Field, model_validator

from agentteam.domain.common import (
    NonNegativeInt,
    PositiveInt,
    RecordModel,
    RelPath,
    SchemaVersion,
    Sha256,
    Slug,
)


class AssistantRefV1(RecordModel):
    """Reference to a Base Definition by id, version, and content hash."""

    id: Slug
    version: PositiveInt
    package_hash: Sha256


class FileEntryV1(RecordModel):
    path: RelPath
    size: NonNegativeInt
    sha256: Sha256


class BundleManifestV1(RecordModel):
    schema_version: SchemaVersion
    kind: Literal["bundle-manifest"]
    assistant: AssistantRefV1
    overlay_refs: list[str] = Field(default_factory=list)
    effective_definition_hash: Sha256 = Field(
        description="Computed by AgentTeam; equals assistant.package_hash in M1a."
    )
    files: list[FileEntryV1] = Field(default_factory=list)
    created_at: AwareDatetime

    @model_validator(mode="after")
    def _archive_contract(self) -> BundleManifestV1:
        """V1 archive contract (plan section 7): unique, NFC, code-point-sorted,
        no case-fold collisions. These are model-only invariants a JSON Schema
        cannot express (see schemas/README.md)."""
        paths = [f.path for f in self.files]
        if len(set(paths)) != len(paths):
            raise ValueError("file paths must be unique")
        for path in paths:
            if unicodedata.normalize("NFC", path) != path:
                raise ValueError(f"file path is not NFC-normalised: {path!r}")
        if paths != sorted(paths):
            raise ValueError("file paths must be sorted by code point")
        folded = [p.casefold() for p in paths]
        if len(set(folded)) != len(folded):
            raise ValueError("two file paths differ only by case")
        return self
