"""Worker: analisis highlight via Ollama."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.processing_job import ProcessingJob

logger = logging.getLogger(__name__)


async def run_ollama_analyze(session: AsyncSession, job: ProcessingJob) -> None:
    """Analisis transkrip dan ekstraksi momen menarik (Anti-Halusinasi)."""
    logger.info("Memulai ollama_analyze untuk job %s", job.id)
    # TODO: implementasi Ollama + validasi JSON
    raise NotImplementedError("Worker ollama_analyze belum diimplementasi.")
