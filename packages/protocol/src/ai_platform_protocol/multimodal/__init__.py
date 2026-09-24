"""Multimodal model protocol — Phase 10."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class MultimodalErrorCode(StrEnum):
    MULTIMODAL_PROVIDER_UNAVAILABLE = "multimodal_provider_unavailable"
    MULTIMODAL_MODEL_NOT_FOUND = "multimodal_model_not_found"
    MULTIMODAL_INPUT_INVALID = "multimodal_input_invalid"
    MULTIMODAL_IMAGE_LIMIT_EXCEEDED = "multimodal_image_limit_exceeded"
    MULTIMODAL_CONTEXT_LIMIT_EXCEEDED = "multimodal_context_limit_exceeded"
    VISION_ENCODER_UNAVAILABLE = "vision_encoder_unavailable"
    IMAGE_PROCESSING_FAILED = "image_processing_failed"
    PROJECTOR_FAILED = "projector_failed"
    FUSION_FAILED = "fusion_failed"
    MULTIMODAL_INFERENCE_FAILED = "multimodal_inference_failed"
    MULTIMODAL_STREAM_FAILED = "multimodal_stream_failed"
    MULTIMODAL_CAPABILITY_UNSUPPORTED = "multimodal_capability_unsupported"
    MODEL_DEVICE_UNAVAILABLE = "model_device_unavailable"
    MODEL_OUT_OF_MEMORY = "model_out_of_memory"


class ImageReference(BaseModel):
    """Secure image reference — no raw filesystem paths."""

    id: str
    mime_type: str
    width: int
    height: int
    byte_size: int
    storage_reference: str
    sha256: str


class TextContent(BaseModel):
    type: Literal["text"] = "text"
    text: str


class ImageContent(BaseModel):
    type: Literal["image"] = "image"
    image: ImageReference
    detail: Literal["low", "high", "auto"] = "auto"


MultimodalContent = TextContent | ImageContent


class MultimodalMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: list[MultimodalContent] = Field(default_factory=list)

    def text_parts(self) -> list[str]:
        return [part.text for part in self.content if isinstance(part, TextContent)]

    def image_parts(self) -> list[ImageReference]:
        return [part.image for part in self.content if isinstance(part, ImageContent)]


class MultimodalCapabilities(BaseModel):
    supports_text: bool = True
    supports_image: bool = True
    supports_multi_image: bool = True
    supports_streaming: bool = True
    supports_structured_output: bool = True
    supports_embeddings: bool = False
    max_context_tokens: int = 8192
    max_images: int = 4
    max_image_pixels: int = 16_777_216
    embedding_dimension: int | None = None
    modalities: list[str] = Field(default_factory=lambda: ["text", "image"])


class MultimodalUsage(BaseModel):
    text_input_tokens: int = 0
    visual_input_tokens: int = 0
    total_input_units: int = 0
    output_tokens: int = 0
    image_count: int = 0
    processing_time_ms: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class ImageProcessingMetadata(BaseModel):
    original_width: int
    original_height: int
    processed_width: int
    processed_height: int
    scale: float = 1.0
    crop: dict[str, int] | None = None
    padding: dict[str, int] | None = None


class ProcessedImage(BaseModel):
    image_id: str
    mime_type: str
    metadata: ImageProcessingMetadata
    tensor_shape: list[int] = Field(default_factory=list)
    data_reference: str | None = None


class VisualEmbedding(BaseModel):
    image_id: str
    embeddings: list[list[float]]
    embedding_dimension: int
    token_count: int
    spatial_shape: dict[str, int] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class VisionEncoderOutput(BaseModel):
    embeddings: list[VisualEmbedding]
    embedding_dimension: int
    token_count: int
    spatial_shape: dict[str, int] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MultimodalEmbedding(BaseModel):
    text_embedding: list[float] | None = None
    visual_embeddings: list[VisualEmbedding] = Field(default_factory=list)
    fused_embedding: list[float] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MultimodalRequest(BaseModel):
    model: str = "default"
    messages: list[MultimodalMessage] = Field(default_factory=list)
    prompt: str | None = None
    system_prompt: str | None = None
    images: list[ImageReference] = Field(default_factory=list)
    response_schema: dict[str, Any] | None = None
    max_tokens: int = Field(default=1024, ge=1, le=128_000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    stream: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_input(self) -> MultimodalRequest:
        has_messages = bool(self.messages)
        has_prompt = bool(self.prompt)
        has_images = bool(self.images) or any(m.image_parts() for m in self.messages)
        if not has_messages and not has_prompt and not has_images:
            raise ValueError("At least one of messages, prompt, or images is required")
        return self

    def resolved_messages(self) -> list[MultimodalMessage]:
        if self.messages:
            return self.messages
        content: list[MultimodalContent] = []
        if self.prompt:
            content.append(TextContent(text=self.prompt))
        for image in self.images:
            content.append(ImageContent(image=image))
        messages: list[MultimodalMessage] = []
        if self.system_prompt:
            messages.append(
                MultimodalMessage(
                    role="system",
                    content=[TextContent(text=self.system_prompt)],
                )
            )
        if content:
            messages.append(MultimodalMessage(role="user", content=content))
        return messages

    def image_count(self) -> int:
        count = 0
        for message in self.resolved_messages():
            count += len(message.image_parts())
        return count


class MultimodalResponse(BaseModel):
    id: str
    model: str
    content: str | None = None
    parsed: dict[str, Any] | None = None
    finish_reason: Literal["stop", "length", "error"] = "stop"
    usage: MultimodalUsage
    provider: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MultimodalStreamChunk(BaseModel):
    type: Literal["chunk", "structured_delta", "done", "error"]
    content: str | None = None
    parsed_delta: dict[str, Any] | None = None
    usage: MultimodalUsage | None = None
    finish_reason: str | None = None
    provider: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MultimodalBatchRequest(BaseModel):
    requests: list[MultimodalRequest] = Field(default_factory=list)


class MultimodalBatchResponse(BaseModel):
    responses: list[MultimodalResponse] = Field(default_factory=list)


class ContextBudget(BaseModel):
    text_tokens: int = 0
    visual_tokens: int = 0
    image_count: int = 0
    image_pixels: int = 0
    total_context_cost: int = 0
    within_limit: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
