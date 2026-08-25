"""Coordination-provider registry metadata and generic disposition API."""

from __future__ import annotations

from enum import StrEnum

from agentteam.domain.team import SubstrateKind

_OPTIONAL_PROVIDER_KEY = "clawteam"
_OPTIONAL_PROVIDER_MODULE = "agentteam.coordination.clawteam"


class ProviderDisposition(StrEnum):
    SUPPORTED = "supported"
    PENDING = "pending"
    PARITY_GREEN = "parity-green"
    FAILED_ROUTED = "failed-routed"
    DROPPED_BY_OWNER = "dropped-by-owner"


CLAWTEAM_DISPOSITION = ProviderDisposition.PENDING

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


__all__ = [
    "ProviderDisposition",
    "provider_disposition",
]
