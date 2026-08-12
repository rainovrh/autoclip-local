from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ClipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    highlight_moment_id: int
    aspect_ratio: str
    crop_mode: str
    output_path: str | None
    resolution: str | None
    duration_seconds: float | None
    render_status: str
    render_error_message: str | None
    created_at: datetime
    updated_at: datetime
