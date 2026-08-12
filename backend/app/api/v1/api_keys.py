import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.api_key import ApiKey
from app.db.session import get_db_session
from app.schemas.api_key import ApiKeyCreate, ApiKeyResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=list[ApiKeyResponse])
async def list_api_keys(
    session: AsyncSession = Depends(get_db_session),
) -> list[ApiKeyResponse]:
    """Daftar semua API key."""
    result = await session.execute(select(ApiKey).order_by(ApiKey.created_at.desc()))
    keys = result.scalars().all()
    return [ApiKeyResponse.model_validate(k) for k in keys]


@router.post("", response_model=ApiKeyResponse, status_code=201)
async def create_api_key(
    payload: ApiKeyCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ApiKeyResponse:
    """Buat API key baru."""
    api_key = ApiKey(
        service_name=payload.service_name.strip(),
        api_key_value=payload.api_key_value.strip(),
        is_active=True,
    )
    session.add(api_key)
    try:
        await session.commit()
        await session.refresh(api_key)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="API key untuk service ini sudah ada.",
        )
    return ApiKeyResponse.model_validate(api_key)


@router.put("/{key_id}", response_model=ApiKeyResponse)
async def update_api_key(
    key_id: int,
    payload: ApiKeyCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ApiKeyResponse:
    """Update API key."""
    api_key = await session.get(ApiKey, key_id)
    if api_key is None:
        raise HTTPException(status_code=404, detail="API key tidak ditemukan.")

    api_key.service_name = payload.service_name.strip()
    api_key.api_key_value = payload.api_key_value.strip()
    session.add(api_key)
    try:
        await session.commit()
        await session.refresh(api_key)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="API key untuk service ini sudah ada.",
        )
    return ApiKeyResponse.model_validate(api_key)


@router.delete("/{key_id}", status_code=204)
async def delete_api_key(
    key_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> None:
    """Hapus API key."""
    api_key = await session.get(ApiKey, key_id)
    if api_key is None:
        raise HTTPException(status_code=404, detail="API key tidak ditemukan.")
    await session.delete(api_key)
    await session.commit()


@router.patch("/{key_id}/toggle", response_model=ApiKeyResponse)
async def toggle_api_key(
    key_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> ApiKeyResponse:
    """Aktifkan/nonaktifkan API key."""
    api_key = await session.get(ApiKey, key_id)
    if api_key is None:
        raise HTTPException(status_code=404, detail="API key tidak ditemukan.")

    api_key.is_active = not api_key.is_active
    session.add(api_key)
    await session.commit()
    await session.refresh(api_key)
    return ApiKeyResponse.model_validate(api_key)
