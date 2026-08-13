"""Rate limiting middleware using sliding window."""

import logging
import time
from collections import defaultdict
from typing import Callable

from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """Simple in-memory rate limiting middleware."""

    def __init__(
        self,
        app: Callable,
        requests_per_minute: int = 60,
        window_seconds: int = 60,
    ) -> None:
        self.app = app
        self.requests_per_minute = requests_per_minute
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        client = scope.get("client")
        client_ip = client[0] if client else "unknown"
        now = time.time()

        window_start = now - self.window_seconds
        self.requests[client_ip] = [
            ts for ts in self.requests[client_ip] if ts > window_start
        ]

        if len(self.requests[client_ip]) >= self.requests_per_minute:
            logger.warning("Rate limit exceeded for %s", client_ip)
            response = JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": self.window_seconds,
                },
            )
            await response(scope, receive, send)
            return

        self.requests[client_ip].append(now)
        await self.app(scope, receive, send)
