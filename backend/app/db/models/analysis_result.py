from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    llm_model: Mapped[str] = mapped_column(String, nullable=False)
    raw_json_output: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    project: Mapped["Project"] = relationship(back_populates="analysis_results")
    highlight_moments: Mapped[list["HighlightMoment"]] = relationship(
        back_populates="analysis"
    )


from app.db.models.highlight_moment import HighlightMoment  # noqa: E402
from app.db.models.project import Project  # noqa: E402
