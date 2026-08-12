from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base


class HighlightMoment(Base):
    __tablename__ = "highlight_moments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    analysis_id: Mapped[int] = mapped_column(
        ForeignKey("analysis_results.id", ondelete="CASCADE"), nullable=False
    )
    start_segment_id: Mapped[int] = mapped_column(
        ForeignKey("transcript_segments.id"), nullable=False
    )
    end_segment_id: Mapped[int] = mapped_column(
        ForeignKey("transcript_segments.id"), nullable=False
    )
    start_word_id: Mapped[int | None] = mapped_column(
        ForeignKey("transcript_words.id")
    )
    end_word_id: Mapped[int | None] = mapped_column(ForeignKey("transcript_words.id"))
    suggested_duration_seconds: Mapped[float | None] = mapped_column(Float)
    engagement_reason: Mapped[str | None] = mapped_column(Text)
    engagement_score: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    analysis: Mapped["AnalysisResult"] = relationship(back_populates="highlight_moments")
    clips: Mapped[list["Clip"]] = relationship(back_populates="highlight_moment")


from app.db.models.analysis_result import AnalysisResult  # noqa: E402
from app.db.models.clip import Clip  # noqa: E402
