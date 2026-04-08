import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import settings
from app.db.base import engine, Base, AsyncSessionLocal
from app.db.seed import seed_example_development_data

logging.basicConfig(
    level=settings.LOG_LEVEL.upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    force=True,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise the database tables on startup."""
    for attempt in range(5):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created / verified.")
            break
        except Exception as exc:
            logger.warning(
                "Could not connect to database (attempt %d/5): %s", attempt + 1, exc
            )
            if attempt == 4:
                logger.error(
                    "Failed to connect to database after 5 attempts. "
                    "Make sure the DB is running (`docker compose up db`)."
                )
                raise
            time.sleep(2 ** attempt)

    if settings.ENVIRONMENT == "development":
        async with AsyncSessionLocal() as db:
            await seed_example_development_data(db)

    yield


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Backend service for the Timesheet application. "
        "Supports timesheet entry management, time codes, and approval workflows."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
def root():
    return {"message": f"{settings.APP_NAME} is running."}


@app.get("/health", tags=["Root"])
def health_check():
    return {"status": "ok"}


app.include_router(api_router)
