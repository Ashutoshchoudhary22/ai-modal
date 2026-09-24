"""Inference request/response models."""

from typing import Any, Literal, Self

from pydantic import BaseModel, Field, model_validator

from ai_platform_protocol.models.common import TokenUsage


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str


class GenerateRequest(BaseModel):
    model: str = "default"
    messages: list[ChatMessage] = Field(default_factory=list)
    prompt: str | None = None
    system_prompt: str | None = None
    max_tokens: int = Field(default=1024, ge=1, le=128_000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    stop: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_prompt_source(self) -> Self:
        if not self.messages and not self.prompt:
            raise ValueError("Either messages or prompt must be provided")
        return self

    def resolved_messages(self) -> list[ChatMessage]:
        if self.messages:
            return self.messages
        messages: list[ChatMessage] = []
        if self.system_prompt:
            messages.append(ChatMessage(role="system", content=self.system_prompt))
        if self.prompt:
            messages.append(ChatMessage(role="user", content=self.prompt))
        return messages


class GenerateResponse(BaseModel):
    id: str
    model: str
    content: str
    finish_reason: Literal["stop", "length", "error"] = "stop"
    usage: TokenUsage
    provider: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class StreamChunk(BaseModel):
    type: Literal["chunk", "done", "error"]
    content: str | None = None
    usage: TokenUsage | None = None
    message: str | None = None
    provider: str | None = None


class StructuredGenerateRequest(BaseModel):
    model: str = "default"
    messages: list[ChatMessage] = Field(default_factory=list)
    prompt: str | None = None
    system_prompt: str | None = None
    response_schema: dict[str, Any]
    max_tokens: int = Field(default=1024, ge=1, le=128_000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_prompt_source(self) -> Self:
        if not self.messages and not self.prompt:
            raise ValueError("Either messages or prompt must be provided")
        return self

    def resolved_messages(self) -> list[ChatMessage]:
        if self.messages:
            return self.messages
        messages: list[ChatMessage] = []
        if self.system_prompt:
            messages.append(ChatMessage(role="system", content=self.system_prompt))
        if self.prompt:
            messages.append(ChatMessage(role="user", content=self.prompt))
        return messages


class StructuredGenerateResponse(BaseModel):
    id: str
    model: str
    parsed: dict[str, Any]
    usage: TokenUsage
    provider: str | None = None


class EmbedRequest(BaseModel):
    model: str = "embed-default"
    inputs: list[str]
    metadata: dict[str, Any] = Field(default_factory=dict)


class EmbedResponse(BaseModel):
    model: str
    embeddings: list[list[float]]
    dimensions: int
    usage: TokenUsage
    provider: str | None = None


class VisionImageInput(BaseModel):
    url: str | None = None
    base64: str | None = None
    detail: Literal["low", "high", "auto"] = "auto"


class VisionRequest(BaseModel):
    model: str = "vision-default"
    messages: list[ChatMessage] = Field(default_factory=list)
    images: list[VisionImageInput] = Field(default_factory=list)
    max_tokens: int = Field(default=1024, ge=1, le=128_000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class VisionResponse(BaseModel):
    id: str
    model: str
    content: str
    usage: TokenUsage
    provider: str | None = None
