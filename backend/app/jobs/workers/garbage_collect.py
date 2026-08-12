"""Worker: garbage collection untuk membersihkan file sementara."""

import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.garbage_collection_log import GarbageCollectionLog
from app.db.models.processing_job import ProcessingJob
from app.db.models.project import Project
from app.db.models.video_source import VideoSource

logger = logging.getLogger(__name__)


async def run_garbage_collect(session: AsyncSession, job: ProcessingJob) -> None:
    """Bersihkan file temporary untuk proyek yang sudah selesai."""
    logger.info("Memulai garbage_collect untuk job %s", job.id)

    project = await session.get(Project, job.project_id)
    if project is None:
        raise ValueError(f"Project {job.project_id} tidak ditemukan.")

    if project.status not in {"RENDERED", "FAILED"}:
        logger.info(
            "Project %s belum selesai, melewati garbage collection.", project.id
        )
        return

    deleted_files = []

    video_sources = await session.execute(
        select(VideoSource).where(VideoSource.project_id == project.id)
    )
    for source in video_sources.scalars().all():
        if source.audio_path:
            audio_path = Path(source.audio_path)
            if audio_path.exists():
                audio_path.unlink()
                deleted_files.append((str(audio_path), "audio"))
                source.audio_path = None
                session.add(source)

    for file_path, file_type in deleted_files:
        log = GarbageCollectionLog(
            project_id=project.id,
            file_path=file_path,
            file_type=file_type,
            reason="project_status_completed",
        )
        session.add(log)

    await session.commit()
    logger.info(
        "Garbage collection selesai: project=%s deleted=%s",
        project.id,
        len(deleted_files),
    )
