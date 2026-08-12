import logging

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.project import Project
from app.db.session import get_db_session
from app.schemas.project import ProjectListResponse, ProjectResponse

logger = logging.getLogger(__name__)

router = APIRouter()


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
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan.")
    return ProjectResponse.model_validate(project)
