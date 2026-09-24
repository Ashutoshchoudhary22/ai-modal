"""Future proprietary model provider placeholder."""

from __future__ import annotations

from collections.abc import AsyncIterator

from ai_platform_protocol.models.errors import ProviderErrorCode
from ai_platform_protocol.models.inference import (
    EmbedRequest,
    EmbedResponse,
    GenerateRequest,
    GenerateResponse,
    StreamChunk,
    StructuredGenerateRequest,
    StructuredGenerateResponse,
    VisionRequest,
    VisionResponse,
)
from ai_platform_protocol.models.provider import ProviderCapabilities, ProviderState, ProviderStatus

from ai_api.providers.errors import ProviderError


class ProprietaryModelProvider:
    provider_id = "proprietary"
    provider_name = "Proprietary Model Provider"

    async def get_status(self) -> ProviderStatus:
        return ProviderStatus(
            provider_id=self.provider_id,
            provider_name=self.provider_name,
            state=ProviderState.UNAVAILABLE,
            message="Proprietary model provider is not implemented yet",
            capabilities=ProviderCapabilities(
                generate=False,
                stream=False,
                structured=False,
                embed=False,
                vision=False,
            ),
        )

    async def _not_implemented(self) -> None:
        raise ProviderError(
            ProviderErrorCode.PROVIDER_UNAVAILABLE,
            "Proprietary model provider is not implemented yet",
            status_code=503,
        )

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        await self._not_implemented()
        raise AssertionError("unreachable")

    async def stream(self, request: GenerateRequest) -> AsyncIterator[StreamChunk]:
        await self._not_implemented()
        yield StreamChunk(type="error", message="unreachable")
        raise AssertionError("unreachable")

    async def generate_structured(
        self, request: StructuredGenerateRequest
    ) -> StructuredGenerateResponse:
        await self._not_implemented()
        raise AssertionError("unreachable")

    async def embed(self, request: EmbedRequest) -> EmbedResponse:
        await self._not_implemented()
        raise AssertionError("unreachable")

    async def vision(self, request: VisionRequest) -> VisionResponse:
        await self._not_implemented()
        raise AssertionError("unreachable")

    def count_tokens(self, text: str, model_id: str | None = None) -> int:
        _ = (text, model_id)
        raise ProviderError(
            ProviderErrorCode.PROVIDER_UNAVAILABLE,
            "Proprietary model provider is not implemented yet",
            status_code=503,
        )
