# FILE: scheduler.py
# PURPOSE: Periodically run the alert dispatch with resilience, logging, and configurable interval
# USAGE: Configure environment in .env -> run: python scheduler.py

import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_MISSED
from datetime import datetime
from alert import send_forecast_to_all

# ---- Configuration ----
# Adjust these values if you want a different cadence or concurrency
JOB_INTERVAL_MINUTES = 30        # check every 30 minutes (adjust as needed)
JOB_JITTER_SECONDS = 60          # add up to 60s jitter to avoid thundering herd
THREAD_POOL_SIZE = 5             # number of worker threads for jobs
MISFIRE_GRACE_SECONDS = 300      # how long to accept missed runs (5 minutes)

# ---- Logging ----
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("weather-scheduler")


# ---- Event handlers ----
def job_error_listener(event):
    logger.error("Job raised an exception: %s", event.exception, exc_info=True)


def job_missed_listener(event):
    logger.warning("Job missed execution (misfire). Job id: %s", event.job_id)


# ---- Job wrapper ----
def scheduled_job():
    now = datetime.utcnow()
    logger.info("Scheduler triggered job at %s UTC", now.strftime("%Y-%m-%d %H:%M:%S"))
    try:
        send_forecast_to_all()
        logger.info("Job completed successfully.")
    except Exception as e:
        logger.exception("Unhandled error during job execution: %s", e)


# ---- Scheduler setup ----
def main():
    executors = {"default": ThreadPoolExecutor(THREAD_POOL_SIZE)}
    job_defaults = {"coalesce": True, "misfire_grace_time": MISFIRE_GRACE_SECONDS}

    scheduler = BlockingScheduler(executors=executors, job_defaults=job_defaults)

    # Attach listeners for visibility
    scheduler.add_listener(job_error_listener, EVENT_JOB_ERROR)
    scheduler.add_listener(job_missed_listener, EVENT_JOB_MISSED)

    # Schedule the job
    scheduler.add_job(
        scheduled_job,
        trigger="interval",
        minutes=JOB_INTERVAL_MINUTES,
        jitter=JOB_JITTER_SECONDS,
        id="weather_alert_dispatch",
        replace_existing=True,
    )

    logger.info(
        "Scheduler started. Job 'weather_alert_dispatch' running every %s minutes (jitter=%s seconds).",
        JOB_INTERVAL_MINUTES,
        JOB_JITTER_SECONDS,
    )

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped by user.")
    except Exception as e:
        logger.exception("Scheduler terminated unexpectedly: %s", e)


if __name__ == "__main__":
    main()