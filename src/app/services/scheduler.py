"""Background scheduler for automated Sambatan lifecycle management."""

import logging
from datetime import UTC, datetime
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.services.sambatan import SambatanLifecycleService, sambatan_lifecycle_service

logger = logging.getLogger(__name__)


class SambatanScheduler:
    """Background scheduler for running Sambatan lifecycle transitions."""

    def __init__(
        self,
        lifecycle_service: Optional[SambatanLifecycleService] = None,
        interval_minutes: int = 5
    ):
        """Initialize the scheduler.
        
        Args:
            lifecycle_service: Service to use for lifecycle transitions
            interval_minutes: How often to run lifecycle checks (default: 5 minutes)
        """
        self.lifecycle_service = lifecycle_service or sambatan_lifecycle_service
        self.interval_minutes = interval_minutes
        self.scheduler: Optional[BackgroundScheduler] = None
        self._is_running = False

    def start(self) -> None:
        """Start the background scheduler."""
        if self._is_running:
            logger.warning("Scheduler is already running")
            return

        self.scheduler = BackgroundScheduler(timezone="UTC")
        
        # Add job to run lifecycle transitions
        self.scheduler.add_job(
            func=self._run_lifecycle_job,
            trigger=IntervalTrigger(minutes=self.interval_minutes),
            id='sambatan_lifecycle',
            name='Run Sambatan lifecycle transitions',
            replace_existing=True,
            max_instances=1,  # Prevent overlapping executions
        )
        
        self.scheduler.start()
        self._is_running = True
        
        logger.info(
            f"Sambatan scheduler started - running every {self.interval_minutes} minutes"
        )

    def stop(self) -> None:
        """Stop the background scheduler."""
        if not self._is_running or not self.scheduler:
            logger.warning("Scheduler is not running")
            return

        self.scheduler.shutdown(wait=True)
        self._is_running = False
        logger.info("Sambatan scheduler stopped")

    def run_now(self) -> None:
        """Manually trigger a lifecycle check immediately."""
        logger.info("Manually triggering Sambatan lifecycle check")
        self._run_lifecycle_job()

    def _run_lifecycle_job(self) -> None:
        """Execute the lifecycle transition job."""
        try:
            now = datetime.now(UTC)
            logger.debug(f"Running Sambatan lifecycle check at {now}")
            
            transitions = self.lifecycle_service.run(now=now)
            
            if transitions:
                logger.info(
                    f"Sambatan lifecycle check completed: {len(transitions)} transition(s) occurred"
                )
                for transition in transitions:
                    logger.info(
                        f"  - Campaign {transition.campaign_id}: {transition.event}"
                    )
            else:
                logger.debug("Sambatan lifecycle check completed: no transitions")
                
        except Exception as exc:
            logger.error(f"Error running Sambatan lifecycle job: {exc}", exc_info=True)

    @property
    def is_running(self) -> bool:
        """Check if scheduler is currently running."""
        return self._is_running

    def get_next_run_time(self) -> Optional[datetime]:
        """Get the next scheduled run time."""
        if not self.scheduler or not self._is_running:
            return None
        
        job = self.scheduler.get_job('sambatan_lifecycle')
        if job:
            return job.next_run_time
        return None


# Global scheduler instance
_scheduler_instance: Optional[SambatanScheduler] = None


def get_scheduler(
    lifecycle_service: Optional[SambatanLifecycleService] = None,
    interval_minutes: int = 5
) -> SambatanScheduler:
    """Get or create the global scheduler instance.
    
    Args:
        lifecycle_service: Service to use for lifecycle transitions
        interval_minutes: How often to run lifecycle checks (default: 5 minutes)
    
    Returns:
        The global scheduler instance
    """
    global _scheduler_instance
    
    if _scheduler_instance is None:
        _scheduler_instance = SambatanScheduler(
            lifecycle_service=lifecycle_service,
            interval_minutes=interval_minutes
        )
    
    return _scheduler_instance


def start_scheduler(interval_minutes: int = 5) -> SambatanScheduler:
    """Start the global scheduler instance.
    
    Args:
        interval_minutes: How often to run lifecycle checks (default: 5 minutes)
    
    Returns:
        The started scheduler instance
    """
    scheduler = get_scheduler(interval_minutes=interval_minutes)
    scheduler.start()
    return scheduler


def stop_scheduler() -> None:
    """Stop the global scheduler instance if it exists."""
    global _scheduler_instance
    
    if _scheduler_instance:
        _scheduler_instance.stop()
