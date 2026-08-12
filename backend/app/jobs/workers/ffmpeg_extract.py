"""Worker: ekstraksi audio via FFmpeg."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.processing_job import ProcessingJob

logger = logging.getLogger(__name__)


async def run_ffmpeg_extract(session: AsyncSession, job: ProcessingJob) -> None:
    """Ekstrak audio .wav dari video sumber proyek."""
    logger.info("Memulai ffmpeg_extract untuk job %s", job.id)
    # TODO: implementasi FFmpeg extract audio
    raise NotImplementedError("Worker ffmpeg_extract belum diimplementasi.")
