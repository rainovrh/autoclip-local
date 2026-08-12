from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base


class BrollAsset(Base):
    __tablename__ = "broll_assets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    clip_id: Mapped[int] = mapped_column(
        ForeignKey("clips.id", ondelete="CASCADE"), nullable=False
    )
    source_segment_id: Mapped[int | None] = mapped_column(
        ForeignKey("transcript_segments.id")
    )
    pexels_query: Mapped[str | None] = mapped_column(String)
    pexels_video_id: Mapped[str | None] = mapped_column(String)
    pexels_video_url: Mapped[str | None] = mapped_column(String)
    local_cache_path: Mapped[str | None] = mapped_column(String)
    overlay_start_time: Mapped[float | None] = mapped_column(Float)
    overlay_end_time: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    clip: Mapped["Clip"] = relationship(back_populates="broll_assets")


from app.db.models.clip import Clip  # noqa: E402
