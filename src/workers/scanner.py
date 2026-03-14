"""Scanner worker - runs strategy engines on market data."""

from typing import Any, Optional
from uuid import UUID
from src.services.supabase_client import get_supabase_client
from src.strategies.arb_scanner import ArbitrageScanner
from src.strategies.pattern_detector import PatternDetector
from src.models.market import MarketSnapshot
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Scanner:
    """Worker that runs strategies on market data."""

    def __init__(self) -> None:
        """Initialize scanner."""
        self._supabase = get_supabase_client()
        self._strategies = [
            ArbitrageScanner(),
            PatternDetector(),
        ]

    def scan_all_markets(self) -> int:
        """Run all strategies on all markets.

        Returns:
            Number of alerts generated
        """
        logger.info("Starting market scan")

        # Fetch all markets
        markets = self._supabase.fetch_markets()

        if not markets:
            logger.warning("No markets found to scan")
            return 0

        total_alerts = 0

        for market in markets:
            try:
                alerts = self._scan_market(market)
                total_alerts += len(alerts)
            except Exception as e:
                logger.error(
                    "Failed to scan market",
                    market_id=market.get("polymarket_id"),
                    error=str(e),
                )

        logger.info("Scan complete", markets=len(markets), alerts=total_alerts)
        return total_alerts

    def _scan_market(self, market: dict[str, Any]) -> list[dict[str, Any]]:
        """Scan a single market with all strategies.

        Args:
            market: Market data from database

        Returns:
            List of generated alerts
        """
        market_id = market.get("polymarket_id")
        question = market.get("question", "")
        db_market_id = market.get("id")

        if not market_id or not db_market_id:
            return []

        # Fetch recent snapshots
        snapshots_data = self._supabase.fetch_snapshots(db_market_id, limit=100)

        # Convert to model objects
        snapshots = [
            MarketSnapshot(
                id=s.get("id"),
                market_id=UUID(s.get("market_id", "")),
                timestamp=s.get("timestamp"),
                yes_price=s.get("yes_price"),
                no_price=s.get("no_price"),
                yes_volume=s.get("yes_volume"),
                no_volume=s.get("no_volume"),
                liquidity=s.get("liquidity"),
            )
            for s in snapshots_data
        ]

        if not snapshots:
            logger.debug("No snapshots for market", market_id=market_id)
            return []

        alerts = []

        # Run each strategy
        for strategy in self._strategies:
            strategy_alerts = strategy.analyze(market_id, question, snapshots)

            for alert in strategy_alerts:
                # Store alert in database
                alert_data = {
                    "type": alert.type.value,
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "data": alert.data,
                }
                self._supabase.insert_alert(alert_data)
                alerts.append(alert_data)

        return alerts

    def scan_realtime_prices(
        self,
        market_data: list[dict[str, Any]],
    ) -> int:
        """Scan real-time price data without database.

        Args:
            market_data: List of market data with current prices

        Returns:
            Number of alerts generated
        """
        logger.info("Scanning realtime prices", markets=len(market_data))

        arb_scanner = ArbitrageScanner()
        total_alerts = 0

        for market in market_data:
            condition_id = market.get("conditionId") or market.get("id")
            question = market.get("question", "")
            yes_price = market.get("yesPrice", 0.5)
            no_price = market.get("noPrice", 0.5)

            # Check arbitrage
            alerts = arb_scanner.check_real_time_arb(
                condition_id,
                question,
                yes_price,
                no_price,
            )

            total_alerts += len(alerts)

            for alert in alerts:
                logger.info(
                    f"[ALERT] {alert.message}",
                    extra={"alert_type": alert.type.value},
                )

        return total_alerts


# Global instance
_scanner: Optional[Scanner] = None


def get_scanner() -> Scanner:
    """Get global scanner instance."""
    global _scanner
    if _scanner is None:
        _scanner = Scanner()
    return _scanner
