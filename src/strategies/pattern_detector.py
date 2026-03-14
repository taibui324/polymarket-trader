"""Technical pattern detection strategy."""

from decimal import Decimal
from typing import Any
from datetime import datetime, timedelta
from src.strategies.base import BaseStrategy
from src.models.market import MarketSnapshot
from src.models.alert import Alert, AlertType, AlertSeverity
from src.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PatternDetector(BaseStrategy):
    """Detect technical patterns in market data.

    Patterns detected:
    - Price movement alerts (% change threshold)
    - Volume spikes
    - Moving average crossovers
    - Support/resistance breaks
    """

    def __init__(self) -> None:
        """Initialize pattern detector."""
        super().__init__("PatternDetector")
        settings = get_settings()
        self.price_threshold = Decimal(str(settings.alert_threshold_price_move))
        self.volume_spike_multiplier = 2.0  # Volume 2x average = spike
        self.ma_short = 5  # Short-term MA period
        self.ma_long = 20  # Long-term MA period

    def analyze(
        self,
        market_id: str,
        question: str,
        snapshots: list[MarketSnapshot],
    ) -> list[Alert]:
        """Analyze market data for patterns.

        Args:
            market_id: Market identifier
            question: Market question
            snapshots: Historical price snapshots

        Returns:
            List of pattern alerts
        """
        if len(snapshots) < 2:
            return []

        alerts = []

        # Sort by timestamp (newest first)
        sorted_snapshots = sorted(snapshots, key=lambda s: s.timestamp, reverse=True)

        # 1. Check for significant price movements
        price_alerts = self._check_price_movement(market_id, question, sorted_snapshots)
        alerts.extend(price_alerts)

        # 2. Check for volume spikes
        volume_alerts = self._check_volume_spike(market_id, question, sorted_snapshots)
        alerts.extend(volume_alerts)

        # 3. Check for MA crossovers
        ma_alerts = self._check_ma_crossover(market_id, question, sorted_snapshots)
        alerts.extend(ma_alerts)

        # 4. Check for support/resistance breaks
        sr_alerts = self._check_sr_break(market_id, question, sorted_snapshots)
        alerts.extend(sr_alerts)

        return alerts

    def _check_price_movement(
        self,
        market_id: str,
        question: str,
        snapshots: list[MarketSnapshot],
    ) -> list[Alert]:
        """Check for significant price movements."""
        if len(snapshots) < 2:
            return []

        latest = snapshots[0]
        previous = snapshots[1]

        # Calculate percentage change
        if previous.yes_price > 0:
            change = (latest.yes_price - previous.yes_price) / previous.yes_price

            if abs(change) > self.price_threshold:
                alert = Alert(
                    type=AlertType.PRICE_MOVE,
                    severity=AlertSeverity.WARNING,
                    message=(
                        f"Price movement: {question[:40]}... "
                        f"${float(previous.yes_price):.2f} → ${float(latest.yes_price):.2f} "
                        f"({float(change)*100:+.1f}%)"
                    ),
                    data={
                        "market_id": market_id,
                        "question": question,
                        "old_price": float(previous.yes_price),
                        "new_price": float(latest.yes_price),
                        "change_pct": float(change),
                    },
                )
                self._alerts.append(alert)
                self.log_analysis(market_id, f"PRICE_MOVE: {float(change)*100:+.1f}%")
                return [alert]

        return []

    def _check_volume_spike(
        self,
        market_id: str,
        question: str,
        snapshots: list[MarketSnapshot],
    ) -> list[Alert]:
        """Check for volume spikes."""
        if len(snapshots) < 10:
            return []

        latest = snapshots[0]
        if not latest.yes_volume:
            return []

        # Calculate average volume from recent snapshots
        volumes = [
            float(s.yes_volume or 0)
            for s in snapshots[1:10]  # Skip latest
            if s.yes_volume
        ]

        if not volumes:
            return []

        avg_volume = sum(volumes) / len(volumes)
        current_volume = float(latest.yes_volume or 0)

        if current_volume > avg_volume * self.volume_spike_multiplier:
            alert = Alert(
                type=AlertType.VOLUME_SPIKE,
                severity=AlertSeverity.INFO,
                message=(
                    f"Volume spike: {question[:40]}... "
                    f"${avg_volume:.0f} → ${current_volume:.0f} "
                    f"({current_volume/avg_volume:.1f}x avg)"
                ),
                data={
                    "market_id": market_id,
                    "question": question,
                    "current_volume": current_volume,
                    "avg_volume": avg_volume,
                    "multiplier": current_volume / avg_volume,
                },
            )
            self._alerts.append(alert)
            self.log_analysis(market_id, f"VOLUME_SPIKE: {current_volume/avg_volume:.1f}x")
            return [alert]

        return []

    def _check_ma_crossover(
        self,
        market_id: str,
        question: str,
        snapshots: list[MarketSnapshot],
    ) -> list[Alert]:
        """Check for moving average crossovers."""
        if len(snapshots) < self.ma_long:
            return []

        # Calculate MAs
        short_ma = self._calculate_ma(snapshots, self.ma_short)
        long_ma = self._calculate_ma(snapshots, self.ma_long)

        if short_ma is None or long_ma is None:
            return []

        # Check for crossover
        prev_short = self._calculate_ma(snapshots[1:], self.ma_short)
        prev_long = self._calculate_ma(snapshots[1:], self.ma_long)

        if prev_short is None or prev_long is None:
            return []

        # Golden cross (short crosses above long) - bullish
        if prev_short <= prev_long and short_ma > long_ma:
            alert = Alert(
                type=AlertType.PATTERN,
                severity=AlertSeverity.INFO,
                message=f"Golden Cross: {question[:40]}... Short MA crossed above Long MA",
                data={
                    "market_id": market_id,
                    "question": question,
                    "pattern_type": "golden_cross",
                    "short_ma": float(short_ma),
                    "long_ma": float(long_ma),
                },
            )
            self._alerts.append(alert)
            self.log_analysis(market_id, "GOLDEN_CROSS")
            return [alert]

        # Death cross (short crosses below long) - bearish
        if prev_short >= prev_long and short_ma < long_ma:
            alert = Alert(
                type=AlertType.PATTERN,
                severity=AlertSeverity.INFO,
                message=f"Death Cross: {question[:40]}... Short MA crossed below Long MA",
                data={
                    "market_id": market_id,
                    "question": question,
                    "pattern_type": "death_cross",
                    "short_ma": float(short_ma),
                    "long_ma": float(long_ma),
                },
            )
            self._alerts.append(alert)
            self.log_analysis(market_id, "DEATH_CROSS")
            return [alert]

        return []

    def _check_sr_break(
        self,
        market_id: str,
        question: str,
        snapshots: list[MarketSnapshot],
    ) -> list[Alert]:
        """Check for support/resistance breaks."""
        if len(snapshots) < 10:
            return []

        # Exclude current price from historical calculation
        # snapshots[0] is current, snapshots[1:] are historical
        historical_prices = [float(s.yes_price) for s in snapshots[1:10]]

        if not historical_prices:
            return []

        # Find recent high and low from historical data only
        recent_high = max(historical_prices)
        recent_low = min(historical_prices)
        current = float(snapshots[0].yes_price)

        # Breakout above resistance
        if current > recent_high * 1.02:  # 2% above high
            alert = Alert(
                type=AlertType.PATTERN,
                severity=AlertSeverity.WARNING,
                message=f"Resistance breakout: {question[:40]}... ${recent_high:.2f} → ${current:.2f}",
                data={
                    "market_id": market_id,
                    "question": question,
                    "pattern_type": "resistance_break",
                    "resistance": recent_high,
                    "current": current,
                },
            )
            self._alerts.append(alert)
            self.log_analysis(market_id, f"RESISTANCE_BREAK: ${current:.2f}")
            return [alert]

        # Breakdown below support
        if current < recent_low * 0.98:  # 2% below low
            alert = Alert(
                type=AlertType.PATTERN,
                severity=AlertSeverity.WARNING,
                message=f"Support break: {question[:40]}... ${recent_low:.2f} → ${current:.2f}",
                data={
                    "market_id": market_id,
                    "question": question,
                    "pattern_type": "support_break",
                    "support": recent_low,
                    "current": current,
                },
            )
            self._alerts.append(alert)
            self.log_analysis(market_id, f"SUPPORT_BREAK: ${current:.2f}")
            return [alert]

        return []

    def _calculate_ma(
        self,
        snapshots: list[MarketSnapshot],
        period: int,
    ) -> Decimal | None:
        """Calculate simple moving average."""
        if len(snapshots) < period:
            return None

        prices = [s.yes_price for s in snapshots[:period]]
        if not prices:
            return None

        return sum(prices) / Decimal(str(period))
