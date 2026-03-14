"""Market data models."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class Market(BaseModel):
    """Polymarket market."""

    id: Optional[UUID] = None
    polymarket_id: str
    question: str
    description: Optional[str] = None
    outcome_yes: str = "Yes"
    outcome_no: str = "No"
    created_at: datetime = Field(default_factory=_utc_now)
    closed_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    result: Optional[str] = None  # 'yes', 'no', 'unresolved'

    model_config = {"from_attributes": True}


class MarketSnapshot(BaseModel):
    """Historical snapshot of market odds."""

    id: Optional[UUID] = None
    market_id: UUID
    timestamp: datetime = Field(default_factory=_utc_now)
    yes_price: Decimal
    no_price: Decimal
    yes_volume: Optional[Decimal] = None
    no_volume: Optional[Decimal] = None
    liquidity: Optional[Decimal] = None

    model_config = {"from_attributes": True}


class MarketWithPrices(BaseModel):
    """Market with current prices for display."""

    market: Market
    yes_price: Decimal
    no_price: Decimal
    yes_volume: Optional[Decimal] = None
    no_volume: Optional[Decimal] = None
    liquidity: Optional[Decimal] = None
    timestamp: datetime = Field(default_factory=_utc_now)

    @property
    def total_price(self) -> Decimal:
        """Sum of yes + no prices (should be ~1.00)."""
        return self.yes_price + self.no_price

    @property
    def arb_opportunity(self) -> Optional[Decimal]:
        """Returns arb spread if exists, None otherwise."""
        spread = abs(self.total_price - Decimal("1.00"))
        return spread if spread > Decimal("0.02") else None
