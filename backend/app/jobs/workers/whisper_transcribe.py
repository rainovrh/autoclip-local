"""Worker: transkripsi via faster-whisper."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.processing_job import ProcessingJob
from app.db.models.project import Project
from app.db.models.transcript import Transcript
from app.db.models.transcript_segment import TranscriptSegment
from app.db.models.transcript_word import TranscriptWord
from app.db.models.video_source import VideoSource
from app.services.transcription import WhisperTranscriptionService

logger = logging.getLogger(__name__)


async def run_whisper_transcribe(session: AsyncSession, job: ProcessingJob) -> None:
    """Transkripsi audio dengan word-level timestamps."""
    logger.info("Memulai whisper_transcribe untuk job %s", job.id)

    project = await session.get(Project, job.project_id)
    if project is None:
        raise ValueError(f"Project {job.project_id} tidak ditemukan.")

    video_source = await session.execute(
        VideoSource.__table__.select().where(VideoSource.project_id == project.id)
    )
    source = video_source.fetchone()
    if source is None:
        raise ValueError("Video sumber belum diunggah.")

    file_path = source.file_path
    if not file_path:
        raise ValueError("Path video sumber kosong.")

    service = WhisperTranscriptionService()
    try:
        result = service.transcribe(file_path)
    finally:
        service.unload()

    transcript = Transcript(
        project_id=project.id,
        full_text=result.text,
        language=result.language,
        whisper_model=service.model_name,
    )
    session.add(transcript)
    await session.flush()

    for segment in result.segments:
        transcript_segment = TranscriptSegment(
            transcript_id=transcript.id,
            segment_index=segment.index,
            start_time=segment.start,
            end_time=segment.end,
            text=segment.text,
        )
        session.add(transcript_segment)
        await session.flush()

        for word_idx, word in enumerate(segment.words):
            transcript_word = TranscriptWord(
                segment_id=transcript_segment.id,
                word_index=word_idx,
                word=word.word,
                start_time=word.start,
                end_time=word.end,
                confidence=word.probability,
            )
            session.add(transcript_word)

    project.status = "TRANSCRIBED"
    session.add(project)
    await session.commit()

    logger.info(
        "Transkripsi selesai: project=%s segments=%s words=%s",
        project.id,
        len(result.segments),
        sum(len(s.words) for s in result.segments),
    )
