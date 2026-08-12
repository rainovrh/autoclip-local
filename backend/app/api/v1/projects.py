import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models.project import Project
from app.db.models.video_source import VideoSource
from app.db.session import get_db_session
from app.schemas.project import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    VideoSourceResponse,
)

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
