import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import JobType
from app.db.models.processing_job import ProcessingJob

logger = logging.getLogger(__name__)


async def enqueue_job(
    session: AsyncSession,
    project_id: int,
    job_type: JobType,
    priority: int = 0,
) -> ProcessingJob:
    """Daftarkan job baru ke antrean processing_jobs."""
    job = ProcessingJob(
        project_id=project_id,
        job_type=job_type,
        status="queued",
        priority=priority,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    logger.info("Job %s (%s) didaftarkan untuk proyek %s", job.id, job_type, project_id)
    return job


async def get_next_queued_job(session: AsyncSession) -> ProcessingJob | None:
    """Ambil job berikutnya yang siap dijalankan (FIFO + priority)."""
    result = await session.execute(
        select(ProcessingJob)
        .where(ProcessingJob.status == "queued")
        .order_by(ProcessingJob.priority.desc(), ProcessingJob.created_at.asc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def mark_job_running(session: AsyncSession, job: ProcessingJob) -> None:
    job.status = "running"
    job.started_at = datetime.now(UTC)
    await session.commit()


async def mark_job_completed(session: AsyncSession, job: ProcessingJob) -> None:
    job.status = "completed"
    job.finished_at = datetime.now(UTC)
    await session.commit()
    logger.info("Job %s selesai.", job.id)


async def mark_job_failed(
    session: AsyncSession, job: ProcessingJob, error_message: str
) -> None:
    job.status = "failed"
    job.finished_at = datetime.now(UTC)
    job.error_message = error_message
    await session.commit()
    logger.error("Job %s gagal: %s", job.id, error_message)
