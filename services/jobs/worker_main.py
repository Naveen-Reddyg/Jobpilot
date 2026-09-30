import logging

from app.scheduler.worker import run_scheduler


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_scheduler()
