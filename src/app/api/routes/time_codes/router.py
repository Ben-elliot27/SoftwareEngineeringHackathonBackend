import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.repository.time_codes import (
    create_time_code,
    delete_time_code,
    get_time_code,
    get_time_code_by_code,
    get_time_codes,
    update_time_code,
)
from app.schemas.time_code import TimeCodeCreate, TimeCodeResponse, TimeCodeUpdate

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[TimeCodeResponse])
async def list_time_codes(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: AsyncSession = Depends(deps.get_db),
):
    """List all time codes."""
    return await get_time_codes(db, skip=skip, limit=limit, active_only=active_only)


@router.post("/", response_model=TimeCodeResponse, status_code=201)
async def create_time_code_endpoint(
    payload: TimeCodeCreate,
    db: AsyncSession = Depends(deps.get_db),
):
    """Create a new time code."""
    existing = await get_time_code_by_code(db, code=payload.code)
    if existing:
        raise HTTPException(status_code=409, detail="Time code already exists")
    return await create_time_code(db, payload)


@router.get("/{time_code_id}", response_model=TimeCodeResponse)
async def get_time_code_endpoint(
    time_code_id: int,
    db: AsyncSession = Depends(deps.get_db),
):
    """Get a time code by ID."""
    tc = await get_time_code(db, time_code_id)
    if not tc:
        raise HTTPException(status_code=404, detail="Time code not found")
    return tc


@router.patch("/{time_code_id}", response_model=TimeCodeResponse)
async def update_time_code_endpoint(
    time_code_id: int,
    payload: TimeCodeUpdate,
    db: AsyncSession = Depends(deps.get_db),
):
    """Update a time code."""
    tc = await get_time_code(db, time_code_id)
    if not tc:
        raise HTTPException(status_code=404, detail="Time code not found")
    if payload.code:
        existing = await get_time_code_by_code(db, code=payload.code)
        if existing and existing.id != time_code_id:
            raise HTTPException(status_code=409, detail="Time code already in use")
    return await update_time_code(db, tc, payload)


@router.delete("/{time_code_id}", status_code=204)
async def delete_time_code_endpoint(
    time_code_id: int,
    db: AsyncSession = Depends(deps.get_db),
):
    """Delete a time code."""
    tc = await get_time_code(db, time_code_id)
    if not tc:
        raise HTTPException(status_code=404, detail="Time code not found")
    await delete_time_code(db, tc)
