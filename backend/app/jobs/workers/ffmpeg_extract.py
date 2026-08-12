"""Worker: ekstraksi audio via FFmpeg."""

import logging
from pathlib import Path

import ffmpeg
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.processing_job import ProcessingJob
from app.db.models.project import Project
from app.db.models.video_source import VideoSource

logger = logging.getLogger(__name__)


async def run_ffmpeg_extract(session: AsyncSession, job: ProcessingJob) -> None:
    """Ekstrak audio .wav dari video sumber proyek."""
    logger.info("Memulai ffmpeg_extract untuk job %s", job.id)

    project = await session.get(Project, job.project_id)
    if project is None:
        raise ValueError(f"Project {job.project_id} tidak ditemukan.")

    video_source = await session.execute(
        select(VideoSource).where(VideoSource.project_id == project.id)
    )
    source = video_source.scalar_one_or_none()
    if source is None:
        raise ValueError("Video sumber belum diunggah.")

    input_path = Path(source.file_path)
    if not input_path.exists():
        raise ValueError(f"File video tidak ditemukan: {input_path}")

    output_path = input_path.with_suffix(".wav")
    output_path = Path(project.folder_path) / f"audio-{source.id}.wav"

    try:
        (
            ffmpeg.input(str(input_path))
            .output(
                str(output_path),
                format="wav",
                acodec="pcm_s16le",
                ac=1,
                ar="16000",
                loglevel="error",
            )
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as exc:
        stderr = exc.stderr.decode("utf-8", errors="replace") if exc.stderr else ""
        raise RuntimeError(f"FFmpeg gagal: {stderr}") from exc

    if not output_path.exists():
        raise RuntimeError("File audio tidak berhasil dibuat.")

    source.audio_path = str(output_path)
    session.add(source)

    project.status = "AUDIO_EXTRACTED"
    session.add(project)
    await session.commit()

    logger.info(
        "Audio diekstrak: project=%s audio=%s",
        project.id,
        output_path.name,
    )

