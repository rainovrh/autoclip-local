"""Worker: analisis highlight via Ollama."""

import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.analysis_result import AnalysisResult
from app.db.models.highlight_moment import HighlightMoment
from app.db.models.processing_job import ProcessingJob
from app.db.models.project import Project
from app.db.models.transcript import Transcript
from app.db.models.transcript_segment import TranscriptSegment
from app.services.analysis import HighlightMomentDTO, OllamaAnalysisService

logger = logging.getLogger(__name__)


async def run_ollama_analyze(session: AsyncSession, job: ProcessingJob) -> None:
    """Analisis transkrip dan ekstraksi momen menarik (Anti-Halusinasi)."""
    logger.info("Memulai ollama_analyze untuk job %s", job.id)

    project = await session.get(Project, job.project_id)
    if project is None:
        raise ValueError(f"Project {job.project_id} tidak ditemukan.")

    transcript = await session.execute(
        select(Transcript)
        .where(Transcript.project_id == project.id)
        .order_by(Transcript.id.asc())
    )
    transcript_row = transcript.scalar_one_or_none()
    if transcript_row is None:
        raise ValueError("Transkrip belum tersedia untuk proyek ini.")

    segments_result = await session.execute(
        select(TranscriptSegment)
        .where(TranscriptSegment.transcript_id == transcript_row.id)
        .order_by(TranscriptSegment.segment_index.asc())
    )
    segments = segments_result.scalars().all()
    if not segments:
        raise ValueError("Tidak ada segmen transkrip untuk dianalisis.")

    dto_segments = [
        HighlightMomentDTO(start_segment_id=s.id, end_segment_id=s.id)
        for s in segments
    ]
    # Reuse DTO as data carrier for prompt building
    dto_segments = [
        type("TranscriptSegmentDTO", (), {"segment_id": s.id, "text": s.text})()
        for s in segments
    ]

    service = OllamaAnalysisService()
    try:
        moments = await service.analyze(dto_segments)
    except Exception as exc:
        raise ValueError(f"Gagal menganalisis transkrip: {exc}") from exc

    if not moments:
        logger.warning("Tidak ada momen highlight yang diekstrak untuk project %s", project.id)

    analysis = AnalysisResult(
        project_id=project.id,
        llm_model=service.model_name,
        raw_json_output=json.dumps(
            [
                {
                    "start_segment_id": m.start_segment_id,
                    "end_segment_id": m.end_segment_id,
                    "suggested_duration_seconds": m.suggested_duration_seconds,
                    "engagement_reason": m.engagement_reason,
                    "engagement_score": m.engagement_score,
                }
                for m in moments
            ]
        ),
    )
    session.add(analysis)
    await session.flush()

    for moment in moments:
        highlight = HighlightMoment(
            analysis_id=analysis.id,
            start_segment_id=moment.start_segment_id,
            end_segment_id=moment.end_segment_id,
            suggested_duration_seconds=moment.suggested_duration_seconds,
            engagement_reason=moment.engagement_reason,
            engagement_score=moment.engagement_score,
        )
        session.add(highlight)

    project.status = "ANALYZED"
    session.add(project)
    await session.commit()

    logger.info(
        "Analisis selesai: project=%s moments=%s model=%s",
        project.id,
        len(moments),
        service.model_name,
    )
