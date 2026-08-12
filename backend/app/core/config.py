from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self

# backend/app/core/config.py -> project root = ../../..
BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent

ProjectStatus = Literal[
    "UPLOADED",
    "AUDIO_EXTRACTED",
    "TRANSCRIBED",
    "ANALYZED",
    "RENDERED",
    "FAILED",
]

JobType = Literal[
    "ffmpeg_extract_audio",
    "whisper_transcribe",
    "ollama_analyze",
    "render_clip",
]

JobStatus = Literal["queued", "running", "completed", "failed"]


def resolve_project_path(path: Path | str) -> Path:
    """Resolve path relatif terhadap root proyek (bukan cwd terminal)."""
    resolved = Path(path)
    if resolved.is_absolute():
        return resolved
    normalized = resolved.as_posix().removeprefix("./")
    return PROJECT_ROOT / normalized


def build_sqlite_url(db_path: Path) -> str:
    """Buat DSN SQLite async dengan path absolut (aman di Windows)."""
    return f"sqlite+aiosqlite:///{db_path.resolve().as_posix()}"


def resolve_database_url(url: str) -> str:
    """Normalisasi DATABASE_URL agar file DB selalu di bawah project root."""
    prefix = "sqlite+aiosqlite:///"
    if not url.startswith(prefix):
        msg = f"Unsupported DATABASE_URL scheme: {url}"
        raise ValueError(msg)

    raw_path = url.removeprefix(prefix)
    db_path = resolve_project_path(raw_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return build_sqlite_url(db_path)


class Settings(BaseSettings):
    """Konfigurasi aplikasi dari environment / .env."""

    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env", BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite+aiosqlite:///./data/autoclip.db"
    storage_root: Path = Path("./storage")
    assets_root: Path = Path("./assets")

    ollama_base_url: str = "http://localhost:11434"
    default_ollama_model: str = "llama3.1:8b"
    default_whisper_model: str = "large-v3"

    pexels_api_key: str = ""

    api_host: str = "127.0.0.1"
    api_port: int = 8000
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    log_level: str = "INFO"

    @model_validator(mode="after")
    def resolve_paths(self) -> Self:
        storage = resolve_project_path(self.storage_root)
        assets = resolve_project_path(self.assets_root)
        storage.mkdir(parents=True, exist_ok=True)
        assets.mkdir(parents=True, exist_ok=True)

        object.__setattr__(self, "storage_root", storage)
        object.__setattr__(self, "assets_root", assets)
        object.__setattr__(self, "database_url", resolve_database_url(self.database_url))
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
