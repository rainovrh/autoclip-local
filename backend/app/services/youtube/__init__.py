"""YouTube URL validation and download service using yt-dlp."""

import logging
import re
from pathlib import Path

import yt_dlp

logger = logging.getLogger(__name__)

YOUTUBE_URL_PATTERN = re.compile(
    r"^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)[A-Za-z0-9_-]{11}(\?.*)?(&.*)?$"
)


def is_valid_youtube_url(url: str) -> bool:
    return bool(YOUTUBE_URL_PATTERN.match(url))


def download_youtube_video(url: str, output_folder: Path) -> dict:
    """Download YouTube video to the specified folder using yt-dlp."""
    output_template = str(output_folder / "%(title)s.%(ext)s")
    ydl_opts = {
        "format": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "merge_output_format": "mp4",
    }

    metadata: dict = {
        "file_path": None,
        "title": None,
        "duration": None,
        "resolution": None,
        "fps": None,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if info is None:
            raise RuntimeError("Gagal mengunduh video YouTube.")

        metadata["title"] = info.get("title")
        metadata["duration"] = info.get("duration")
        metadata["resolution"] = info.get("resolution") or (
            f"{info.get('width')}x{info.get('height')}"
            if info.get("width") and info.get("height")
            else None
        )
        metadata["fps"] = info.get("fps")
        metadata["file_path"] = ydl.prepare_filename(info)

    return metadata
