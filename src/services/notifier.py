"""Notification service for alerts."""

import threading
from typing import Any, Optional
import json
from src.models.alert import Alert, AlertType, AlertSeverity
from src.services.supabase_client import get_supabase_client
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Notifier:
    """Alert notification service."""

    def __init__(self) -> None:
        """Initialize notifier."""
        self._supabase = get_supabase_client()

    def send_alert(
        self,
        alert_type: AlertType,
        message: str,
        severity: AlertSeverity = AlertSeverity.INFO,
        data: Optional[dict[str, Any]] = None,
    ) -> Alert:
        """Send an alert notification."""
        alert_data = {
            "type": alert_type.value,
            "severity": severity.value,
            "message": message,
            "data": json.dumps(data) if data else None,
        }

        # Store in database
        db_alert = self._supabase.insert_alert(alert_data)

        # Validate response
        if not db_alert or "id" not in db_alert:
            logger.error("Failed to insert alert: missing id in response", alert_type=alert_type.value)
            raise RuntimeError("Failed to insert alert: missing id in response")

        # Print to console
        self._print_alert(alert_type, severity, message, data)

        return Alert(
            id=db_alert.get("id"),
            type=alert_type,
            severity=severity,
            message=message,
            data=data,
        )

    def _print_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        data: Optional[dict[str, Any]],
    ) -> None:
        """Print alert to console with formatting."""
        severity_emoji = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.CRITICAL: "🚨",
        }

        emoji = severity_emoji.get(severity, "ℹ️")
        type_str = alert_type.value.upper()

        logger.info(
            f"{emoji} [{type_str}] {message}",
            extra={"alert_type": alert_type.value, "severity": severity.value},
        )

        if data:
            logger.debug("Alert data", data=data)

    def send_arb_alert(
        self,
        market_id: str,
        question: str,
        yes_price: float,
        no_price: float,
        spread: float,
    ) -> Alert:
        """Send arbitrage opportunity alert."""
        message = (
            f"Arbitrage opportunity: {question[:50]}... "
            f"YES: ${yes_price:.2f}, NO: ${no_price:.2f}, Spread: {spread*100:.2f}%"
        )

        return self.send_alert(
            alert_type=AlertType.ARB_OPPORTUNITY,
            message=message,
            severity=AlertSeverity.WARNING if spread < 0.05 else AlertSeverity.CRITICAL,
            data={
                "market_id": market_id,
                "question": question,
                "yes_price": yes_price,
                "no_price": no_price,
                "spread": spread,
            },
        )

    def send_price_alert(
        self,
        market_id: str,
        question: str,
        old_price: float,
        new_price: float,
        change_pct: float,
    ) -> Alert:
        """Send price movement alert."""
        # Handle equal prices correctly
        if new_price > old_price:
            direction = "UP"
        elif new_price < old_price:
            direction = "DOWN"
        else:
            direction = "UNCHANGED"

        message = (
            f"Price {direction}: {question[:50]}... "
            f"${old_price:.2f} → ${new_price:.2f} ({change_pct*100:+.1f}%)"
        )

        return self.send_alert(
            alert_type=AlertType.PRICE_MOVE,
            message=message,
            severity=AlertSeverity.INFO,
            data={
                "market_id": market_id,
                "question": question,
                "old_price": old_price,
                "new_price": new_price,
                "change_pct": change_pct,
            },
        )

    def send_pattern_alert(
        self,
        market_id: str,
        question: str,
        pattern_type: str,
        details: str,
    ) -> Alert:
        """Send pattern detection alert."""
        message = f"Pattern detected: {pattern_type} - {question[:40]}... {details}"

        return self.send_alert(
            alert_type=AlertType.PATTERN,
            message=message,
            severity=AlertSeverity.INFO,
            data={
                "market_id": market_id,
                "question": question,
                "pattern_type": pattern_type,
                "details": details,
            },
        )


# Global instance with thread-safe singleton
_notifier: Optional[Notifier] = None
_notifier_lock = threading.Lock()


def get_notifier() -> Notifier:
    """Get global notifier instance (thread-safe)."""
    global _notifier
    if _notifier is None:
        with _notifier_lock:
            if _notifier is None:
                _notifier = Notifier()
    return _notifier
