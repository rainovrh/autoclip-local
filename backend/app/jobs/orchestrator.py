"""Worker orchestration service for processing jobs."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Awaitable, Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models.processing_job import ProcessingJob
from app.jobs.queue import get_next_queued_job, mark_job_failed, mark_job_running
from app.jobs.workers.broll import run_broll_search
from app.jobs.workers.ffmpeg_extract import run_ffmpeg_extract
from app.jobs.workers.garbage_collect import run_garbage_collect
from app.jobs.workers.ollama_analyze import run_ollama_analyze
from app.jobs.workers.render_clip import run_render_clip
from app.jobs.workers.whisper_transcribe import run_whisper_transcribe
from app.services.webhooks import send_webhook_notification

logger = logging.getLogger(__name__)

UTC = timezone.utc

WORKER_REGISTRY: dict[str, Callable[[AsyncSession, ProcessingJob], Awaitable[None]]] = {
    "ffmpeg_extract_audio": run_ffmpeg_extract,
    "whisper_transcribe": run_whisper_transcribe,
    "ollama_analyze": run_ollama_analyze,
    "render_clip": run_render_clip,
    "broll_search": run_broll_search,
    "garbage_collect": run_garbage_collect,
}


async def process_job(session: AsyncSession, job: ProcessingJob) -> None:
    """Execute a single job using the appropriate worker."""
    worker = WORKER_REGISTRY.get(job.job_type)
    if worker is None:
        raise ValueError(f"Unknown job type: {job.job_type}")

    await mark_job_running(session, job)
    try:
        await worker(session, job)
        await session.refresh(job)
        if job.status != "failed":
            job.status = "completed"
            job.finished_at = datetime.now(UTC)
            session.add(job)
            await session.commit()
            logger.info("Job %s completed successfully", job.id)
            await send_webhook_notification(job, "completed")
    except Exception as exc:
        error_msg = str(exc)
        await mark_job_failed(session, job, error_msg)
        await session.refresh(job)
        await send_webhook_notification(job, "failed", error_msg)
        raise


async def run_worker_loop(stop_event: asyncio.Event | None = None) -> None:
    """Main worker loop that continuously polls for and processes jobs."""
    from app.db.session import get_db_session

    settings = get_settings()
    poll_interval = settings.worker_poll_interval

    logger.info("Worker loop started with poll interval %.1fs", poll_interval)

    while True:
        if stop_event is not None and stop_event.is_set():
            logger.info("Worker loop stopping...")
            break

        try:
            async for session in get_db_session():
                job = await get_next_queued_job(session)
                if job is None:
                    await session.close()
                    await asyncio.sleep(poll_interval)
                    continue

                if job.scheduled_at and job.scheduled_at > datetime.now(UTC):
                    await session.close()
                    await asyncio.sleep(poll_interval)
                    continue

                logger.info("Processing job %s (%s)", job.id, job.job_type)
                try:
                    await process_job(session, job)
                except Exception as exc:
                    logger.error("Job %s failed: %s", job.id, exc)
                    if job.retry_count < job.max_retries:
                        job.retry_count += 1
                        job.status = "queued"
                        job.error_message = None
                        session.add(job)
                        await session.commit()
                        logger.info(
                            "Job %s requeued (attempt %s/%s)",
                            job.id,
                            job.retry_count,
                            job.max_retries,
                        )
                    else:
                        logger.error(
                            "Job %s failed permanently after %s retries",
                            job.id,
                            job.retry_count,
                        )

                await session.close()

        except Exception as exc:
            logger.error("Worker loop error: %s", exc, exc_info=True)
            await asyncio.sleep(poll_interval)


async def enqueue_scheduled_jobs() -> None:
    """Check for scheduled jobs that are ready to run."""
    from app.db.session import get_db_session

    async for session in get_db_session():
        result = await session.execute(
            select(ProcessingJob)
            .where(ProcessingJob.status == "queued")
            .where(ProcessingJob.scheduled_at.is_not(None))
            .where(ProcessingJob.scheduled_at <= datetime.now(UTC))
        )
        jobs = result.scalars().all()

        for job in jobs:
            job.scheduled_at = None
            session.add(job)

        if jobs:
            await session.commit()
            logger.info("Activated %s scheduled jobs", len(jobs))

        break
