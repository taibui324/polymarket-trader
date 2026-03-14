"""Trade data models."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum


class TradeSide(str, Enum):
    """Trade side."""

    YES = "yes"
    NO = "no"


class TradeStatus(str, Enum):
    """Trade status."""

    PENDING = "pending"
    FILLED = "filled"
    SETTLED = "settled"
    CANCELLED = "cancelled"


class Trade(BaseModel):
    """Trade record."""

    id: Optional[UUID] = None
    market_id: Optional[UUID] = None
    user_id: str
    side: TradeSide
    amount: Decimal
    price: Decimal
    status: TradeStatus = TradeStatus.PENDING
    profit_loss: Optional[Decimal] = None
    placed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    settled_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @property
    def payout(self) -> Decimal:
        """Calculate potential payout if trade wins."""
        if self.status == TradeStatus.SETTLED and self.profit_loss is not None:
            return self.amount + self.profit_loss
        return self.amount * self.price
