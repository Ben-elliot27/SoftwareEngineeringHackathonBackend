import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.repository.users import (
    create_user,
    delete_user,
    get_user,
    get_user_by_email,
    get_users,
    update_user,
)
from app.schemas.user import UserCreate, UserResponse, UserUpdate

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: AsyncSession = Depends(deps.get_db),
):
    """List all users."""
    return await get_users(db, skip=skip, limit=limit, active_only=active_only)


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user_endpoint(
    payload: UserCreate,
    db: AsyncSession = Depends(deps.get_db),
):
    """Create a new user."""
    existing = await get_user_by_email(db, email=payload.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    return await create_user(db, payload)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_endpoint(
    user_id: int,
    db: AsyncSession = Depends(deps.get_db),
):
    """Get a user by ID."""
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user_endpoint(
    user_id: int,
    payload: UserUpdate,
    db: AsyncSession = Depends(deps.get_db),
):
    """Update a user."""
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.email:
        existing = await get_user_by_email(db, email=payload.email)
        if existing and existing.id != user_id:
            raise HTTPException(status_code=409, detail="Email already in use")
    return await update_user(db, user, payload)


@router.delete("/{user_id}", status_code=204)
async def delete_user_endpoint(
    user_id: int,
    db: AsyncSession = Depends(deps.get_db),
):
    """Delete a user."""
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await delete_user(db, user)
