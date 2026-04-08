import logging
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.models.timesheet_entry import EntryStatus
from app.db.repository.timesheet_entries import (
    approve_timesheet_entry,
    create_timesheet_entry,
    delete_timesheet_entry,
    get_timesheet_entries,
    get_timesheet_entry,
    reject_timesheet_entry,
    update_timesheet_entry,
)
from app.db.repository.time_codes import get_time_code
from app.db.repository.users import get_user
from app.schemas.timesheet_entry import (
    ApprovalRequest,
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
):
    """List timesheet entries with optional filters."""
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
):
    """Create a new timesheet entry."""
    user = await get_user(db, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    tc = await get_time_code(db, payload.time_code_id)
    if not tc:
        raise HTTPException(status_code=404, detail="Time code not found")
    if not tc.is_active:
        raise HTTPException(status_code=422, detail="Time code is inactive")
    return await create_timesheet_entry(db, payload)


@router.get("/{entry_id}", response_model=TimesheetEntryResponse)
async def get_timesheet_entry_endpoint(
    entry_id: int,
    db: AsyncSession = Depends(deps.get_db),
):
    """Get a timesheet entry by ID."""
    entry = await get_timesheet_entry(db, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Timesheet entry not found")
    return entry


@router.patch("/{entry_id}", response_model=TimesheetEntryResponse)
async def update_timesheet_entry_endpoint(
    entry_id: int,
    payload: TimesheetEntryUpdate,
    db: AsyncSession = Depends(deps.get_db),
):
    """Update a timesheet entry (only allowed while status is pending)."""
    entry = await get_timesheet_entry(db, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Timesheet entry not found")
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
    return await update_timesheet_entry(db, entry, payload)


@router.post("/{entry_id}/approve", response_model=TimesheetEntryResponse)
async def approve_entry(
    entry_id: int,
    payload: ApprovalRequest,
    db: AsyncSession = Depends(deps.get_db),
):
    """Approve a timesheet entry."""
    entry = await get_timesheet_entry(db, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Timesheet entry not found")
    if entry.status == EntryStatus.approved:
        raise HTTPException(status_code=422, detail="Entry is already approved")
    approver = await get_user(db, payload.approved_by_id)
    if not approver:
        raise HTTPException(status_code=404, detail="Approver user not found")
    return await approve_timesheet_entry(db, entry, payload)


@router.post("/{entry_id}/reject", response_model=TimesheetEntryResponse)
async def reject_entry(
    entry_id: int,
    payload: RejectionRequest,
    db: AsyncSession = Depends(deps.get_db),
):
    """Reject a timesheet entry."""
    entry = await get_timesheet_entry(db, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Timesheet entry not found")
    if entry.status == EntryStatus.rejected:
        raise HTTPException(status_code=422, detail="Entry is already rejected")
    approver = await get_user(db, payload.approved_by_id)
    if not approver:
        raise HTTPException(status_code=404, detail="Approver user not found")
    return await reject_timesheet_entry(db, entry, payload)


@router.delete("/{entry_id}", status_code=204)
async def delete_timesheet_entry_endpoint(
    entry_id: int,
    db: AsyncSession = Depends(deps.get_db),
):
    """Delete a timesheet entry."""
    entry = await get_timesheet_entry(db, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Timesheet entry not found")
    await delete_timesheet_entry(db, entry)
