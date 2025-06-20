import os
import re
import aiohttp
import asyncio
import logging
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from config import load_configuration

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/114.0.0.0 Safari/537.36"
}

REGEX_M3U8 = re.compile(r'https?://[^\s"\']+\.m3u8')

async def validate_url(url):
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.head(url, allow_redirects=True, timeout=10) as r:
                if r.status == 200:
                    return True
            async with session.get(url, allow_redirects=True, timeout=10) as r:
                return r.status == 200
    except Exception as e:
        logger.debug(f"Error validating URL {url}: {e}")
        return False

async def get_html(url):
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url, timeout=10) as r:
                r.raise_for_status()
                return await r.text()
    except Exception as e:
        logger.debug(f"Error getting HTML from {url}: {e}")
        return None

async def get_html_with_playwright(page, url):
    try:
        await page.goto(url, timeout=15000)
        await page.wait_for_timeout(3000)
        return await page.content()
    except Exception as e:
        logger.debug(f"Error with Playwright on {url}: {e}")
        return None

async def capture_m3u8_by_network(page, url):
    urls = []

    async def on_response(response):
        if ".m3u8" in response.url:
            urls.append(response.url)

    page.on("response", on_response)

    try:
        await page.goto(url, timeout=15000)
        await page.wait_for_timeout(4000)
    except Exception as e:
        logger.debug(f"Error capturing by network on {url}: {e}")

    return urls

async def scrape_url(page, url):
    found_urls = set()

    html = await get_html(url)
    if html:
        found_urls.update(REGEX_M3U8.findall(html))

    html_js = await get_html_with_playwright(page, url)
    if html_js:
        found_urls.update(REGEX_M3U8.findall(html_js))

    network_urls = await capture_m3u8_by_network(page, url)
    found_urls.update(network_urls)

    valid_urls = await validate_urls_async(list(found_urls))
    return valid_urls

async def validate_urls_async(urls):
    if not urls:
        return []
    
    results = await asyncio.gather(*(validate_url(url) for url in urls), return_exceptions=True)
    valid_urls = []
    
    for url, result in zip(urls, results):
        if not isinstance(result, Exception) and result:
            valid_urls.append(url)
    
    return valid_urls

def generate_filename(domain, url):
    name = url.replace("https://", "").replace("http://", "")
    name = name.replace("/", "-").replace(".", "_")
    if name.endswith("-"):
        name = name[:-1]
    return f"{name}.m3u8"

async def scrape_all_files():
    config = load_configuration()
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            for domain, urls in config.items():
                if domain == "cronjob":
                    continue

                for url in urls:
                    logger.info(f"🔍 Scraping: {url}")
                    
                    try:
                        page = await browser.new_page()
                        m3u8_urls = await scrape_url(page, url)
                        await page.close()

                        if not m3u8_urls:
                            logger.warning(f"❌ No URLs found for {url}")
                            continue

                        filename = generate_filename(domain, url)
                        path = os.path.join("assets", filename)

                        with open(path, "w", encoding="utf-8") as f:
                            f.write("#EXTM3U\n")
                            for i, link in enumerate(m3u8_urls, 1):
                                f.write(f"#EXTINF:-1,Option {i}\n{link}\n")
                        
                        logger.info(f"✅ Saved: {path}")
                        
                    except Exception as e:
                        logger.error(f"Error processing {url}: {e}")
                        
            await browser.close()
            logger.info("🏁 Scraping completed")
            
    except Exception as e:
        logger.error(f"Error in general scraping: {e}")
        raise