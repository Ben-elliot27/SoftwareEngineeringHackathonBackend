from pydantic_settings import BaseSettings


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
