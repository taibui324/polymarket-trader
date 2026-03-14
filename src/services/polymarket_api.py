"""Polymarket API client."""

import httpx
from typing import Any, Optional
from decimal import Decimal
from src.config import get_settings
from src.utils.retry import retry_with_backoff
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PolymarketAPIError(Exception):
    """Polymarket API error."""

    pass


class PolymarketAPI:
    """Client for Polymarket API."""

    BASE_URL = "https://clob.polymarket.com"

    def __init__(self) -> None:
        """Initialize API client."""
        settings = get_settings()
        self._api_key = settings.polymarket_api_key
        self._client = httpx.Client(
            timeout=30.0,
            headers=self._get_headers(),
        )

    def _get_headers(self) -> dict[str, str]:
        """Get request headers."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def get_markets(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get active markets."""
        # Polymarket uses GraphQL, but for simplicity we'll use REST endpoints
        # This is a simplified implementation - real API may need GraphQL
        url = f"{self.BASE_URL}/markets"
        params = {"limit": limit, "active": True}

        try:
            response = self._client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            logger.info("Fetched markets", count=len(data))
            return data
        except httpx.HTTPStatusError as e:
            logger.error("API error", status=e.response.status_code, detail=e.response.text)
            raise PolymarketAPIError(f"Failed to fetch markets: {e}")

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def get_market(self, condition_id: str) -> dict[str, Any]:
        """Get a specific market by condition ID."""
        url = f"{self.BASE_URL}/markets/{condition_id}"

        try:
            response = self._client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error("API error", status=e.response.status_code)
            raise PolymarketAPIError(f"Failed to fetch market: {e}")

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def get_order_book(self, condition_id: str) -> dict[str, Any]:
        """Get order book for a market."""
        url = f"{self.BASE_URL}/orderbooks/{condition_id}"

        try:
            response = self._client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error("API error", status=e.response.status_code)
            raise PolymarketAPIError(f"Failed to fetch orderbook: {e}")

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def get_price(self, condition_id: str) -> dict[str, Decimal]:
        """Get current prices for yes/no outcomes."""
        # Try to get from order book or price endpoint
        url = f"{self.BASE_URL}/prices"

        try:
            response = self._client.get(url, params={"conditionId": condition_id})
            response.raise_for_status()
            data = response.json()

            # Parse price data
            yes_price = Decimal(str(data.get("yes", "0.5")))
            no_price = Decimal(str(data.get("no", "0.5")))

            return {"yes": yes_price, "no": no_price}
        except httpx.HTTPStatusError as e:
            logger.warning("Price fetch failed, using default", error=str(e))
            return {"yes": Decimal("0.5"), "no": Decimal("0.5")}

    def get_candidate_markets(self) -> list[dict[str, Any]]:
        """Get candidate markets (newly created, high volume)."""
        # This would typically query for markets with certain criteria
        # For now, return active markets with additional filtering
        markets = self.get_markets(limit=50)

        # Filter for candidate markets (can be customized)
        candidate_markets = [
            m for m in markets
            if m.get("volumeNum") and float(m.get("volumeNum", 0)) > 10000
        ]

        logger.info("Found candidate markets", count=len(candidate_markets))
        return candidate_markets

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()


# Global instance
_polymarket_api: Optional[PolymarketAPI] = None


def get_polymarket_api() -> PolymarketAPI:
    """Get global Polymarket API instance."""
    global _polymarket_api
    if _polymarket_api is None:
        _polymarket_api = PolymarketAPI()
    return _polymarket_api
