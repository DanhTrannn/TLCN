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
    enable_docs: bool = True
    bootstrap_admin_email: str = "admin@tlcn.local"
    bootstrap_admin_password: str = Field(default="Admin@12345", min_length=8)
    bootstrap_admin_display_name: str = "TLCN Admin"

    # Auth / cookie
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 720
    auth_cookie_name: str = "tlcn_access"
    csrf_cookie_name: str = "tlcn_csrf"
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    cookie_domain: str | None = None

    # Internal / demo
    internal_secret: str = "change-me-internal-secret"
    demo_mode: bool = True

    # Money / catalog
    currency_code: str = "VND"
    shipping_flat_fee_vnd: int = 30000
    free_shipping_threshold_vnd: int = 500000
    cart_item_max_quantity: int = 20
    catalog_page_size: int = 12
    order_page_size: int = 10

    # Concurrency
    checkout_max_retries: int = 3

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
