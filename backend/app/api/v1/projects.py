import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models.project import Project
from app.db.session import get_db_session
from app.schemas.project import ProjectCreate, ProjectListResponse, ProjectResponse

logger = logging.getLogger(__name__)

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
