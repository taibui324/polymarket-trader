"""Tests for trading strategies."""

import pytest
from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from src.strategies.arb_scanner import ArbitrageScanner
from src.strategies.pattern_detector import PatternDetector
from src.models.market import MarketSnapshot


class TestArbitrageScanner:
    """Test arbitrage scanner strategy."""

    def test_no_arb_when_prices_normal(self):
        """Test no alert when prices are normal."""
        scanner = ArbitrageScanner()

        market_id = str(uuid4())
        snapshots = [
            MarketSnapshot(
                id=uuid4(),
                market_id=uuid4(),
                timestamp=datetime.utcnow(),
                yes_price=Decimal("0.55"),
                no_price=Decimal("0.45"),
            )
        ]

        alerts = scanner.analyze(market_id, "Test market?", snapshots)
        assert len(alerts) == 0

    def test_arb_detected_when_spread_large(self):
        """Test arbitrage detected when spread exceeds threshold."""
        scanner = ArbitrageScanner()

        market_id = str(uuid4())
        snapshots = [
            MarketSnapshot(
                id=uuid4(),
                market_id=uuid4(),
                timestamp=datetime.utcnow(),
                yes_price=Decimal("0.60"),
                no_price=Decimal("0.50"),
            )
        ]

        alerts = scanner.analyze(market_id, "Test market?", snapshots)
        assert len(alerts) == 1
        assert alerts[0].type.value == "arb_opportunity"

    def test_check_real_time_arb(self):
        """Test real-time arbitrage check."""
        scanner = ArbitrageScanner()

        alerts = scanner.check_real_time_arb(
            "test-market",
            "Test?",
            Decimal("0.65"),
            Decimal("0.50"),
        )

        assert len(alerts) == 1


class TestPatternDetector:
    """Test pattern detector strategy."""

    def test_price_movement_detected(self):
        """Test significant price movement detection."""
        detector = PatternDetector()

        market_id = str(uuid4())
        now = datetime.utcnow()
        mkt_id = uuid4()

        snapshots = [
            MarketSnapshot(
                id=uuid4(),
                market_id=mkt_id,
                timestamp=now,
                yes_price=Decimal("0.70"),
                no_price=Decimal("0.30"),
            ),
            MarketSnapshot(
                id=uuid4(),
                market_id=mkt_id,
                timestamp=now,
                yes_price=Decimal("0.50"),
                no_price=Decimal("0.50"),
            ),
        ]

        alerts = detector.analyze(market_id, "Test?", snapshots)
        assert len(alerts) >= 1

    def test_no_alerts_insufficient_data(self):
        """Test no alerts with insufficient data."""
        detector = PatternDetector()

        market_id = str(uuid4())
        mkt_id = uuid4()
        snapshots = [
            MarketSnapshot(
                id=uuid4(),
                market_id=mkt_id,
                timestamp=datetime.utcnow(),
                yes_price=Decimal("0.50"),
                no_price=Decimal("0.50"),
            )
        ]

        alerts = detector.analyze(market_id, "Test?", snapshots)
        assert len(alerts) == 0
