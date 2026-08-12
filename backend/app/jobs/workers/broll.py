"""Worker: cari dan unduh b-roll assets untuk klip."""

import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models.broll_asset import BrollAsset
from app.db.models.clip import Clip
from app.db.models.highlight_moment import HighlightMoment
from app.db.models.processing_job import ProcessingJob
from app.db.models.transcript_segment import TranscriptSegment
from app.services.broll import pexels_client

logger = logging.getLogger(__name__)


def _extract_keywords_from_moment(highlight: HighlightMoment, segment_text: str) -> str:
    """Ekstrak kata kunci dari teks segmen untuk pencarian b-roll."""
    words = segment_text.split()
    keywords = " ".join(words[:8])
    return keywords.strip() or "video"


async def run_broll_search(session: AsyncSession, job: ProcessingJob) -> None:
    """Cari b-roll assets untuk klip yang belum memiliki b-roll."""
    logger.info("Memulai broll_search untuk job %s", job.id)

    clips_result = await session.execute(
        select(Clip)
        .where(Clip.project_id == job.project_id)
        .where(Clip.render_status != "completed")
    )
    clips = clips_result.scalars().all()

    if not clips:
        logger.info("Tidak ada klip yang perlu diproses untuk project %s", job.project_id)
        return

    settings = get_settings()
    broll_root = Path(settings.assets_root) / "broll" / str(job.project_id)
    broll_root.mkdir(parents=True, exist_ok=True)

    processed = 0
    for clip in clips:
        brolls = await session.execute(
            select(BrollAsset).where(BrollAsset.clip_id == clip.id)
        )
        if brolls.scalar_one_or_none() is not None:
            continue

        highlight = await session.get(HighlightMoment, clip.highlight_moment_id)
        if highlight is None:
            continue

        start_segment = await session.get(TranscriptSegment, highlight.start_segment_id)
        if start_segment is None:
            continue

        query = _extract_keywords_from_moment(highlight, start_segment.text)
        search_result = await pexels_client.search_video(query)

        broll_asset = BrollAsset(
            clip_id=clip.id,
            source_segment_id=start_segment.id,
            pexels_query=query,
            pexels_video_url=search_result.video_url,
            status=search_result.status,
        )
        session.add(broll_asset)
        await session.flush()

        if search_result.status == "found" and search_result.video_url:
            ext = ".mp4"
            destination = broll_root / f"broll-{broll_asset.id}{ext}"
            local_path = await pexels_client.download_video(
                search_result.video_url, destination
            )
            if local_path:
                broll_asset.local_cache_path = local_path
                broll_asset.status = "success"
            else:
                broll_asset.status = "failed"
                broll_asset.render_error_message = "Gagal mengunduh video."
        else:
            broll_asset.render_error_message = search_result.error

        session.add(broll_asset)
        await session.commit()
        processed += 1

    logger.info(
        "B-roll search selesai untuk job %s: %s klip diproses",
        job.id,
        processed,
    )
