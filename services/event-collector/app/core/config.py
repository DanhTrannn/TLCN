from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="COLLECTOR_",
        case_sensitive=False,
        extra="ignore",
    )

    service_name: str = "event-collector"
    service_version: str = "0.1.0"
    cors_origins: str = "http://localhost:3000"
    event_directory: Path = Path("/data/events")
    rotation_max_bytes: int = Field(default=10 * 1024 * 1024, gt=0)
    rotation_max_age_seconds: int = Field(default=300, gt=0)
    dedup_window_seconds: int = Field(default=3600, gt=0)
    dedup_max_entries: int = Field(default=100_000, gt=0)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

