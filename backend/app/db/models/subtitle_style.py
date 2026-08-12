from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base


class SubtitleStyle(Base):
    __tablename__ = "subtitle_styles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    clip_id: Mapped[int] = mapped_column(
        ForeignKey("clips.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    display_mode: Mapped[str] = mapped_column(
        String, nullable=False, default="word_by_word"
    )
    font_family: Mapped[str] = mapped_column(String, nullable=False, default="Inter")
    font_size: Mapped[int] = mapped_column(Integer, nullable=False, default=48)
    font_weight: Mapped[str] = mapped_column(String, nullable=False, default="bold")
    is_uppercase: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    text_color: Mapped[str] = mapped_column(String, nullable=False, default="#FFFFFF")
    highlight_color: Mapped[str] = mapped_column(
        String, nullable=False, default="#FFD500"
    )
    background_color: Mapped[str | None] = mapped_column(String)
    background_opacity: Mapped[float | None] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    clip: Mapped["Clip"] = relationship(back_populates="subtitle_style")


from app.db.models.clip import Clip  # noqa: E402
