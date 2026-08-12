import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.clip import Clip
from app.db.session import get_db_session
from app.schemas.clip import ClipResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=list[ClipResponse])
async def list_clips(
    project_id: int | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> list[ClipResponse]:
    """Daftar klip, opsional difilter per proyek."""
    query = select(Clip).order_by(Clip.created_at.desc())
    if project_id is not None:
        query = query.where(Clip.project_id == project_id)

    result = await session.execute(query)
    clips = result.scalars().all()
    return [ClipResponse.model_validate(c) for c in clips]


@router.get("/{clip_id}", response_model=ClipResponse)
async def get_clip(
    clip_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> ClipResponse:
    """Detail satu klip."""
    clip = await session.get(Clip, clip_id)
    if clip is None:
        raise HTTPException(status_code=404, detail="Klip tidak ditemukan.")
    return ClipResponse.model_validate(clip)
