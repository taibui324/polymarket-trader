"""Arbitrage detection strategy."""

from decimal import Decimal
from typing import Any
from src.strategies.base import BaseStrategy
from src.models.market import MarketSnapshot
from src.models.alert import Alert, AlertType, AlertSeverity
from src.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ArbitrageScanner(BaseStrategy):
    """Scan for arbitrage opportunities in Polymarket markets.

    In efficient markets, yes_price + no_price should equal 1.00.
    Deviations indicate potential arbitrage opportunities.
    """

    def __init__(self) -> None:
        """Initialize arbitrage scanner."""
        super().__init__("ArbitrageScanner")
        settings = get_settings()
        self.threshold = Decimal(str(settings.alert_threshold_arb))

    def analyze(
        self,
        market_id: str,
        question: str,
        snapshots: list[MarketSnapshot],
    ) -> list[Alert]:
        """Analyze for arbitrage opportunities.

        Args:
            market_id: Market identifier
            question: Market question
            snapshots: Historical price snapshots

        Returns:
            List of arbitrage alerts
        """
        if not snapshots:
            return []

        alerts = []
        latest = snapshots[0]  # Most recent snapshot

        # Calculate total price (should be ~1.00)
        total_price = latest.yes_price + latest.no_price
        spread = abs(total_price - Decimal("1.00"))

        # Check if spread exceeds threshold
        if spread > self.threshold:
            spread_pct = float(spread)
            is_profitable = spread > Decimal("0.03")  # Worth trading if > 3%

            alert = Alert(
                type=AlertType.ARB_OPPORTUNITY,
                severity=AlertSeverity.CRITICAL if is_profitable else AlertSeverity.WARNING,
                message=(
                    f"Arbitrage detected: {question[:50]}... "
                    f"YES: ${latest.yes_price:.2f}, NO: ${latest.no_price:.2f}, "
                    f"Spread: {spread_pct*100:.2f}%"
                ),
                data={
                    "market_id": market_id,
                    "question": question,
                    "yes_price": float(latest.yes_price),
                    "no_price": float(latest.no_price),
                    "spread": float(spread),
                    "total_price": float(total_price),
                },
            )
            alerts.append(alert)
            self._alerts.append(alert)

            self.log_analysis(
                market_id,
                f"ARB OPPORTUNITY: spread={spread_pct*100:.2f}%",
            )

        return alerts

    def check_real_time_arb(
        self,
        market_id: str,
        question: str,
        yes_price: Decimal,
        no_price: Decimal,
    ) -> list[Alert]:
        """Check for arbitrage in real-time price data.

        Args:
            market_id: Market identifier
            question: Market question
            yes_price: Current YES price
            no_price: Current NO price

        Returns:
            List of alerts
        """
        total_price = yes_price + no_price
        spread = abs(total_price - Decimal("1.00"))

        if spread > self.threshold:
            spread_pct = float(spread)

            alert = Alert(
                type=AlertType.ARB_OPPORTUNITY,
                severity=AlertSeverity.CRITICAL if spread > Decimal("0.03") else AlertSeverity.WARNING,
                message=(
                    f"Arbitrage: {question[:50]}... "
                    f"YES: ${yes_price:.2f}, NO: ${no_price:.2f}, "
                    f"Spread: {spread_pct*100:.2f}%"
                ),
                data={
                    "market_id": market_id,
                    "question": question,
                    "yes_price": float(yes_price),
                    "no_price": float(no_price),
                    "spread": float(spread),
                },
            )
            self._alerts.append(alert)
            return [alert]

        return []
