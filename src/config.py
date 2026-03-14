"""Configuration management for Polymarket Trading System."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""

    # Polymarket
    polymarket_api_key: str = ""

    # Trading thresholds
    alert_threshold_arb: float = 0.02  # 2% arbitrage
    alert_threshold_price_move: float = 0.10  # 10% price move

    # Polling
    poll_interval_seconds: int = 30

    # App
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
