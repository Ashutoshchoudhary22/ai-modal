"""Health and readiness routes."""

from ai_platform_shared.config import get_settings
from fastapi import APIRouter

from ai_api.dependencies import get_inference_service

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "version": "0.1.0",
        "environment": settings.env,
    }


@router.get("/ready")
async def readiness_check() -> dict[str, object]:
    service = get_inference_service()
    status = await service.provider.get_status()
    ready = status.state.value in {"ready", "configured"}
    return {
        "status": "ready" if ready else "not_ready",
        "provider": status.provider_id,
        "provider_state": status.state.value,
        "model_id": status.model_id,
        "message": status.message,
        "device": status.device.model_dump() if status.device else None,
    }
