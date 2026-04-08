from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.time_code import TimeCode
from app.schemas.time_code import TimeCodeCreate, TimeCodeUpdate


async def get_time_code(db: AsyncSession, time_code_id: int) -> Optional[TimeCode]:
    result = await db.execute(select(TimeCode).where(TimeCode.id == time_code_id))
    return result.scalars().first()


async def get_time_code_by_code(db: AsyncSession, code: str) -> Optional[TimeCode]:
    result = await db.execute(select(TimeCode).where(TimeCode.code == code))
    return result.scalars().first()


async def get_time_codes(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
) -> Sequence[TimeCode]:
    query = select(TimeCode).offset(skip).limit(limit)
    if active_only:
        query = query.where(TimeCode.is_active.is_(True))
    result = await db.execute(query)
    return result.scalars().all()


async def create_time_code(db: AsyncSession, payload: TimeCodeCreate) -> TimeCode:
    time_code = TimeCode(**payload.model_dump())
    db.add(time_code)
    await db.commit()
    await db.refresh(time_code)
    return time_code


async def update_time_code(
    db: AsyncSession, time_code: TimeCode, payload: TimeCodeUpdate
) -> TimeCode:
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(time_code, field, value)
    await db.commit()
    await db.refresh(time_code)
    return time_code


async def delete_time_code(db: AsyncSession, time_code: TimeCode) -> None:
    await db.delete(time_code)
    await db.commit()
