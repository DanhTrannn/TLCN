from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="API_",
        case_sensitive=False,
        extra="ignore",
    )

    service_name: str = "ecommerce-api"
    service_version: str = "0.1.0"
    database_url: str = "mysql+pymysql://ecommerce_app:change-me@mysql-ecommerce:3306/ecommerce"
    secret_key: str = Field(min_length=32)
    cors_origins: str = "http://localhost:3000"
    cookie_secure: bool = False
    enable_docs: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

