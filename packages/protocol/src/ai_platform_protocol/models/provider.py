"""Provider status and capability models."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ProviderState(StrEnum):
    CONFIGURED = "configured"
    LOADING = "loading"
    READY = "ready"
    UNAVAILABLE = "unavailable"


class ProviderCapabilities(BaseModel):
    generate: bool = True
    stream: bool = True
    structured: bool = True
    embed: bool = False
    vision: bool = False
    modalities: list[str] = Field(default_factory=lambda: ["text"])


class DeviceInfo(BaseModel):
    device_type: str
    device_name: str | None = None
    cuda_available: bool = False
    cuda_device_count: int = 0
    dtype: str | None = None


class ProviderStatus(BaseModel):
    provider_id: str
    provider_name: str
    state: ProviderState
    model_id: str | None = None
    message: str | None = None
    device: DeviceInfo | None = None
    capabilities: ProviderCapabilities = Field(default_factory=ProviderCapabilities)
    diagnostics: dict[str, Any] = Field(default_factory=dict)
