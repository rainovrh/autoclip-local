from datetime import datetime

from pydantic import BaseModel, ConfigDict


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    job_type: str
    status: str
    priority: int
    started_at: datetime | None
    finished_at: datetime | None
    error_message: str | None
    created_at: datetime


class JobAcceptedResponse(BaseModel):
    job_id: int
    message: str = "Job berhasil didaftarkan ke antrean."
