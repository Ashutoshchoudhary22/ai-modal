"""Platform metadata routes."""

from ai_platform_shared.config import get_settings
from fastapi import APIRouter

router = APIRouter(tags=["meta"])


@router.get("/meta")
async def get_meta() -> dict[str, object]:
    settings = get_settings()
    return {
        "api_version": "v1",
        "platform_version": "0.1.0",
        "supported_modalities": ["text"],
        "providers": [settings.model_provider],
    }
