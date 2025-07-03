# rh-server

Robin Hood Server

## Overview

**rh-server** is a FastAPI-based backend service for scraping, aggregating, and serving `.m3u8` streaming playlist files from configurable sources. It automates the extraction of streaming links from various domains, stores them in the `assets/` directory, and exposes endpoints to access, refresh, and manage these playlists.

## Features

- Scrapes `.m3u8` streaming links from user-defined URLs using Playwright and BeautifulSoup.
- Stores playlists in the `assets/` directory in standard M3U format.
- Exposes REST API endpoints to:
  - List available assets
  - Retrieve metadata about sources and channels
  - Download individual `.m3u8` files
  - Trigger a manual refresh (scraping)
  - Check server and scheduler status
- Supports scheduled scraping via a configurable cronjob.
- Docker-ready for easy deployment.

## Installation

### Requirements
- Python 3.8+
- [Playwright](https://playwright.dev/python/) dependencies (installed automatically via Docker or `requirements.txt`)

### Local Setup

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd rh-server
   ```
2. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   playwright install
   ```
3. **Copy and edit the configuration:**
   ```bash
   cp config.yaml.sample config.yaml
   # Edit config.yaml to add your domains and channels
   ```
4. **Run the server:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

### Docker

1. **Build the image:**
   ```bash
   docker build -t rh-server .
   ```
2. **Run the container:**
   ```bash
   docker run -p 8000:8000 -v $(pwd)/assets:/app/assets -v $(pwd)/config.yaml:/app/config.yaml rh-server
   ```

## Configuration

Edit `config.yaml` to define the domains and channels to scrape. Example:

```yaml
domain.com:
  - https://domain.com/channel1/
  - https://domain.com/channel2/

cronjob:
  crontab: "0 */5 * * *"  # Every 5 hours (standard crontab format)
```

- Each domain key contains a list of URLs to scrape for `.m3u8` links.
- The `cronjob` section configures the scraping schedule (optional).

## API Endpoints

- `GET /status` — Returns server, scheduler, and scraping status.
- `GET /assets` — Lists all available `.m3u8` files.
- `GET /assets/metadata` — Returns metadata about all configured domains and channels.
- `POST /assets/refresh` — Triggers a background scraping job (manual refresh).
- `GET /assets/{file}.m3u8` — Downloads a specific playlist file.

## Example Usage

- **List assets:**
  ```bash
  curl http://localhost:8000/assets
  ```
- **Trigger manual refresh:**
  ```bash
  curl -X POST http://localhost:8000/assets/refresh
  ```
- **Download a playlist:**
  ```bash
  curl http://localhost:8000/assets/<file>.m3u8
  ```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

**Credits:** Developed by wetdreams69
