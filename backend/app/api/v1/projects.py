import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models.analysis_result import AnalysisResult
from app.db.models.clip import Clip
from app.db.models.highlight_moment import HighlightMoment
from app.db.models.project import Project
from app.db.models.subtitle_style import SubtitleStyle
from app.db.models.transcript import Transcript
from app.db.models.video_source import VideoSource
from app.db.session import get_db_session
from app.jobs.queue import enqueue_job
from app.schemas.job import JobAcceptedResponse
from app.schemas.project import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    VideoSourceResponse,
)
from app.services.youtube import download_youtube_video, is_valid_youtube_url

logger = logging.getLogger(__name__)

ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".mpg", ".mpeg"}


router = APIRouter()


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    payload: ProjectCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ProjectResponse:
    """Buat proyek baru dan folder output yang sesuai."""
    settings = get_settings()
    slug = payload.slugify_title()
    base_folder = settings.storage_root / "projects" / slug
    folder_path = base_folder

    counter = 1
    while True:
        existing = await session.execute(
            select(Project).where(Project.folder_path == str(folder_path))
        )
        if existing.scalar_one_or_none() is None:
            break
        folder_path = settings.storage_root / "projects" / f"{slug}-{counter}"
        counter += 1

    folder_path.mkdir(parents=True, exist_ok=True)

    project = Project(
        title=payload.title.strip(),
        folder_path=str(folder_path),
        source_type=payload.source_type,
        source_url=payload.source_url,
        original_filename=payload.original_filename,
    )
    session.add(project)
    try:
        await session.commit()
        await session.refresh(project)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Proyek dengan judul tersebut sudah ada.",
        )

    logger.info(
        "Proyek dibuat: id=%s title=%s folder=%s",
        project.id,
        project.title,
        project.folder_path,
    )
    return ProjectResponse.model_validate(project)


@router.post("/{project_id}/upload", response_model=VideoSourceResponse, status_code=201)
async def upload_video(
    project_id: int,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
) -> VideoSourceResponse:
    """Unggah video sumber ke dalam proyek."""
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan.")

    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        supported = ", ".join(sorted(ALLOWED_VIDEO_EXTENSIONS))
        raise HTTPException(
            status_code=422,
            detail=f"Format file tidak didukung. Gunakan: {supported}",
        )

    existing_source = await session.execute(
        select(VideoSource).where(VideoSource.project_id == project_id)
    )
    existing = existing_source.scalar_one_or_none()
    if existing:
        old_path = Path(existing.file_path)
        if old_path.exists():
            old_path.unlink()
        await session.delete(existing)
        await session.flush()

    safe_filename = f"{uuid.uuid4().hex}{ext}"
    destination = Path(project.folder_path) / safe_filename
    destination.parent.mkdir(parents=True, exist_ok=True)

    try:
        with destination.open("wb") as buffer:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                buffer.write(chunk)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan file: {exc}") from exc
    finally:
        await file.close()

    video_source = VideoSource(
        project_id=project.id,
        file_path=str(destination),
    )
    session.add(video_source)
    await session.commit()
    await session.refresh(video_source)

    logger.info(
        "Video diunggah: project=%s file=%s size=%s",
        project_id,
        destination.name,
        destination.stat().st_size,
    )
    return VideoSourceResponse.model_validate(video_source)


@router.post("/{project_id}/download-youtube", response_model=VideoSourceResponse, status_code=201)
async def download_youtube(
    project_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> VideoSourceResponse:
    """Unduh video YouTube ke dalam proyek menggunakan yt-dlp."""
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan.")

    if project.source_type != "youtube":
        raise HTTPException(
            status_code=422,
            detail="Proyek ini bukan sumber YouTube.",
        )

    youtube_url = project.source_url
    if not youtube_url or not is_valid_youtube_url(youtube_url):
        raise HTTPException(
            status_code=422,
            detail="URL YouTube tidak valid.",
        )

    existing_source = await session.execute(
        select(VideoSource).where(VideoSource.project_id == project_id)
    )
    existing = existing_source.scalar_one_or_none()
    if existing:
        old_path = Path(existing.file_path)
        if old_path.exists():
            old_path.unlink()
        await session.delete(existing)
        await session.flush()

    try:
        metadata = download_youtube_video(youtube_url, Path(project.folder_path))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Gagal mengunduh video: {exc}",
        ) from exc

    downloaded_path = Path(metadata["file_path"])
    if not downloaded_path.exists():
        raise HTTPException(
            status_code=500,
            detail="File video tidak ditemukan setelah unduhan.",
        )

    video_source = VideoSource(
        project_id=project.id,
        file_path=str(downloaded_path),
        resolution=metadata.get("resolution"),
        duration_seconds=metadata.get("duration"),
        fps=metadata.get("fps"),
    )
    session.add(video_source)
    await session.commit()
    await session.refresh(video_source)

    logger.info(
        "YouTube diunduh: project=%s url=%s file=%s",
        project_id,
        youtube_url,
        downloaded_path.name,
    )
    return VideoSourceResponse.model_validate(video_source)


