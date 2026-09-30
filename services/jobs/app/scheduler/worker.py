from __future__ import annotations

from apscheduler.schedulers.blocking import BlockingScheduler

from app.settings import settings


def run_scheduler() -> None:
    scheduler = BlockingScheduler()
    scheduler.add_job(
        lambda: None,
        "cron",
        hour="6,18",
        minute="0",
        timezone=settings.discovery_timezone,
    )
    scheduler.start()
