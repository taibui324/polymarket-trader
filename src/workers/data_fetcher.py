"""Data fetcher worker - polls and stores market data."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID
from src.config import get_settings
from src.services.polymarket_api import get_polymarket_api
from src.services.supabase_client import get_supabase_client
from src.models.market import Market, MarketSnapshot
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataFetcher:
    """Worker that polls Polymarket and stores market data."""

    def __init__(self) -> None:
        """Initialize data fetcher."""
        settings = get_settings()
        self._polymarket = get_polymarket_api()
        self._supabase = get_supabase_client()
        self._poll_interval = settings.poll_interval_seconds

    def fetch_and_store_markets(self) -> int:
        """Fetch active markets and store in database.

        Returns:
            Number of markets processed
        """
        logger.info("Fetching markets from Polymarket")

        try:
            markets_data = self._polymarket.get_markets(limit=100)
        except Exception as e:
            logger.error("Failed to fetch markets", error=str(e))
            return 0

        processed = 0
        for market_data in markets_data:
            try:
                self._process_market(market_data)
                processed += 1
            except Exception as e:
                logger.error(
                    "Failed to process market",
                    market_id=market_data.get("id"),
                    error=str(e),
                )

        logger.info("Markets processed", count=processed)
        return processed

    def _process_market(self, data: dict[str, Any]) -> None:
        """Process a single market from API response."""
        condition_id = data.get("conditionId") or data.get("id")
        question = data.get("question", "")

        if not condition_id or not question:
            return

        # Check if market exists
        existing = self._supabase.fetch_markets()
        existing_ids = {m.get("polymarket_id") for m in existing}

        if condition_id in existing_ids:
            # Update existing market
            self._update_market(condition_id, data)
        else:
            # Insert new market
            self._insert_market(condition_id, data)

        # Fetch and store snapshot
        self._store_snapshot(condition_id, data)

    def _insert_market(self, condition_id: str, data: dict[str, Any]) -> None:
        """Insert new market into database."""
        market_data = {
            "polymarket_id": condition_id,
            "question": data.get("question", ""),
            "description": data.get("description"),
            "outcome_yes": "Yes",
            "outcome_no": "No",
        }

        self._supabase.insert_market(market_data)
        logger.info("Inserted market", market_id=condition_id)

    def _update_market(self, condition_id: str, data: dict[str, Any]) -> None:
        """Update existing market."""
        # Check if market is closed or resolved
        update_data: dict[str, Any] = {}

        if data.get("closed"):
            update_data["closed_at"] = datetime.utcnow()

        if data.get("resolved"):
            update_data["resolved_at"] = datetime.utcnow()
            update_data["result"] = data.get("outcome")

        if update_data:
            self._supabase.update_market(condition_id, update_data)

    def _store_snapshot(self, condition_id: str, data: dict[str, Any]) -> None:
        """Store price snapshot for a market."""
        # Get prices from API response
        yes_price = self._parse_decimal(data.get("yesPrice", 0.5))
        no_price = self._parse_decimal(data.get("noPrice", 0.5))

        if yes_price is None or no_price is None:
            return

        # Get market ID from database
        markets = self._supabase.fetch_markets()
        market = next((m for m in markets if m.get("polymarket_id") == condition_id), None)

        if not market:
            logger.warning("Market not found for snapshot", market_id=condition_id)
            return

        snapshot_data = {
            "market_id": market.get("id"),
            "timestamp": datetime.utcnow().isoformat(),
            "yes_price": str(yes_price),
            "no_price": str(no_price),
            "yes_volume": str(data.get("volumeNum", 0)),
            "no_volume": str(data.get("volumeNum", 0) * (1 - float(yes_price))),
            "liquidity": str(data.get("liquidity", 0)),
        }

        self._supabase.insert_snapshot(snapshot_data)
        logger.debug("Stored snapshot", market_id=condition_id, yes=yes_price, no=no_price)

    def _parse_decimal(self, value: Any) -> Decimal | None:
        """Parse value to Decimal."""
        if value is None:
            return None

        try:
            return Decimal(str(value))
        except Exception:
            return None

    def run_once(self) -> int:
        """Run a single iteration of data fetching.

        Returns:
            Number of markets processed
        """
        return self.fetch_and_store_markets()


# Global instance
_data_fetcher: Optional[DataFetcher] = None


def get_data_fetcher() -> DataFetcher:
    """Get global data fetcher instance."""
    global _data_fetcher
    if _data_fetcher is None:
        _data_fetcher = DataFetcher()
    return _data_fetcher
