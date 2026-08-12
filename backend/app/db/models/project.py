from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    folder_path: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    original_filename: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, nullable=False, default="UPLOADED")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    video_source: Mapped["VideoSource | None"] = relationship(
        back_populates="project", uselist=False, passive_deletes=True
    )
    transcript: Mapped["Transcript | None"] = relationship(
        back_populates="project", uselist=False, passive_deletes=True
    )
    analysis_results: Mapped[list["AnalysisResult"]] = relationship(
        back_populates="project", passive_deletes=True
    )
    clips: Mapped[list["Clip"]] = relationship(
        back_populates="project", passive_deletes=True
    )
    processing_jobs: Mapped[list["ProcessingJob"]] = relationship(
        back_populates="project", passive_deletes=True
    )
    garbage_collection_logs: Mapped[list["GarbageCollectionLog"]] = relationship(
        back_populates="project", passive_deletes=True
    )


from app.db.models.analysis_result import AnalysisResult  # noqa: E402
from app.db.models.clip import Clip  # noqa: E402
from app.db.models.garbage_collection_log import GarbageCollectionLog  # noqa: E402
from app.db.models.processing_job import ProcessingJob  # noqa: E402
from app.db.models.transcript import Transcript  # noqa: E402
from app.db.models.video_source import VideoSource  # noqa: E402
