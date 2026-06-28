"""
Centralized configuration management using Pydantic Settings.

All environment variables are validated and typed at startup, providing:
- Type safety and validation
- Default values
- Clear documentation of required env vars
- Single source of truth for configuration
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """PostgreSQL database configuration."""

    user: str = Field(default="postgres", alias="POSTGRES_USER")
    password: str = Field(default="postgres", alias="POSTGRES_PASSWORD")
    host: str = Field(default="localhost", alias="POSTGRES_HOST")
    port: int = Field(default=5432, alias="POSTGRES_PORT")
    db: str = Field(default="ai_news_aggregator", alias="POSTGRES_DB")

    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"

    @property
    def async_url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"

    model_config = {"env_file": "app/.env", "extra": "ignore"}


class OpenAISettings(BaseSettings):
    """OpenAI API configuration."""

    api_key: str = Field(default="", alias="OPENAI_API_KEY")
    digest_model: str = Field(default="gpt-4o-mini")
    curator_model: str = Field(default="gpt-4.1")
    email_model: str = Field(default="gpt-4o-mini")

    model_config = {"env_file": "app/.env", "extra": "ignore"}


class EmailSettings(BaseSettings):
    """Email (Gmail SMTP) configuration."""

    sender_email: str = Field(default="", alias="MY_EMAIL")
    app_password: str = Field(default="", alias="APP_PASSWORD")
    smtp_host: str = Field(default="smtp.gmail.com")
    smtp_port: int = Field(default=465)

    model_config = {"env_file": "app/.env", "extra": "ignore"}


class ProxySettings(BaseSettings):
    """Optional proxy configuration for YouTube transcript fetching."""

    username: Optional[str] = Field(default=None, alias="PROXY_USERNAME")
    password: Optional[str] = Field(default=None, alias="PROXY_PASSWORD")

    @property
    def is_configured(self) -> bool:
        return bool(self.username and self.password)

    model_config = {"env_file": "app/.env", "extra": "ignore"}


class PipelineSettings(BaseSettings):
    """Pipeline execution configuration."""

    default_hours: int = Field(default=24, description="Default lookback window in hours")
    default_top_n: int = Field(default=10, description="Default number of top articles")
    max_content_length: int = Field(default=8000, description="Max content chars for digest")
    max_concurrent_scrapers: int = Field(default=5, description="Max concurrent scraper tasks")
    retry_max_attempts: int = Field(default=3, description="Max retry attempts for failed operations")
    retry_wait_seconds: float = Field(default=1.0, description="Initial wait between retries")

    model_config = {"env_file": "app/.env", "extra": "ignore"}


class Settings(BaseSettings):
    """Root settings aggregating all configuration sections."""

    database: DatabaseSettings = DatabaseSettings()
    openai: OpenAISettings = OpenAISettings()
    email: EmailSettings = EmailSettings()
    proxy: ProxySettings = ProxySettings()
    pipeline: PipelineSettings = PipelineSettings()

    # Application metadata
    app_name: str = "AI Newsletter Agent"
    app_version: str = "2.0.0"
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    model_config = {"env_file": "app/.env", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings. Call once at startup."""
    return Settings()
