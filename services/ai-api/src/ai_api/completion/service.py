"""Completion service — maps CompletionRequest to ModelProvider."""

from __future__ import annotations

import time
import uuid

from ai_api.completion.mock import mock_completion
from ai_api.completion.prompts import to_generate_request
from ai_api.completion.security import is_sensitive_path, redact_secrets
from ai_api.completion.validation import check_balanced_delimiters, sanitize_completion
from ai_api.providers.errors import ProviderError
from ai_platform_protocol.completion import (
    CompletionCandidate,
    CompletionRequest,
    CompletionResponse,
)
from ai_platform_protocol.providers.base import ModelProvider
from ai_platform_shared.config import Settings, get_settings
from ai_platform_shared.logging import get_logger

logger = get_logger(__name__)


class CompletionServiceError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class CompletionService:
    def __init__(self, provider: ModelProvider, settings: Settings | None = None) -> None:
        self._provider = provider
        self._settings = settings or get_settings()

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        if not self._settings.completion_enabled:
            raise CompletionServiceError("COMPLETION_DISABLED", "Inline completion is disabled")

        if is_sensitive_path(request.file_path):
            raise CompletionServiceError(
                "COMPLETION_SENSITIVE_FILE",
                f"Completion disabled for sensitive file: {request.file_path}",
            )

        max_prefix = self._settings.completion_max_prefix_tokens * 4
        max_suffix = self._settings.completion_max_suffix_tokens * 4
        if len(request.prefix) > max_prefix or len(request.suffix) > max_suffix:
            raise CompletionServiceError(
                "COMPLETION_CONTEXT_TOO_LARGE",
                "Prefix or suffix exceeds allowed size",
            )

        request_id = request.request_id or str(uuid.uuid4())
        model = (
            request.model
            if request.model != "default"
            else self._settings.completion_model or self._settings.default_model
        )

        started = time.perf_counter()
        text = await self._generate_completion(request, model)
        latency_ms = int((time.perf_counter() - started) * 1000)

        sanitized = sanitize_completion(
            text,
            request.prefix,
            request.suffix,
            max_lines=self._settings.completion_max_output_lines,
        )
        if not sanitized:
            raise CompletionServiceError("COMPLETION_INVALID_RESPONSE", "Empty completion")

        candidate = CompletionCandidate(
            text=sanitized,
            confidence=None,
            finish_reason="stop",
        )

        logger.info(
            "completion request_id=%s model=%s language=%s latency_ms=%d valid_syntax=%s",
            request_id,
            model,
            request.language,
            latency_ms,
            check_balanced_delimiters(sanitized),
        )

        return CompletionResponse(
            request_id=request_id,
            completion=candidate,
            candidates=[candidate],
            usage=None,
            model=model,
            provider=getattr(self._provider, "provider_id", "unknown"),
            latency_ms=latency_ms,
        )

    async def _generate_completion(self, request: CompletionRequest, model: str) -> str:
        provider_id = getattr(self._provider, "provider_id", "")
        if provider_id == "development_mock":
            return mock_completion(request.prefix, request.suffix, request.language)

        safe_request = request.model_copy(
            update={
                "prefix": redact_secrets(request.prefix),
                "suffix": redact_secrets(request.suffix),
            }
        )
        gen_request = to_generate_request(safe_request, model)
        try:
            response = await self._provider.generate(gen_request)
        except ProviderError as exc:
            raise CompletionServiceError(
                "COMPLETION_PROVIDER_UNAVAILABLE",
                exc.message,
            ) from exc
        return response.content
