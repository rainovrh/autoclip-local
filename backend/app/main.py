from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import clips, jobs, projects, settings
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    await init_db()
    yield


def create_app() -> FastAPI:
    app_settings = get_settings()

    app = FastAPI(
        title="AutoClip Local",
        description="Aplikasi web lokal untuk memotong video panjang menjadi klip vertikal.",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
    app.include_router(clips.router, prefix="/api/v1/clips", tags=["clips"])
    app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
    app.include_router(settings.router, prefix="/api/v1/settings", tags=["settings"])

    return app


app = create_app()
