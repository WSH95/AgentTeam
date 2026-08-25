"""Coordination-provider registry metadata and generic disposition API."""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from importlib import import_module
from pathlib import Path
from typing import Protocol, cast

from agentteam.coordination.protocol import CoordinationSubstrate
from agentteam.domain.team import SubstrateKind

_OPTIONAL_PROVIDER_KEY = "clawteam"
_OPTIONAL_PROVIDER_MODULE = "agentteam.coordination.clawteam"


class ProviderDisposition(StrEnum):
    SUPPORTED = "supported"
    PENDING = "pending"
    PARITY_GREEN = "parity-green"
    FAILED_ROUTED = "failed-routed"
    DROPPED_BY_OWNER = "dropped-by-owner"


CLAWTEAM_DISPOSITION = ProviderDisposition.PARITY_GREEN

_PROVIDER_MODULES = {
    SubstrateKind.LOCAL.value: "agentteam.coordination.local",
    _OPTIONAL_PROVIDER_KEY: _OPTIONAL_PROVIDER_MODULE,
}


def provider_disposition(substrate: SubstrateKind) -> ProviderDisposition:
    """Return support metadata without importing an optional provider."""
    if substrate.value not in _PROVIDER_MODULES:
        raise ValueError(f"unregistered coordination substrate: {substrate.value}")
    if substrate is SubstrateKind.LOCAL:
        return ProviderDisposition.SUPPORTED
    return CLAWTEAM_DISPOSITION


class _ProviderFactory(Protocol):
    def __call__(
        self,
        coordination_root: Path,
        *,
        environ: Mapping[str, str],
        platform: str,
    ) -> CoordinationSubstrate: ...


def create_provider(
    substrate: SubstrateKind,
    coordination_root: Path,
    *,
    environ: Mapping[str, str],
    platform: str,
) -> CoordinationSubstrate:
    """Construct a registered provider without exposing it to the run layer."""
    disposition = provider_disposition(substrate)
    if disposition not in {
        ProviderDisposition.SUPPORTED,
        ProviderDisposition.PARITY_GREEN,
    }:
        raise RuntimeError(
            f"coordination substrate {substrate.value!r} is unavailable "
            f"(disposition: {disposition.value})"
        )
    module = import_module(_PROVIDER_MODULES[substrate.value])
    factory = cast(_ProviderFactory, module.__dict__["create_provider"])
    return factory(
        coordination_root,
        environ=environ,
        platform=platform,
    )


__all__ = [
    "ProviderDisposition",
    "create_provider",
    "provider_disposition",
]
