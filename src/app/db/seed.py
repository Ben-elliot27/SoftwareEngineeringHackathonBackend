import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository.time_codes import create_time_code, get_time_code_by_code
from app.db.repository.users import create_user, get_user_by_email
from app.schemas.time_code import TimeCodeCreate
from app.schemas.user import UserCreate

logger = logging.getLogger(__name__)

SEED_USERS = [
    UserCreate(name="Alice Manager", email="alice@example.com", role="manager"),
    UserCreate(name="Bob Employee", email="bob@example.com", role="employee"),
    UserCreate(name="Carol Employee", email="carol@example.com", role="employee"),
]

SEED_TIME_CODES = [
    TimeCodeCreate(code="DEV", description="Software Development"),
    TimeCodeCreate(code="ADMIN", description="Administrative Tasks"),
    TimeCodeCreate(code="MEET", description="Meetings"),
    TimeCodeCreate(code="TRAIN", description="Training and Learning"),
    TimeCodeCreate(code="LEAVE", description="Annual / Sick Leave"),
]


async def seed_example_development_data(db: AsyncSession) -> None:
    logger.info("Seeding development data...")

    for user_data in SEED_USERS:
        existing = await get_user_by_email(db, email=user_data.email)
        if not existing:
            await create_user(db, user_data)
            logger.info("Created seed user: %s", user_data.email)

    for tc_data in SEED_TIME_CODES:
        existing = await get_time_code_by_code(db, code=tc_data.code)
        if not existing:
            await create_time_code(db, tc_data)
            logger.info("Created seed time code: %s", tc_data.code)

    logger.info("Seeding complete.")
