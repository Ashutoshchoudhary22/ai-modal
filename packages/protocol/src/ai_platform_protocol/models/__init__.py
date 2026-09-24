"""Core Pydantic models for AI Platform API."""

from ai_platform_protocol.models.common import ErrorDetail, ErrorResponse, TokenUsage
from ai_platform_protocol.models.errors import ProviderErrorCode
from ai_platform_protocol.models.inference import (
    ChatMessage,
    EmbedRequest,
    EmbedResponse,
    GenerateRequest,
    GenerateResponse,
    StreamChunk,
    StructuredGenerateRequest,
    StructuredGenerateResponse,
    VisionImageInput,
    VisionRequest,
    VisionResponse,
)
from ai_platform_protocol.models.provider import (
    DeviceInfo,
    ProviderCapabilities,
    ProviderState,
    ProviderStatus,
)
from ai_platform_protocol.models.registry import ModelRegistryRecord

__all__ = [
    "ChatMessage",
    "DeviceInfo",
    "EmbedRequest",
    "EmbedResponse",
    "ErrorDetail",
    "ErrorResponse",
    "GenerateRequest",
    "GenerateResponse",
    "ModelRegistryRecord",
    "ProviderCapabilities",
    "ProviderErrorCode",
    "ProviderState",
    "ProviderStatus",
    "StreamChunk",
    "StructuredGenerateRequest",
    "StructuredGenerateResponse",
    "TokenUsage",
    "VisionImageInput",
    "VisionRequest",
    "VisionResponse",
]
