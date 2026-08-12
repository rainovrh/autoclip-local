import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.processing_job import ProcessingJob
from app.db.session import get_db_session
from app.schemas.job import JobResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=list[JobResponse])
async def list_jobs(
    project_id: int | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> list[JobResponse]:
    """Daftar semua job, opsional difilter per proyek."""
    query = select(ProcessingJob).order_by(ProcessingJob.created_at.desc())
    if project_id is not None:
        query = query.where(ProcessingJob.project_id == project_id)

    result = await session.execute(query)
    jobs = result.scalars().all()
    return [JobResponse.model_validate(j) for j in jobs]


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> JobResponse:
    """Status satu job pemrosesan."""
    job = await session.get(ProcessingJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job tidak ditemukan.")
    return JobResponse.model_validate(job)
