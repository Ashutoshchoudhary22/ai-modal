"""Adapter from MultimodalModel to agent DecisionModel protocol."""

from __future__ import annotations

from ai_platform_protocol.models.common import TokenUsage
from ai_platform_protocol.models.inference import (
    GenerateRequest,
    GenerateResponse,
    StructuredGenerateRequest,
    StructuredGenerateResponse,
)
from ai_platform_protocol.multimodal import MultimodalMessage, MultimodalRequest, TextContent


class MultimodalDecisionAdapter:
    def __init__(self, model) -> None:
        self._model = model

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        mm_request = self._to_multimodal_request(request)
        response = await self._model.generate(mm_request)
        return GenerateResponse(
            id=response.id,
            model=response.model,
            content=response.content or "",
            finish_reason=response.finish_reason,
            usage=self._usage(response.usage),
            provider=response.provider,
        )

    async def generate_structured(
        self, request: StructuredGenerateRequest
    ) -> StructuredGenerateResponse:
        mm_request = self._to_multimodal_request(request)
        mm_request = mm_request.model_copy(update={"response_schema": request.response_schema})
        response = await self._model.generate_structured(mm_request)
        return StructuredGenerateResponse(
            id=response.id,
            model=response.model,
            parsed=response.parsed or {},
            usage=self._usage(response.usage),
            provider=response.provider,
        )

    def _to_multimodal_request(
        self, request: GenerateRequest | StructuredGenerateRequest
    ) -> MultimodalRequest:
        if request.messages:
            return MultimodalRequest(
                model=request.model,
                messages=[
                    MultimodalMessage(
                        role=m.role,
                        content=[TextContent(text=m.content)],
                    )
                    for m in request.resolved_messages()
                ],
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
            )
        return MultimodalRequest(
            model=request.model,
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
        )

    @staticmethod
    def _usage(usage) -> TokenUsage:
        return TokenUsage(
            prompt_tokens=usage.total_input_units,
            completion_tokens=usage.output_tokens,
            total_tokens=usage.total_input_units + usage.output_tokens,
        )
