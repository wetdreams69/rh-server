import os
import logging
import asyncio
from fastapi import FastAPI
from fastapi.responses import FileResponse, Response
from contextlib import asynccontextmanager
from config import (
    ensure_assets_directory,
    load_configuration,
)
from utils import start_cron_scraping
from scraper import scrape_all_files

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = None
scheduler = None
scraping_status = {"running": False, "last_run": None, "error": None}

@asynccontextmanager
async def lifespan(app: FastAPI):
    global config, scheduler
    logger.info("🔧 Initializing server...")
    
    try:
        ensure_assets_directory()
        config = load_configuration()
        
        assets_files = [f for f in os.listdir("assets") if f.endswith('.m3u8')] if os.path.exists("assets") else []
        
        if not assets_files:
            logger.info("📁 Assets folder empty, running initial scraping...")
            await scrape_all_files()
        else:
            logger.info(f"📁 Found {len(assets_files)} files in assets, skipping initial scraping")
        
        cronjob_conf = config.get("cronjob", {})
        if cronjob_conf:
            logger.info("⏲️  Starting cronjob...")
            scheduler = start_cron_scraping(config)
        
        logger.info("✅ Server initialized successfully")
        
    except Exception as e:
        logger.error(f"Error in initialization: {e}")
        raise
    
    yield
    
    logger.info("🛑 Shutting down server...")
    if scheduler:
        scheduler.shutdown(wait=True)
        logger.info("🛑 Scheduler stopped")

app = FastAPI(lifespan=lifespan)

@app.get("/status")
def status():
    global scheduler
    scheduler_info = {}
    if scheduler:
        jobs = scheduler.get_jobs()
        scheduler_info = {
            "scheduler_running": scheduler.running,
            "jobs_count": len(jobs),
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": str(job.next_run_time) if job.next_run_time else None
                }
                for job in jobs
            ]
        }
    
    return {
        "status": "Ok.",
        "scheduler": scheduler_info,
        "assets_files": os.listdir("assets") if os.path.exists("assets") else [],
        "scraping": scraping_status
    }

@app.get("/metadata")
def metadata():
    try:
        config = load_configuration()
        data = []
        
        for domain, urls in config.items():
            if domain == "cronjob":
                continue
            
            site = domain
            channels = []
            
            for url in urls:
                path_parts = [p for p in url.split("/") if p]
                if len(path_parts) >= 2:
                    name = "-".join(path_parts[-2:])
                else:
                    name = path_parts[-1] if path_parts else "channel"
                
                name = name.replace(":", "").replace(".", "_")
                endpoint = f"{domain.replace('.', '_')}-{name}"
                
                channels.append({
                    "channel": name,
                    "endpoint": endpoint,
                    "url": url
                })
            
            data.append({"site": site, "channels": channels})
        
        return data
        
    except Exception as e:
        logger.error(f"Error generating metadata: {e}")
        return Response(f"Error: {str(e)}", status_code=500)

async def execute_background_scraping():
    global scraping_status
    try:
        scraping_status["running"] = True
        scraping_status["error"] = None
        await scrape_all_files()
        scraping_status["last_run"] = "successful"
        logger.info("✅ Background scraping completed")
    except Exception as e:
        scraping_status["error"] = str(e)
        scraping_status["last_run"] = "error"
        logger.error(f"❌ Error in background scraping: {e}")
    finally:
        scraping_status["running"] = False

@app.post("/refresh")
async def refresh():
    global scraping_status
    
    if scraping_status["running"]:
        return Response(
            content='{"status": "already_running", "message": "Scraping is already in progress"}',
            status_code=409,
            media_type="application/json"
        )
    
    try:
        logger.info("🔄 Starting manual refresh...")
        
        asyncio.create_task(execute_background_scraping())
        
        return Response(
            content='{"status": "processing", "message": "Scraping started in background"}',
            status_code=201,
            media_type="application/json"
        )
    except Exception as e:
        logger.error(f"Error starting refresh: {e}")
        return Response(f'{{"error": "{str(e)}"}}', status_code=500, media_type="application/json")

@app.get("/{file}")
def get_file(file: str):
    file_path = f"assets/{file}.m3u8"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/vnd.apple.mpegurl")
    return Response("File not found", status_code=404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)