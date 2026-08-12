import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.processing_job import ProcessingJob
from app.db.session import get_db_session
from app.schemas.job import JobResponse

logger = logging.getLogger(__name__)

router = APIRouter()


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
