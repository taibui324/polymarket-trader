"""Background task scheduler."""

from typing import Callable, Optional
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from src.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TaskScheduler:
    """Background task scheduler using APScheduler."""

    def __init__(self) -> None:
        """Initialize scheduler."""
        settings = get_settings()
        self._scheduler = BlockingScheduler()
        self._poll_interval = settings.poll_interval_seconds

    def add_data_fetcher_job(self, func: Callable[[], int]) -> None:
        """Add data fetcher job.

        Args:
            func: Function to run for data fetching
        """
        self._scheduler.add_job(
            func,
            trigger=IntervalTrigger(seconds=self._poll_interval),
            id="data_fetcher",
            name="Data Fetcher",
            replace_existing=True,
        )
        logger.info("Added data fetcher job", interval=self._poll_interval)

    def add_scanner_job(self, func: Callable[[], int]) -> None:
        """Add scanner job.

        Args:
            func: Function to run for scanning
        """
        # Run scanner less frequently than data fetcher
        self._scheduler.add_job(
            func,
            trigger=IntervalTrigger(seconds=self._poll_interval * 2),
            id="scanner",
            name="Market Scanner",
            replace_existing=True,
        )
        logger.info("Added scanner job", interval=self._poll_interval * 2)

    def start(self) -> None:
        """Start the scheduler."""
        logger.info("Starting scheduler")
        self._scheduler.start()

    def shutdown(self) -> None:
        """Shutdown the scheduler."""
        logger.info("Shutting down scheduler")
        self._scheduler.shutdown()

    def list_jobs(self) -> list[dict[str, str]]:
        """List scheduled jobs.

        Returns:
            List of job info
        """
        jobs = []
        for job in self._scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time) if job.next_run_time else None,
            })
        return jobs


# Global instance
_scheduler: Optional[TaskScheduler] = None


def get_scheduler() -> TaskScheduler:
    """Get global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = TaskScheduler()
    return _scheduler
