import logging
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from scraper import scrape_all_files

logger = logging.getLogger(__name__)

def generate_endpoint(domain, url):
    name = url.replace("https://", "").replace("http://", "")
    name = name.replace("/", "-").replace(".", "_")
    if name.endswith("-"):
        name = name[:-1]
    return f"{name}"

def run_async_job():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(scrape_all_files())
        loop.close()
    except Exception as e:
        logger.error(f"Error in cronjob: {e}")

def start_cron_scraping(config):
    scheduler = BackgroundScheduler()
    cronjob_conf = config.get("cronjob", {})
    
    if not cronjob_conf:
        logger.info("No cronjob configuration")
        return
    
    cron_expr = cronjob_conf.get("crontab", "0 */5 * * *")
    parts = cron_expr.strip().split()
    
    if len(parts) != 5:
        logger.error("Crontab format in YAML is invalid (expected 5 fields).")
        return
    
    scheduler.add_job(
        run_async_job,
        CronTrigger(
            minute=parts[0],
            hour=parts[1],
            day=parts[2],
            month=parts[3],
            day_of_week=parts[4]
        ),
        name="scraping_job"
    )
    
    scheduler.start()
    logger.info(f"🕒 Cronjob scheduled with: {cron_expr}")
    return scheduler