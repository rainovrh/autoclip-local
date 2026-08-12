"""Worker: render klip final (crop, subtitle, b-roll overlay)."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.processing_job import ProcessingJob

logger = logging.getLogger(__name__)


async def run_render_clip(session: AsyncSession, job: ProcessingJob) -> None:
    """Render klip vertikal dengan subtitle dan opsional b-roll."""
    logger.info("Memulai render_clip untuk job %s", job.id)
    # TODO: implementasi pipeline rendering
    raise NotImplementedError("Worker render_clip belum diimplementasi.")
