from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.db.models.user import User
from app.schemas.user import UserCreate, UserUpdate


async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def get_users(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
) -> Sequence[User]:
    query = select(User).offset(skip).limit(limit)
    if active_only:
        query = query.where(User.is_active.is_(True))
    result = await db.execute(query)
    return result.scalars().all()


async def create_user(db: AsyncSession, payload: UserCreate) -> User:
    data = payload.model_dump(exclude={"password"})
    data["hashed_password"] = hash_password(payload.password)
    user = User(**data)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user(
    db: AsyncSession, user: User, payload: UserUpdate
) -> User:
    data = payload.model_dump(exclude_unset=True, exclude={"password"})
    if payload.password is not None:
        data["hashed_password"] = hash_password(payload.password)
    for field, value in data.items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user: User) -> None:
    await db.delete(user)
    await db.commit()


async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> Optional[User]:
    """Return the user if credentials are valid and account is active, else None."""
    user = await get_user_by_email(db, email)
    if user is None:
        return None
    if not user.is_active:
        return None
    if not user.hashed_password:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
