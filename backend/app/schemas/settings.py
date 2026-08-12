from pydantic import BaseModel


class AppSettingsResponse(BaseModel):
    default_aspect_ratio: str = "9:16"
    default_whisper_model: str = "large-v3"
    default_ollama_model: str = "llama3.1:8b"


class HealthResponse(BaseModel):
    status: str = "ok"
    message: str = "AutoClip Local API siap."
