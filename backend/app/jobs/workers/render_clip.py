"""Worker: render klip final (crop, subtitle, b-roll overlay)."""

import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.broll_asset import BrollAsset
from app.db.models.clip import Clip
from app.db.models.highlight_moment import HighlightMoment
from app.db.models.processing_job import ProcessingJob
from app.db.models.project import Project
from app.db.models.subtitle_style import SubtitleStyle
from app.db.models.transcript_segment import TranscriptSegment
from app.db.models.transcript_word import TranscriptWord
from app.db.models.video_source import VideoSource
from app.services.rendering import rendering_service

logger = logging.getLogger(__name__)


async def run_render_clip(session: AsyncSession, job: ProcessingJob) -> None:
    """Render klip vertikal dengan subtitle dan opsional b-roll."""
    logger.info("Memulai render_clip untuk job %s", job.id)

    clips_result = await session.execute(
        select(Clip)
        .where(Clip.project_id == job.project_id)
        .where(Clip.render_status == "queued")
    )
    clips = clips_result.scalars().all()
    if not clips:
        logger.info("Tidak ada klip yang perlu dirender untuk project %s", job.project_id)
        return

    for clip in clips:
        try:
            await _render_single_clip(session, clip)
        except Exception as exc:
            logger.error("Gagal rendering clip %s: %s", clip.id, exc, exc_info=True)
            clip.render_status = "failed"
            clip.render_error_message = str(exc)
            session.add(clip)
            await session.commit()

    logger.info(
        "Render selesai untuk job %s: %s klip diproses",
        job.id,
        len(clips),
    )


async def _render_single_clip(session: AsyncSession, clip: Clip) -> None:
    """Render satu klip dan update statusnya."""
    project = await session.get(Project, clip.project_id)
    if project is None:
        raise ValueError(f"Project {clip.project_id} tidak ditemukan.")

    video_source = await session.execute(
        select(VideoSource).where(VideoSource.project_id == project.id)
    )
    source = video_source.scalar_one_or_none()
    if source is None:
        raise ValueError("Video sumber belum diunggah.")

    highlight = await session.get(HighlightMoment, clip.highlight_moment_id)
    if highlight is None:
        raise ValueError("Highlight moment tidak ditemukan.")

    start_segment = await session.get(TranscriptSegment, highlight.start_segment_id)
    end_segment = await session.get(TranscriptSegment, highlight.end_segment_id)
    if start_segment is None or end_segment is None:
        raise ValueError("Segmen transkrip untuk highlight tidak ditemukan.")

    start_time = start_segment.start_time
    end_time = end_segment.end_time

    subtitle_words = None
    subtitle_style = await session.execute(
        select(SubtitleStyle).where(SubtitleStyle.clip_id == clip.id)
    )
    style_row = subtitle_style.scalar_one_or_none()
    if style_row and style_row.display_mode == "word_by_word":
        words_result = await session.execute(
            select(TranscriptWord)
            .where(TranscriptWord.segment_id == start_segment.id)
            .order_by(TranscriptWord.word_index.asc())
        )
        words = words_result.scalars().all()
        subtitle_words = [
            (w.word, w.start_time - start_time, w.end_time - start_time)
            for w in words
            if w.start_time >= start_time and w.end_time <= end_time
        ]

    broll_paths = []
    broll_timings = []
    brolls = await session.execute(
        select(BrollAsset)
        .where(BrollAsset.clip_id == clip.id)
        .where(BrollAsset.status == "success")
    )
    for broll in brolls.scalars().all():
        if broll.local_cache_path and Path(broll.local_cache_path).exists():
            broll_paths.append(broll.local_cache_path)
            broll_timings.append(
                (
                    broll.overlay_start_time or 0,
                    broll.overlay_end_time or (end_time - start_time),
                )
            )

    output_filename = f"clip-{clip.id}-{project.id}.mp4"
    output_path = Path(project.folder_path) / "output" / output_filename

    try:
        metadata = rendering_service.render_clip(
            source_path=source.file_path,
            output_path=output_path,
            start=start_time,
            end=end_time,
            aspect_ratio=clip.aspect_ratio,
            subtitle_words=subtitle_words,
            broll_paths=broll_paths,
            broll_timings=broll_timings,
        )
    except Exception as exc:
        clip.render_status = "failed"
        clip.render_error_message = str(exc)
        session.add(clip)
        await session.commit()
        raise

    clip.output_path = metadata["output_path"]
    clip.resolution = metadata["resolution"]
    clip.duration_seconds = metadata["duration_seconds"]
    clip.render_status = "completed"
    session.add(clip)
    await session.commit()

    logger.info(
        "Render selesai: clip=%s output=%s resolution=%s duration=%.2f",
        clip.id,
        clip.output_path,
        clip.resolution,
        clip.duration_seconds or 0,
    )
