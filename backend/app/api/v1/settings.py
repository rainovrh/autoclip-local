import logging

from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.settings import AppSettingsResponse, HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Cek kesehatan API."""
    return HealthResponse()


@router.get("", response_model=AppSettingsResponse)
async def get_settings_endpoint() -> AppSettingsResponse:
    """Pengaturan global aplikasi."""
    settings = get_settings()
    return AppSettingsResponse(
        default_aspect_ratio="9:16",
        default_whisper_model=settings.default_whisper_model,
        default_ollama_model=settings.default_ollama_model,
    )
