import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.models.user import User, UserRole
from app.db.repository.time_codes import (
    create_time_code,
    delete_time_code,
    get_time_code,
    get_time_code_by_code,
    get_time_codes,
    get_time_codes_for_user,
    grant_time_code_access,
    get_users_for_time_code,
    revoke_time_code_access,
    update_time_code,
    user_has_time_code_access,
)
from app.db.repository.users import get_user
from app.schemas.time_code import TimeCodeCreate, TimeCodeResponse, TimeCodeUpdate
from app.schemas.user import UserResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[TimeCodeResponse])
async def list_time_codes(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    List time codes.

    * **Admin/Manager**: returns all time codes.
    * **Employee**: returns only time codes they have been granted access to.
    """
    if current_user.role in (UserRole.admin, UserRole.manager):
        return await get_time_codes(db, skip=skip, limit=limit, active_only=active_only)
    return await get_time_codes_for_user(
        db, user_id=current_user.id, skip=skip, limit=limit, active_only=active_only
    )


@router.post("/", response_model=TimeCodeResponse, status_code=201)
async def create_time_code_endpoint(
    payload: TimeCodeCreate,
    db: AsyncSession = Depends(deps.get_db),
    _current_user: User = Depends(deps.require_admin),
):
    """Create a new time code. **Admin only.**"""
    existing = await get_time_code_by_code(db, code=payload.code)
    if existing:
        raise HTTPException(status_code=409, detail="Time code already exists")
    return await create_time_code(db, payload)


@router.get("/{time_code_id}", response_model=TimeCodeResponse)
async def get_time_code_endpoint(
    time_code_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Get a time code by ID.

    Employees may only access time codes they have been granted access to.
    """
    tc = await get_time_code(db, time_code_id)
    if not tc:
        raise HTTPException(status_code=404, detail="Time code not found")
    if current_user.role == UserRole.employee:
        has_access = await user_has_time_code_access(db, current_user.id, time_code_id)
        if not has_access:
            raise HTTPException(status_code=403, detail="Access to this time code is not permitted")
    return tc


@router.patch("/{time_code_id}", response_model=TimeCodeResponse)
async def update_time_code_endpoint(
    time_code_id: int,
    payload: TimeCodeUpdate,
    db: AsyncSession = Depends(deps.get_db),
    _current_user: User = Depends(deps.require_admin),
):
    """Update a time code. **Admin only.**"""
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
    _current_user: User = Depends(deps.require_admin),
):
    """Delete a time code. **Admin only.**"""
    tc = await get_time_code(db, time_code_id)
    if not tc:
        raise HTTPException(status_code=404, detail="Time code not found")
    await delete_time_code(db, tc)


# ---------------------------------------------------------------------------
# Access management (admin only)
# ---------------------------------------------------------------------------

@router.get("/{time_code_id}/access", response_model=List[UserResponse])
async def list_time_code_access(
    time_code_id: int,
    db: AsyncSession = Depends(deps.get_db),
    _current_user: User = Depends(deps.require_admin),
):
    """List all users who have access to a time code. **Admin only.**"""
    tc = await get_time_code(db, time_code_id)
    if not tc:
        raise HTTPException(status_code=404, detail="Time code not found")
    return await get_users_for_time_code(db, time_code_id)


@router.post("/{time_code_id}/access/{user_id}", status_code=201)
async def grant_access(
    time_code_id: int,
    user_id: int,
    db: AsyncSession = Depends(deps.get_db),
    _current_user: User = Depends(deps.require_admin),
):
    """Grant a user access to a time code. **Admin only.**"""
    tc = await get_time_code(db, time_code_id)
    if not tc:
        raise HTTPException(status_code=404, detail="Time code not found")
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await grant_time_code_access(db, user_id=user_id, time_code_id=time_code_id)
    return {"detail": f"Access granted: user {user_id} → time code {time_code_id}"}


@router.delete("/{time_code_id}/access/{user_id}", status_code=204)
async def revoke_access(
    time_code_id: int,
    user_id: int,
    db: AsyncSession = Depends(deps.get_db),
    _current_user: User = Depends(deps.require_admin),
):
    """Revoke a user's access to a time code. **Admin only.**"""
    tc = await get_time_code(db, time_code_id)
    if not tc:
        raise HTTPException(status_code=404, detail="Time code not found")
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    deleted = await revoke_time_code_access(db, user_id=user_id, time_code_id=time_code_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Access grant not found")
