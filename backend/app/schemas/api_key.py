from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApiKeyCreate(BaseModel):
    service_name: str = Field(..., min_length=1, max_length=100)
    api_key_value: str = Field(..., min_length=1, max_length=255)


class ApiKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service_name: str
    api_key_value: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
