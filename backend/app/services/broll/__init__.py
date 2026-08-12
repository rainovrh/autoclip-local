"""Pexels client + fallback logic (non-blocking overlay)."""

import logging
from dataclasses import dataclass
from pathlib import Path

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class BrollSearchResult:
    query: str
    video_url: str | None
    local_path: str | None
    status: str
    error: str | None = None


class PexelsClient:
    """Client untuk Pexels API."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or get_settings().pexels_api_key
        self.base_url = "https://api.pexels.com/videos"

    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def search_video(self, query: str, per_page: int = 3) -> BrollSearchResult:
        """Cari video pendek di Pexels berdasarkan query."""
        if not self.is_configured():
            return BrollSearchResult(
                query=query,
                video_url=None,
                local_path=None,
                status="skipped",
                error="Pexels API key tidak dikonfigurasi.",
            )

        headers = {"Authorization": self.api_key}
        params = {"query": query, "per_page": per_page, "orientation": "landscape"}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/search",
                    headers=headers,
                    params=params,
                )
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            return BrollSearchResult(
                query=query,
                video_url=None,
                local_path=None,
                status="failed",
                error=f"Pexels search failed: {exc}",
            )

        videos = data.get("videos", [])
        if not videos:
            return BrollSearchResult(
                query=query,
                video_url=None,
                local_path=None,
                status="skipped",
                error="Tidak ada video yang cocok.",
            )

        best_video = videos[0]
        video_files = best_video.get("video_files", [])
        download_url = None
        for vf in video_files:
            if vf.get("width", 0) >= 1280 and vf.get("height", 0) >= 720:
                download_url = vf.get("link")
                break

        if not download_url and video_files:
            download_url = video_files[0].get("link")

        return BrollSearchResult(
            query=query,
            video_url=download_url,
            local_path=None,
            status="found",
        )

    async def download_video(self, url: str, destination: Path) -> str | None:
        """Unduh video dari URL ke path lokal."""
        try:
            async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(response.content)
                return str(destination)
        except Exception as exc:
            logger.error("Gagal mengunduh b-roll dari %s: %s", url, exc)
            return None


pexels_client = PexelsClient()

