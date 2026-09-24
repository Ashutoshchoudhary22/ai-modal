"""Model registry record types."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ModelRegistryRecord(BaseModel):
    model_id: str
    model_name: str
    version: str
    provider: str
    architecture: str | None = None
    capabilities: dict[str, Any] = Field(default_factory=dict)
    context_length: int | None = None
    modalities: list[str] = Field(default_factory=lambda: ["text"])
    status: str = "registered"
    local_path: str | None = None
    created_at: datetime | None = None
