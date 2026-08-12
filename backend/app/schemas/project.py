import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    source_type: str = Field(..., pattern="^(youtube|local_upload)$")
    source_url: str | None = Field(default=None)
    original_filename: str | None = Field(default=None)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        return value.strip()

    @field_validator("source_url")
    @classmethod
    def validate_source_url_not_empty(cls, value: str | None) -> str | None:
        if value is not None and value == "":
            raise ValueError("source_url tidak boleh kosong.")
        return value

    @field_validator("original_filename")
    @classmethod
    def validate_original_filename_not_empty(cls, value: str | None) -> str | None:
        if value is not None and value == "":
            raise ValueError("original_filename tidak boleh kosong.")
        return value

    @model_validator(mode="after")
    def validate_source_requirements(self) -> "ProjectCreate":
        if self.source_type == "youtube" and not self.source_url:
            raise ValueError("source_url wajib diisi untuk sumber youtube.")
        if self.source_type == "local_upload" and not self.original_filename:
            raise ValueError("original_filename wajib diisi untuk unggahan lokal.")
        return self

    def slugify_title(self) -> str:
        slug = re.sub(r"[^\w\s-]", "", self.title.strip().lower())
        slug = re.sub(r"[\s-]+", "-", slug).strip("-")
        return slug[:100] or "untitled-project"


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    folder_path: str
    source_type: str
    source_url: str | None
    original_filename: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class VideoSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    file_path: str
    audio_path: str | None
    resolution: str | None
    duration_seconds: float | None
    fps: float | None
    quality_check_passed: bool
    created_at: datetime


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int
