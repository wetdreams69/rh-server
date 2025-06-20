from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from utils import load_configuration
import logging

log = logging.getLogger("cronjob")

def start_cronjob(scrape_fn):
    config = load_configuration()
    cron_expr = config.get("cronjob", {}).get("crontab", "0 */5 * * *")
    parts = cron_expr.strip().split()
    
    if len(parts) != 5:
        raise ValueError("Crontab format in YAML is invalid (expected 5 fields).")

    scheduler = BackgroundScheduler()
    scheduler.add_job(scrape_fn, CronTrigger(
        minute=parts[0],
        hour=parts[1],
        day=parts[2],
        month=parts[3],
        day_of_week=parts[4]
    ))
    scheduler.start()
    log.info(f"🕒 Cronjob started with schedule: '{cron_expr}'")