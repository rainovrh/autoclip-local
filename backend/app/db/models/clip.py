from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base


class Clip(Base):
    __tablename__ = "clips"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    highlight_moment_id: Mapped[int] = mapped_column(
        ForeignKey("highlight_moments.id", ondelete="CASCADE"), nullable=False
    )
    aspect_ratio: Mapped[str] = mapped_column(String, nullable=False, default="9:16")
    crop_mode: Mapped[str] = mapped_column(
        String, nullable=False, default="center_crop_static"
    )
    output_path: Mapped[str | None] = mapped_column(String)
    resolution: Mapped[str | None] = mapped_column(String)
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    render_status: Mapped[str] = mapped_column(String, nullable=False, default="queued")
    render_error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    project: Mapped["Project"] = relationship(back_populates="clips")
    highlight_moment: Mapped["HighlightMoment"] = relationship(
        back_populates="clips"
    )
    subtitle_style: Mapped["SubtitleStyle | None"] = relationship(
        back_populates="clip", uselist=False
    )
    broll_assets: Mapped[list["BrollAsset"]] = relationship(back_populates="clip")


from app.db.models.broll_asset import BrollAsset  # noqa: E402
from app.db.models.highlight_moment import HighlightMoment  # noqa: E402
from app.db.models.project import Project  # noqa: E402
from app.db.models.subtitle_style import SubtitleStyle  # noqa: E402
