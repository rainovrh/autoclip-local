import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.clip import Clip
from app.db.models.subtitle_style import SubtitleStyle
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


@router.put("/{clip_id}/subtitle-style")
async def update_subtitle_style(
    clip_id: int,
    style: dict,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Update gaya subtitle untuk klip."""
    clip = await session.get(Clip, clip_id)
    if clip is None:
        raise HTTPException(status_code=404, detail="Klip tidak ditemukan.")

    subtitle_style = await session.execute(
        select(SubtitleStyle).where(SubtitleStyle.clip_id == clip_id)
    )
    style_row = subtitle_style.scalar_one_or_none()
    if style_row is None:
        style_row = SubtitleStyle(clip_id=clip_id)
        session.add(style_row)

    allowed_fields = {
        "display_mode",
        "font_family",
        "font_size",
        "font_weight",
        "is_uppercase",
        "text_color",
        "highlight_color",
        "background_color",
        "background_opacity",
    }
    for key, value in style.items():
        if key in allowed_fields and hasattr(style_row, key):
            setattr(style_row, key, value)

    session.add(style_row)
    await session.commit()
    await session.refresh(style_row)

    return {
        "id": style_row.id,
        "clip_id": style_row.clip_id,
        "display_mode": style_row.display_mode,
        "font_family": style_row.font_family,
        "font_size": style_row.font_size,
        "font_weight": style_row.font_weight,
        "is_uppercase": style_row.is_uppercase,
        "text_color": style_row.text_color,
        "highlight_color": style_row.highlight_color,
        "background_color": style_row.background_color,
        "background_opacity": style_row.background_opacity,
    }

