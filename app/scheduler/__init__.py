import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.config.settings import settings
from app.services import process_pending_tasks

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def start_scheduler():
    scheduler.add_job(
        process_pending_tasks,
        "interval",
        seconds=settings.scheduler_interval,
        id="process_pending",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    logger.info("Scheduler started, interval=%ds", settings.scheduler_interval)


def stop_scheduler():
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")
