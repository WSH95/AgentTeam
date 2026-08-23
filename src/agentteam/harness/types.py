"""Internal harness models (plan section 9). Never exported as checked-in schemas.

These are working objects between render, invoke, and parse; the persistent
contracts stay the nine V1 records of `agentteam.domain`.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic import ConfigDict, Field

from agentteam.domain.assistant import AssistantDefinitionV1
from agentteam.domain.bundle import BundleManifestV1
from agentteam.domain.common import RecordModel
from agentteam.domain.profile import CapabilityRecordV1, HarnessProfileV1
from agentteam.domain.review import NormalizedReviewV1
from agentteam.domain.run import (
    CommandV1,
    EnvironmentV1,
    InjectionV1,
    ObservedV1,
    PlaceholderV1,
    RequestedV1,
    SchemaOutcome,
    SelectionV1,
    UsageV1,
)


class InternalModel(RecordModel):
    """Base for internal working objects; may carry Paths (never serialised as contracts)."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)


class RenderContext(InternalModel):
    """Everything a renderer needs; write targets are separated from read sources.

    `workspace` is the read-only source tree; `workspace_root` and
    `config_root` are where workspace-channel and config-home-channel files
    are written (a real run points them at the leg's isolated copies; a
    render-only run redirects them under the output directory so nothing the
    user owns is ever touched).
    """

    profile: HarnessProfileV1
    definition: AssistantDefinitionV1
    package_root: Path
    bundle: BundleManifestV1
    selection: SelectionV1
    requested: RequestedV1
    task_file: Path
    workspace: Path
    workspace_root: Path
    config_root: Path
    scratch_dir: Path
    parent_env: dict[str, str]
    platform: str
    run_id: str
    invocation_id: str
    timeout_seconds: int
    profile_file: Path | None = None


class RawInvocationV1(InternalModel):
    """What one process execution produced, before any vendor parsing."""

    exit_code: int | None
    signal: str | None
    stdout: bytes
    stderr: bytes
    output_file_text: str | None
    timed_out: bool
    duration_ms: int
    started_at: datetime | None = None
    finished_at: datetime | None = None


class FileWriteV1(InternalModel):
    """One file the renderer wrote (role: prompt, schema, skill:<name>, instructions...)."""

    path: Path
    role: str
    channel: str


class RenderedInvocationV1(InternalModel):
    """A fully rendered invocation, ready for the process runner.

    `env_values` is excluded from every dump so serialising this object can
    never leak environment values; `environment` carries names only.
    """

    harness: str
    argv: list[str]
    cwd: Path
    env_values: dict[str, str] = Field(exclude=True)
    stdin_text: str | None
    output_file: Path | None
    files_written: list[FileWriteV1]
    injection: InjectionV1
    command: CommandV1
    environment: EnvironmentV1
    placeholders: list[PlaceholderV1]
    schema_channel: str
    timeout_seconds: int


class ParsedLegV1(InternalModel):
    """One leg's parse result; problems instead of exceptions for vendor noise."""

    review: NormalizedReviewV1 | None
    schema_outcome: SchemaOutcome
    usage: UsageV1
    observed: ObservedV1
    problems: list[str] = Field(default_factory=list)


class HarnessCapabilityReportV1(InternalModel):
    """Probe output shape (populated at G5; the Protocol needs the type now)."""

    harness: str
    rows: list[CapabilityRecordV1] = Field(default_factory=list)
