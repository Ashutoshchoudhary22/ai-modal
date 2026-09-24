"""Local vision model provider — lazy-loaded, optional dependencies."""

from __future__ import annotations

from agent.vision.errors import VisionError
from ai_platform_protocol.vision import VisionErrorCode, VisionRequest, VisionResponse


class LocalVisionProvider:
    provider_id = "local"
    provider_name = "Local Vision Provider"

    def __init__(self, model_ref: str = "", device: str = "auto") -> None:
        self._model_ref = model_ref
        self._device = device
        self._ready = False

    def is_ready(self) -> bool:
        return self._ready

    async def analyze(self, request: VisionRequest) -> VisionResponse:
        raise VisionError(
            VisionErrorCode.VISION_PROVIDER_UNAVAILABLE,
            "Local vision provider is not configured. "
            "Set AI_PLATFORM_VISION_MODEL and install optional vision dependencies.",
        )
