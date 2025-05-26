import os
import json
import aiohttp
import asyncio
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

API_URL = f"{os.environ['JIRA_URL'].rstrip('/')}/rest/api/2"
TOKEN = os.environ["JIRA_TOKEN"]
JQL = os.getenv("JIRA_JQL", "")

RAW_DIR = Path("ml_service/data_ingest/raw/jira")
RAW_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "Authorization": f"Bearer {TOKEN.split()[-1]}",  # или "Basic {TOKEN}"
    "Accept": "application/json",
    "Content-Type": "application/json"
}

FIELDS = [
    "summary",
    "description",
    "status",
    "assignee",
    "reporter",
    "created",
    "updated",
    "priority",
    "labels",
    "issuetype",
    "project",
    "comment",
    "attachment",
    "subtasks",
    "parent",
    "duedate",
    "resolution",
    "resolutiondate",
    "worklog",
    "timeoriginalestimate",
    "timeestimate",
    "timespent"
]

async def fetch_issues(session, start_at=0):
    fields_param = ",".join(FIELDS)
    url = f"{API_URL}/search?jql={quote_plus(JQL)}&startAt={start_at}&maxResults=100&fields={fields_param}"

    try:
        async with session.get(url, headers=HEADERS) as r:
            if r.status != 200:
                error_text = await r.text()
                logger.error(f"Error {r.status}: {error_text}")
                r.raise_for_status()

            try:
                data = await r.json()
                return data.get("issues", [])
            except Exception as e:
                error_text = await r.text()
                logger.error(f"Failed to parse JSON: {e}, response: {error_text}")
                raise
    except Exception as e:
        logger.error(f"Request failed: {e}")
        raise


async def main():
    async with aiohttp.ClientSession() as session:
        start_at = 0
        while True:
            issues = await fetch_issues(session, start_at)
            if not issues:
                break

            for issue in issues:
                key = issue["key"]
                file_path = RAW_DIR / f"{key}.json"
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(issue, f, ensure_ascii=False, indent=2)
                logger.info(f"Saved issue: {key}")

            start_at += len(issues)


if __name__ == "__main__":
    asyncio.run(main())