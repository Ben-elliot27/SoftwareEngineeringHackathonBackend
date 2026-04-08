import logging
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.models.timesheet_entry import EntryStatus
from app.db.models.user import User, UserRole
from app.db.repository.timesheet_entries import (
    approve_timesheet_entry,
    create_timesheet_entry,
    delete_timesheet_entry,
    get_timesheet_entries,
    get_timesheet_entry,
    reject_timesheet_entry,
    update_timesheet_entry,
)
from app.db.repository.time_codes import get_time_code, user_has_time_code_access
from app.db.repository.users import get_user
from app.schemas.timesheet_entry import (
    RejectionRequest,
    TimesheetEntryCreate,
    TimesheetEntryResponse,
    TimesheetEntryUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[TimesheetEntryResponse])
async def list_timesheet_entries(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    time_code_id: Optional[int] = Query(None, description="Filter by time code ID"),
    status: Optional[EntryStatus] = Query(None, description="Filter by status"),
    entry_date_from: Optional[date] = Query(None, description="Filter entries on or after this date"),
    entry_date_to: Optional[date] = Query(None, description="Filter entries on or before this date"),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    List timesheet entries.

    * **Employee**: only their own entries are returned (``user_id`` filter is
      forced to their own ID regardless of the query parameter).
    * **Manager / Admin**: may filter by any user.
    """
    if current_user.role == UserRole.employee:
        # Employees can only view their own entries
        user_id = current_user.id

    return await get_timesheet_entries(
        db,
        skip=skip,
        limit=limit,
        user_id=user_id,
        time_code_id=time_code_id,
        status=status,
        entry_date_from=entry_date_from,
        entry_date_to=entry_date_to,
    )


@router.post("/", response_model=TimesheetEntryResponse, status_code=201)
async def create_timesheet_entry_endpoint(
    payload: TimesheetEntryCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Create a new timesheet entry.

    Employees may only create entries for themselves.  Managers and admins may
    create entries on behalf of any active user.
    """
    # Employees can only submit entries for themselves
    if current_user.role == UserRole.employee and payload.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Employees may only create timesheet entries for themselves",
        )

    target_user = await get_user(db, payload.user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    if not target_user.is_active:
        raise HTTPException(
            status_code=409,
            detail="Cannot create timesheet: target user is inactive",
        )

    tc = await get_time_code(db, payload.time_code_id)
    if not tc:
        raise HTTPException(status_code=404, detail="Time code not found")
    if not tc.is_active:
        raise HTTPException(status_code=422, detail="Time code is inactive")

    # Verify the submitting user has access to the chosen time code.
    # Admins and managers bypass this check — only employees are restricted.
    if current_user.role == UserRole.employee:
        has_access = await user_has_time_code_access(db, current_user.id, payload.time_code_id)
        if not has_access:
            raise HTTPException(
                status_code=403,
                detail="You do not have access to this time code",
            )

    return await create_timesheet_entry(db, payload)


@router.get("/{entry_id}", response_model=TimesheetEntryResponse)
async def get_timesheet_entry_endpoint(
    entry_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Get a timesheet entry by ID.

    Employees may only access their own entries.
    """
    entry = await get_timesheet_entry(db, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Timesheet entry not found")
    if current_user.role == UserRole.employee and entry.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return entry


@router.patch("/{entry_id}", response_model=TimesheetEntryResponse)
async def update_timesheet_entry_endpoint(
    entry_id: int,
    payload: TimesheetEntryUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Update a timesheet entry (only allowed while status is pending).

    Employees may only update their own entries.
    """
    entry = await get_timesheet_entry(db, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Timesheet entry not found")
    if current_user.role == UserRole.employee and entry.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    if entry.status != EntryStatus.pending:
        raise HTTPException(
            status_code=422,
            detail="Only pending entries can be updated",
        )
    if payload.time_code_id is not None:
        tc = await get_time_code(db, payload.time_code_id)
        if not tc:
            raise HTTPException(status_code=404, detail="Time code not found")
        if not tc.is_active:
            raise HTTPException(status_code=422, detail="Time code is inactive")
        if current_user.role == UserRole.employee:
            has_access = await user_has_time_code_access(
                db, current_user.id, payload.time_code_id
            )
            if not has_access:
                raise HTTPException(
                    status_code=403,
                    detail="You do not have access to this time code",
                )
    return await update_timesheet_entry(db, entry, payload)


@router.post("/{entry_id}/approve", response_model=TimesheetEntryResponse)
async def approve_entry(
    entry_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_manager_or_admin),
):
    """
    Approve a timesheet entry. **Manager / Admin only.**

    The approver is taken from the authenticated token — it cannot be spoofed
    via the request body.
    """
    entry = await get_timesheet_entry(db, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Timesheet entry not found")
    if entry.status != EntryStatus.pending:
        raise HTTPException(
            status_code=422,
            detail="Only pending entries can be approved",
        )
    return await approve_timesheet_entry(db, entry, approver_id=current_user.id)


@router.post("/{entry_id}/reject", response_model=TimesheetEntryResponse)
async def reject_entry(
    entry_id: int,
    payload: RejectionRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.require_manager_or_admin),
):
    """
    Reject a timesheet entry. **Manager / Admin only.**

    The rejector is taken from the authenticated token — it cannot be spoofed
    via the request body.
    """
    entry = await get_timesheet_entry(db, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Timesheet entry not found")
    if entry.status == EntryStatus.rejected:
        raise HTTPException(status_code=422, detail="Entry is already rejected")
    if entry.status != EntryStatus.pending:
        raise HTTPException(
            status_code=422,
            detail="Only pending entries can be rejected",
        )
    return await reject_timesheet_entry(
        db, entry, approver_id=current_user.id, rejection_reason=payload.rejection_reason
    )


@router.delete("/{entry_id}", status_code=204)
async def delete_timesheet_entry_endpoint(
    entry_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Delete a timesheet entry.

    Employees may only delete their own pending entries.
    Admins may delete any entry.
    """
    entry = await get_timesheet_entry(db, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Timesheet entry not found")
    if current_user.role == UserRole.admin:
        await delete_timesheet_entry(db, entry)
        return
    if entry.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    if entry.status != EntryStatus.pending:
        raise HTTPException(
            status_code=422,
            detail="Only pending entries can be deleted",
        )
    await delete_timesheet_entry(db, entry)
