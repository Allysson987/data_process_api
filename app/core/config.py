
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    APP_NAME: str = "Data Process API"
    ENVIRONMENT: str = "development"

    DATA_JUD_SECRET_KEY: str
    DATABASE_URL: str
    REDIS_URL: str | None = None

    DIARY_UFS: str = "AC,PE"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
