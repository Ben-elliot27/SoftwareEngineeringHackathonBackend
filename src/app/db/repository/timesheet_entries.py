from datetime import date, datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.timesheet_entry import EntryStatus, TimesheetEntry
from app.schemas.timesheet_entry import (
    TimesheetEntryCreate,
    TimesheetEntryUpdate,
)


def _entry_with_relations(query):
    return query.options(
        selectinload(TimesheetEntry.user),
        selectinload(TimesheetEntry.time_code),
        selectinload(TimesheetEntry.approver),
    )


async def get_timesheet_entry(
    db: AsyncSession, entry_id: int
) -> Optional[TimesheetEntry]:
    query = _entry_with_relations(
        select(TimesheetEntry).where(TimesheetEntry.id == entry_id)
    )
    result = await db.execute(query)
    return result.scalars().first()


async def get_timesheet_entries(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    time_code_id: Optional[int] = None,
    status: Optional[EntryStatus] = None,
    entry_date_from: Optional[date] = None,
    entry_date_to: Optional[date] = None,
) -> Sequence[TimesheetEntry]:
    query = _entry_with_relations(select(TimesheetEntry))

    if user_id is not None:
        query = query.where(TimesheetEntry.user_id == user_id)
    if time_code_id is not None:
        query = query.where(TimesheetEntry.time_code_id == time_code_id)
    if status is not None:
        query = query.where(TimesheetEntry.status == status)
    if entry_date_from is not None:
        query = query.where(TimesheetEntry.entry_date >= entry_date_from)
    if entry_date_to is not None:
        query = query.where(TimesheetEntry.entry_date <= entry_date_to)

    query = query.order_by(TimesheetEntry.entry_date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def create_timesheet_entry(
    db: AsyncSession, payload: TimesheetEntryCreate
) -> TimesheetEntry:
    entry = TimesheetEntry(**payload.model_dump())
    db.add(entry)
    await db.commit()
    # Reload with relations
    return await get_timesheet_entry(db, entry.id)


async def update_timesheet_entry(
    db: AsyncSession, entry: TimesheetEntry, payload: TimesheetEntryUpdate
) -> TimesheetEntry:
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(entry, field, value)
    await db.commit()
    return await get_timesheet_entry(db, entry.id)


async def approve_timesheet_entry(
    db: AsyncSession, entry: TimesheetEntry, approver_id: int
) -> TimesheetEntry:
    """Mark *entry* as approved by *approver_id* (taken from the JWT, not the payload)."""
    entry.status = EntryStatus.approved
    entry.approved_by_id = approver_id
    entry.approved_at = datetime.now(timezone.utc)
    entry.rejection_reason = None
    await db.commit()
    return await get_timesheet_entry(db, entry.id)


async def reject_timesheet_entry(
    db: AsyncSession,
    entry: TimesheetEntry,
    approver_id: int,
    rejection_reason: Optional[str] = None,
) -> TimesheetEntry:
    """Mark *entry* as rejected by *approver_id* (taken from the JWT, not the payload)."""
    entry.status = EntryStatus.rejected
    entry.approved_by_id = approver_id
    entry.approved_at = datetime.now(timezone.utc)
    entry.rejection_reason = rejection_reason
    await db.commit()
    return await get_timesheet_entry(db, entry.id)


async def delete_timesheet_entry(db: AsyncSession, entry: TimesheetEntry) -> None:
    await db.delete(entry)
    await db.commit()
