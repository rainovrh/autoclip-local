"""Authentication and authorization middleware."""

import logging
from typing import Callable

from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.db.models.api_key import ApiKey
from app.db.session import get_db_session

logger = logging.getLogger(__name__)

PUBLIC_PATHS = {
    "/api/v1/settings/health",
    "/docs",
    "/openapi.json",
}


async def validate_api_key(api_key: str) -> bool:
    """Validate API key against database."""
    async for session in get_db_session():
        result = await session.execute(
            select(ApiKey).where(ApiKey.api_key_value == api_key).where(ApiKey.is_active)
        )
        key = result.scalar_one_or_none()
        return key is not None
    return False


class AuthMiddleware:
    """Middleware for API key authentication."""

    def __init__(self, app: Callable) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if path in PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/openapi"):
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        api_key = headers.get(b"x-api-key", b"").decode("utf-8", errors="replace")

        if not api_key:
            response = JSONResponse(
                status_code=401,
                content={"detail": "Missing API key. Provide X-API-Key header."},
            )
            await response(scope, receive, send)
            return

        is_valid = await validate_api_key(api_key)
        if not is_valid:
            client = scope.get("client")
            logger.warning(
                "Invalid API key attempt from %s",
                client[0] if client else "unknown",
            )
            response = JSONResponse(
                status_code=403,
                content={"detail": "Invalid or inactive API key."},
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
