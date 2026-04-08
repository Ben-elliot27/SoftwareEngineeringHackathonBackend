import logging

from pydantic import field_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

_INSECURE_DEFAULT_KEY = "change-this-to-a-long-random-secret-in-production"


class Settings(BaseSettings):
    """
    Application settings.

    Values are read in order:
    1. Environment variables
    2. .env file
    3. Defaults defined here
    """

    APP_NAME: str = "Timesheet API"
    APP_VERSION: str = "0.1.0"

    # Database
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "timesheet"
    DB_NAME: str = "timesheet"
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"

    # Misc
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "debug"

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    # JWT / Auth
    SECRET_KEY: str = _INSECURE_DEFAULT_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    @field_validator("SECRET_KEY")
    @classmethod
    def warn_insecure_secret(cls, v: str) -> str:
        if v == _INSECURE_DEFAULT_KEY:
            logger.warning(
                "SECRET_KEY is set to the insecure default value. "
                "Set a strong SECRET_KEY environment variable before deploying to production."
            )
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()
