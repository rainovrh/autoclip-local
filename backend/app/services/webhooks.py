"""Webhook notification service for job events."""

import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

UTC = timezone.utc


def _build_signature(payload: dict, secret: str) -> str:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return hmac.new(secret.encode(), raw.encode(), hashlib.sha256).hexdigest()


async def send_webhook_notification(
    job: Any,
    event_type: str,
    error_message: str | None = None,
) -> None:
    """Send webhook notification for job events."""
    settings = get_settings()
    webhook_url = getattr(job, "webhook_url", None) or settings.default_webhook_url
    if not webhook_url:
        return

    payload = {
        "event": event_type,
        "job_id": job.id,
        "project_id": job.project_id,
        "job_type": job.job_type,
        "status": job.status,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    if error_message:
        payload["error"] = error_message

    if event_type == "completed":
        payload["message"] = f"Job {job.id} completed successfully."
    elif event_type == "failed":
        payload["message"] = f"Job {job.id} failed: {error_message}"

    headers = {"Content-Type": "application/json"}
    webhook_secret = getattr(settings, "webhook_secret", "")
    if webhook_secret:
        headers["X-Webhook-Signature"] = _build_signature(payload, webhook_secret)

    try:
        async with httpx.AsyncClient(timeout=settings.webhook_timeout) as client:
            response = await client.post(
                webhook_url,
                json=payload,
                headers=headers,
            )
            logger.info(
                "Webhook sent to %s for job %s: %s %s",
                webhook_url,
                job.id,
                response.status_code,
                event_type,
            )
    except Exception as exc:
        logger.error("Webhook failed for job %s: %s", job.id, exc)
