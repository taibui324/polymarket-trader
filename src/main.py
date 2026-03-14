"""Main entry point for Polymarket Trading System."""

import sys
import signal
from typing import Optional
from src.config import get_settings
from src.utils.logger import get_logger
from src.workers.data_fetcher import get_data_fetcher
from src.workers.scanner import get_scanner
from src.workers.scheduler import get_scheduler

logger = get_logger(__name__)

# Global shutdown flag
_shutdown_requested = False


def signal_handler(signum: int, frame: object) -> None:
    """Handle shutdown signals."""
    global _shutdown_requested
    logger.info("Shutdown signal received", signal=signum)
    _shutdown_requested = True


def run_once() -> None:
    """Run a single iteration of all workers."""
    logger.info("Running workers once")

    # Fetch data
    data_fetcher = get_data_fetcher()
    markets_processed = data_fetcher.run_once()

    # Run scanner
    scanner = get_scanner()
    alerts_generated = scanner.scan_all_markets()

    logger.info(
        "Workers complete",
        markets=markets_processed,
        alerts=alerts_generated,
    )


def run_continuously() -> None:
    """Run workers continuously with scheduling."""
    logger.info("Starting continuous mode")

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    scheduler = get_scheduler()

    # Add jobs
    scheduler.add_data_fetcher_job(lambda: get_data_fetcher().run_once())
    scheduler.add_scanner_job(lambda: get_scanner().scan_all_markets())

    # Start scheduler
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler interrupted")
    finally:
        scheduler.shutdown()
        logger.info("Scheduler stopped")


def main() -> int:
    """Main entry point."""
    settings = get_settings()

    logger.info(
        "Polymarket Trading System starting",
        poll_interval=settings.poll_interval_seconds,
    )

    # Validate configuration
    if not settings.supabase_url or not settings.supabase_key:
        logger.error("SUPABASE_URL and SUPABASE_KEY must be set")
        return 1

    # Check for single-run mode
    if "--once" in sys.argv:
        run_once()
        return 0

    # Run continuously
    run_continuously()
    return 0


if __name__ == "__main__":
    sys.exit(main())
