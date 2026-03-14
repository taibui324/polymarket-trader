"""Alert data models."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum


class AlertType(str, Enum):
    """Alert type."""

    ARB_OPPORTUNITY = "arb_opportunity"
    PRICE_MOVE = "price_move"
    PATTERN = "pattern"
    VOLUME_SPIKE = "volume_spike"


class AlertSeverity(str, Enum):
    """Alert severity."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Alert(BaseModel):
    """Trading alert."""

    id: Optional[UUID] = None
    type: AlertType
    severity: AlertSeverity = AlertSeverity.INFO
    message: str
    data: Optional[dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged: bool = False

    model_config = {"from_attributes": True}
