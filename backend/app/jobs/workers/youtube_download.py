"""Worker: unduh video YouTube menggunakan yt-dlp."""

import logging
from pathlib import Path

import yt_dlp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.project import Project
from app.db.models.video_source import VideoSource

logger = logging.getLogger(__name__)


async def run_youtube_download(session: AsyncSession, job) -> None:
    """Unduh video YouTube ke folder proyek."""
    logger.info("Memulai youtube_download untuk job %s", job.id)

    project = await session.get(Project, job.project_id)
    if project is None:
        raise ValueError(f"Project {job.project_id} tidak ditemukan.")

    if project.source_type != "youtube":
        raise ValueError("Proyek ini bukan sumber YouTube.")

    youtube_url = project.source_url
    if not youtube_url:
        raise ValueError("URL YouTube kosong.")

    from app.services.youtube import download_youtube_video

    existing_source = await session.execute(
        select(VideoSource).where(VideoSource.project_id == project.id)
    )
    existing = existing_source.scalar_one_or_none()
    if existing:
        old_path = Path(existing.file_path)
        if old_path.exists():
            old_path.unlink()
        await session.delete(existing)
        await session.flush()

    try:
        metadata = download_youtube_video(youtube_url, Path(project.folder_path))
    except Exception as exc:
        raise RuntimeError(f"Gagal mengunduh video YouTube: {exc}") from exc

    downloaded_path = Path(metadata["file_path"])
    if not downloaded_path.exists():
        raise RuntimeError("File video tidak ditemukan setelah unduhan.")

    video_source = VideoSource(
        project_id=project.id,
        file_path=str(downloaded_path),
        resolution=metadata.get("resolution"),
        duration_seconds=metadata.get("duration"),
        fps=metadata.get("fps"),
    )
    session.add(video_source)
    project.status = "AUDIO_EXTRACTED"
    session.add(project)
    await session.commit()
    await session.refresh(video_source)

    logger.info(
        "YouTube diunduh: project=%s file=%s",
        project.id,
        downloaded_path.name,
    )
