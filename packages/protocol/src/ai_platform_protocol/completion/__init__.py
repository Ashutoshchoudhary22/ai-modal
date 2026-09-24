"""Code completion protocol types."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class CompletionPosition(BaseModel):
    line: int = Field(ge=0)
    column: int = Field(ge=0)


class CompletionContext(BaseModel):
    nearby_code: str | None = None
    imports: list[str] = Field(default_factory=list)
    symbols: list[str] = Field(default_factory=list)
    repository_context: str | None = None
    current_function: str | None = None


class CompletionOptions(BaseModel):
    max_tokens: int = Field(default=256, ge=1, le=4096)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    stop: list[str] = Field(default_factory=list)
    context_lines: int = Field(default=50, ge=0, le=500)


class CompletionRequest(BaseModel):
    request_id: str | None = None
    workspace_id: str | None = None
    file_path: str
    language: str = "plaintext"
    prefix: str
    suffix: str = ""
    cursor: CompletionPosition
    document_version: int = Field(default=0, ge=0)
    context: CompletionContext = Field(default_factory=CompletionContext)
    options: CompletionOptions = Field(default_factory=CompletionOptions)
    model: str = "default"
    provider: str | None = None
    trigger_kind: Literal["automatic", "manual"] = "automatic"


class CompletionCandidate(BaseModel):
    text: str
    confidence: float | None = None
    finish_reason: str | None = None


class CompletionUsage(BaseModel):
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class CompletionResponse(BaseModel):
    request_id: str
    completion: CompletionCandidate
    candidates: list[CompletionCandidate] = Field(default_factory=list)
    usage: CompletionUsage | None = None
    model: str
    provider: str
    latency_ms: int | None = None


class CompletionCapabilities(BaseModel):
    enabled: bool = True
    streaming: bool = False
    multi_candidate: bool = False
    repository_context: bool = True


class CompletionErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
