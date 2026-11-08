from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    APP_NAME: str = "Data Process API"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str

    REDIS_URL: str | None = None

    DATA_JUD_SECRET_KEY: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    EMAIL_HASH_SECRET: str
    EMAIL_ENCRYPTION_KEY: str

    DIARY_UFS: str = "AC,PE"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()