@router.post("/{project_id}/extract-audio", response_model=JobAcceptedResponse, status_code=202)
async def extract_audio(
    project_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> JobAcceptedResponse:
    """Ekstrak audio dari video sumber proyek."""
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan.")

    video_source = await session.execute(
        select(VideoSource).where(VideoSource.project_id == project_id)
    )
    if video_source.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=422,
            detail="Video sumber belum diunggah.",
        )

    job = await enqueue_job(session, project_id, "ffmpeg_extract_audio", priority=20)
    return JobAcceptedResponse(job_id=job.id)


@router.post("/{project_id}/transcribe", response_model=JobAcceptedResponse, status_code=202)
async def transcribe_project(
    project_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> JobAcceptedResponse:
    """Antrikan job transkripsi Whisper untuk proyek."""
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan.")

    video_source = await session.execute(
        select(VideoSource).where(VideoSource.project_id == project_id)
    )
    if video_source.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=422,
            detail="Video sumber belum diunggah.",
        )

    job = await enqueue_job(session, project_id, "whisper_transcribe", priority=10)
    return JobAcceptedResponse(job_id=job.id)


@router.post("/{project_id}/analyze", response_model=JobAcceptedResponse, status_code=202)
async def analyze_project(
    project_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> JobAcceptedResponse:
    """Antrikan job analisis LLM untuk proyek."""
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan.")

    transcript = await session.execute(
        select(Transcript).where(Transcript.project_id == project_id)
    )
    if transcript.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=422,
            detail="Transkrip belum tersedia. Jalankan transkripsi terlebih dahulu.",
        )

    job = await enqueue_job(session, project_id, "ollama_analyze", priority=5)
    return JobAcceptedResponse(job_id=job.id)


@router.post("/{project_id}/render", response_model=JobAcceptedResponse, status_code=202)
async def render_project(
    project_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> JobAcceptedResponse:
    """Buat klip dari highlight moments dan antrikan rendering."""
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan.")

    analysis = await session.execute(
        select(AnalysisResult).where(AnalysisResult.project_id == project_id)
    )
    if analysis.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=422,
            detail="Analisis belum tersedia. Jalankan analisis terlebih dahulu.",
        )

    moments_result = await session.execute(
        select(HighlightMoment)
        .where(HighlightMoment.analysis_id == analysis.scalar_one().id)
        .where(HighlightMoment.status == "pending")
    )
    moments = moments_result.scalars().all()
    if not moments:
        raise HTTPException(
            status_code=422,
            detail="Tidak ada highlight moment yang perlu dirender.",
        )

    created_clips = 0
    for moment in moments:
        existing_clip = await session.execute(
            select(Clip).where(Clip.highlight_moment_id == moment.id)
        )
        if existing_clip.scalar_one_or_none() is not None:
            continue

        clip = Clip(
            project_id=project.id,
            highlight_moment_id=moment.id,
            aspect_ratio="9:16",
            crop_mode="center_crop_static",
            render_status="queued",
        )
        session.add(clip)
        await session.flush()

        subtitle_style = SubtitleStyle(clip_id=clip.id)
        session.add(subtitle_style)
        created_clips += 1

    await session.commit()

    if created_clips == 0:
        raise HTTPException(
            status_code=422,
            detail="Semua klip sudah memiliki rendering.",
        )

    job = await enqueue_job(session, project_id, "render_clip", priority=1)
    return JobAcceptedResponse(job_id=job.id)


@router.post("/{project_id}/broll", response_model=JobAcceptedResponse, status_code=202)
async def search_broll(
    project_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> JobAcceptedResponse:
    """Cari b-roll assets untuk klip dalam proyek."""
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan.")

    clips = await session.execute(
        select(Clip).where(Clip.project_id == project_id)
    )
    if clips.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=422,
            detail="Klip belum tersedia. Jalankan rendering terlebih dahulu.",
        )

    job = await enqueue_job(session, project_id, "broll_search", priority=2)
    return JobAcceptedResponse(job_id=job.id)


@router.post("/{project_id}/gc", response_model=JobAcceptedResponse, status_code=202)
async def garbage_collect_project(
    project_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> JobAcceptedResponse:
    """Bersihkan file temporary untuk proyek yang sudah selesai."""
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan.")

    job = await enqueue_job(session, project_id, "garbage_collect", priority=0)
    return JobAcceptedResponse(job_id=job.id)


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    session: AsyncSession = Depends(get_db_session),
) -> ProjectListResponse:
    """Daftar semua proyek."""
    count_result = await session.execute(select(func.count()).select_from(Project))
    total = count_result.scalar_one()

    result = await session.execute(select(Project).order_by(Project.created_at.desc()))
    projects = result.scalars().all()

    return ProjectListResponse(
        items=[ProjectResponse.model_validate(p) for p in projects],
        total=total,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> ProjectResponse:
    """Detail satu proyek."""
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan.")
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> None:
    """Hapus proyek dan file terkait."""
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan.")

    folder = Path(project.folder_path)
    if folder.exists():
        import shutil

        shutil.rmtree(folder, ignore_errors=True)

    await session.delete(project)
    await session.commit()
