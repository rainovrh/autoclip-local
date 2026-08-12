"""Worker: transkripsi via faster-whisper."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.processing_job import ProcessingJob

logger = logging.getLogger(__name__)


async def run_whisper_transcribe(session: AsyncSession, job: ProcessingJob) -> None:
    """Transkripsi audio dengan word-level timestamps."""
    logger.info("Memulai whisper_transcribe untuk job %s", job.id)
    # TODO: implementasi faster-whisper
    raise NotImplementedError("Worker whisper_transcribe belum diimplementasi.")
