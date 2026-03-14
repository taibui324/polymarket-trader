"""Supabase client with retry logic."""

from typing import Any, Optional
from supabase import create_client, Client
from src.config import get_settings
from src.utils.retry import retry_with_backoff
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SupabaseClient:
    """Supabase client wrapper with retry logic."""

    def __init__(self) -> None:
        """Initialize Supabase client."""
        settings = get_settings()
        self._client: Optional[Client] = None
        self._url = settings.supabase_url
        self._key = settings.supabase_key

    @property
    def client(self) -> Client:
        """Get or create Supabase client."""
        if self._client is None:
            if not self._url or not self._key:
                raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
            self._client = create_client(self._url, self._key)
        return self._client

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def fetch_markets(self) -> list[dict[str, Any]]:
        """Fetch active markets."""
        logger.info("Fetching markets from Supabase")
        response = self.client.table("markets").select("*").execute()
        return response.data

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def insert_market(self, data: dict[str, Any]) -> dict[str, Any]:
        """Insert a new market."""
        logger.info("Inserting market", market_id=data.get("polymarket_id"))
        response = self.client.table("markets").insert(data).execute()
        return response.data[0] if response.data else {}

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def update_market(self, market_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Update a market."""
        logger.info("Updating market", market_id=market_id)
        response = (
            self.client.table("markets")
            .update(data)
            .eq("polymarket_id", market_id)
            .execute()
        )
        return response.data[0] if response.data else {}

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def insert_snapshot(self, data: dict[str, Any]) -> dict[str, Any]:
        """Insert a market snapshot."""
        response = self.client.table("market_snapshots").insert(data).execute()
        return response.data[0] if response.data else {}

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def fetch_snapshots(
        self, market_id: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Fetch market snapshots."""
        response = (
            self.client.table("market_snapshots")
            .select("*")
            .eq("market_id", market_id)
            .order("timestamp", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def insert_trade(self, data: dict[str, Any]) -> dict[str, Any]:
        """Insert a trade."""
        logger.info("Inserting trade", market_id=data.get("market_id"))
        response = self.client.table("trades").insert(data).execute()
        return response.data[0] if response.data else {}

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def update_trade(
        self, trade_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a trade."""
        logger.info("Updating trade", trade_id=trade_id)
        response = (
            self.client.table("trades").update(data).eq("id", trade_id).execute()
        )
        return response.data[0] if response.data else {}

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def insert_alert(self, data: dict[str, Any]) -> dict[str, Any]:
        """Insert an alert."""
        logger.info(
            "Inserting alert",
            alert_type=data.get("type"),
            severity=data.get("severity"),
        )
        response = self.client.table("alerts").insert(data).execute()
        return response.data[0] if response.data else {}

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def fetch_alerts(
        self, alert_type: Optional[str] = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Fetch alerts."""
        query = self.client.table("alerts").select("*")
        if alert_type:
            query = query.eq("type", alert_type)
        response = query.order("created_at", desc=True).limit(limit).execute()
        return response.data


# Global instance
_supabase_client: Optional[SupabaseClient] = None


def get_supabase_client() -> SupabaseClient:
    """Get global Supabase client instance."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client
