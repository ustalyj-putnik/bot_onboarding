import os, json, aiohttp, asyncio
from pathlib import Path
from urllib.parse import quote
from dotenv import load_dotenv
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()  # Загружает переменные из .env файла

API_URL = f"{os.environ['CONFLUENCE_URL'].rstrip('/')}"
SPACE    = os.getenv("CONFLUENCE_SPACE", "")
TOKEN    = os.environ["CONFLUENCE_TOKEN"]            # Basic …  или  Bearer …

RAW_DIR  = Path("ml_service/data_ingest/raw/confluence")
RAW_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "Authorization": TOKEN if TOKEN.startswith("Bearer") else f"Basic {TOKEN}",
    "Accept": "application/json"
}


async def fetch(session, url):
    async with session.get(url, headers=HEADERS) as r:
        r.raise_for_status()
        return await r.json()


async def save_page(session, page):
    page_id = page["id"]
    data = await fetch(session, f"{API_URL}/rest/api/content/{page_id}?expand=body.storage,version")
    with open(RAW_DIR / f"{page_id}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("✔", page["title"])


async def main():
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{API_URL}/rest/api/content?limit=100&spaceKey={quote(SPACE)}&type=page"
            page_num = 1

            while url:
                logger.info(f"Fetching page {page_num}...")
                try:
                    data = await fetch(session, url)

                    if "results" not in data:
                        logger.error("Invalid API response: no 'results' field")
                        break

                    tasks = [save_page(session, p) for p in data["results"]]
                    await asyncio.gather(*tasks)

                    # Проверка пагинации
                    if "_links" not in data or "next" not in data["_links"]:
                        logger.info("Reached the last page")
                        break

                    next_url = data["_links"]["next"]
                    if not next_url.startswith("/rest/api"):
                        logger.warning(f"Unexpected next URL: {next_url}")
                        break

                    url = f"{API_URL}{next_url}"
                    page_num += 1
                    await asyncio.sleep(1)  # Пауза

                except aiohttp.ClientResponseError as e:
                    if e.status == 404:
                        logger.warning(f"Page not found, stopping: {url}")
                        break
                    raise

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())