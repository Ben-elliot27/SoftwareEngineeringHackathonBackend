from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.time_code import TimeCode
from app.db.models.user_time_code import UserTimeCodeAccess
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
    """Return all time codes (admin view)."""
    query = select(TimeCode).offset(skip).limit(limit)
    if active_only:
        query = query.where(TimeCode.is_active.is_(True))
    result = await db.execute(query)
    return result.scalars().all()


async def get_time_codes_for_user(
    db: AsyncSession,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
) -> Sequence[TimeCode]:
    """Return only time codes that *user_id* has been granted access to."""
    query = (
        select(TimeCode)
        .join(UserTimeCodeAccess, UserTimeCodeAccess.time_code_id == TimeCode.id)
        .where(UserTimeCodeAccess.user_id == user_id)
        .offset(skip)
        .limit(limit)
    )
    if active_only:
        query = query.where(TimeCode.is_active.is_(True))
    result = await db.execute(query)
    return result.scalars().all()


async def user_has_time_code_access(
    db: AsyncSession, user_id: int, time_code_id: int
) -> bool:
    """Return True if *user_id* has been granted access to *time_code_id*."""
    result = await db.execute(
        select(UserTimeCodeAccess).where(
            UserTimeCodeAccess.user_id == user_id,
            UserTimeCodeAccess.time_code_id == time_code_id,
        )
    )
    return result.scalars().first() is not None


async def grant_time_code_access(
    db: AsyncSession, user_id: int, time_code_id: int
) -> UserTimeCodeAccess:
    """Grant *user_id* access to *time_code_id*. Idempotent."""
    existing = await db.execute(
        select(UserTimeCodeAccess).where(
            UserTimeCodeAccess.user_id == user_id,
            UserTimeCodeAccess.time_code_id == time_code_id,
        )
    )
    access = existing.scalars().first()
    if access is None:
        access = UserTimeCodeAccess(user_id=user_id, time_code_id=time_code_id)
        db.add(access)
        await db.commit()
        await db.refresh(access)
    return access


async def revoke_time_code_access(
    db: AsyncSession, user_id: int, time_code_id: int
) -> bool:
    """Revoke *user_id*'s access to *time_code_id*. Returns True if a row was deleted."""
    result = await db.execute(
        select(UserTimeCodeAccess).where(
            UserTimeCodeAccess.user_id == user_id,
            UserTimeCodeAccess.time_code_id == time_code_id,
        )
    )
    access = result.scalars().first()
    if access is None:
        return False
    await db.delete(access)
    await db.commit()
    return True


async def get_users_for_time_code(
    db: AsyncSession, time_code_id: int
) -> Sequence[UserTimeCodeAccess]:
    """Return all access grants for a given time code."""
    result = await db.execute(
        select(UserTimeCodeAccess).where(
            UserTimeCodeAccess.time_code_id == time_code_id
        )
    )
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
