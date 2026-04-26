from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Equipment Management System"
    app_version: str = "1.0.0"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ems"

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
