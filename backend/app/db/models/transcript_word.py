from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base


class TranscriptWord(Base):
    __tablename__ = "transcript_words"
    __table_args__ = (UniqueConstraint("segment_id", "word_index"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    segment_id: Mapped[int] = mapped_column(
        ForeignKey("transcript_segments.id", ondelete="CASCADE"), nullable=False
    )
    word_index: Mapped[int] = mapped_column(Integer, nullable=False)
    word: Mapped[str] = mapped_column(String, nullable=False)
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)

    segment: Mapped["TranscriptSegment"] = relationship(back_populates="words")


from app.db.models.transcript_segment import TranscriptSegment  # noqa: E402
