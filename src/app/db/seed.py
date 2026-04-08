import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository.time_codes import (
    create_time_code,
    get_time_code_by_code,
    grant_time_code_access,
)
from app.db.repository.users import create_user, get_user_by_email
from app.schemas.time_code import TimeCodeCreate
from app.schemas.user import UserCreate

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Seed data — used in development only (ENVIRONMENT=development).
# These passwords are intentionally simple for local testing.
# They are NEVER used in production because seed_example_development_data()
# is only called when ENVIRONMENT == "development" (see main.py lifespan).
# ---------------------------------------------------------------------------

SEED_USERS = [
    UserCreate(
        name="Admin User",
        email="admin@example.com",
        role="admin",
        password="adminpassword123",
    ),
    UserCreate(
        name="Alice Manager",
        email="alice@example.com",
        role="manager",
        password="alicepassword123",
    ),
    UserCreate(
        name="Bob Employee",
        email="bob@example.com",
        role="employee",
        password="bobpassword123",
    ),
    UserCreate(
        name="Carol Employee",
        email="carol@example.com",
        role="employee",
        password="carolpassword123",
    ),
]

SEED_TIME_CODES = [
    TimeCodeCreate(code="DEV", description="Software Development"),
    TimeCodeCreate(code="ADMIN", description="Administrative Tasks"),
    TimeCodeCreate(code="MEET", description="Meetings"),
    TimeCodeCreate(code="TRAIN", description="Training and Learning"),
    TimeCodeCreate(code="LEAVE", description="Annual / Sick Leave"),
]

# Map employee email → list of time codes they may use
SEED_ACCESS: dict[str, list[str]] = {
    "bob@example.com": ["DEV", "MEET", "LEAVE"],
    "carol@example.com": ["ADMIN", "MEET", "TRAIN", "LEAVE"],
}


async def seed_example_development_data(db: AsyncSession) -> None:
    """Populate the database with example data for local development."""
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

    # Grant time-code access to seed employees
    for email, codes in SEED_ACCESS.items():
        user = await get_user_by_email(db, email=email)
        if not user:
            continue
        for code_str in codes:
            tc = await get_time_code_by_code(db, code=code_str)
            if tc:
                await grant_time_code_access(db, user_id=user.id, time_code_id=tc.id)
                logger.info("Granted %s access to time code %s", email, code_str)

    logger.info("Seeding complete.")

