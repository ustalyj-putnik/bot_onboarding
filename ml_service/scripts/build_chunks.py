import re
import json
import html
from pathlib import Path
from bs4 import BeautifulSoup
import pandas as pd
from tqdm.auto import tqdm
from datetime import datetime
from typing import Dict, Any, List, Tuple
import logging
from bs4 import MarkupResemblesLocatorWarning, XMLParsedAsHTMLWarning
import warnings
from typing import Union

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RAW_DIR = Path("ml_service/data_ingest/raw")
OUT_FILE = Path("ml_service/data_ingest/chunks.parquet")

MIN_LEN = 200  # минимальная длина чанка
MAX_LEN = 500  # максимальная длина чанка
OVERLAP = 50  # перекрытие между чанками

# Отключаем предупреждение о тексте, похожем на URL
warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

# Фильтрация всех специфических предупреждений BeautifulSoup
warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


def clean_html(text: Union[str, bytes, None]) -> str:
    """
    Универсальная очистка HTML/XML контента с автоматическим определением типа.
    Возвращает чистый текст с сохранением значимого содержимого.
    """
    if not text:
        return ""

    if isinstance(text, bytes):
        text = text.decode('utf-8', errors='ignore')

    # Определяем тип контента
    is_xml = '<?xml' in text[:100].lower()
    is_html = '<html' in text[:100].lower() or '<!doctype html' in text[:100].lower()

    try:
        # Выбираем подходящий парсер
        parser = 'lxml-xml' if is_xml and not is_html else 'lxml'
        soup = BeautifulSoup(text, parser)

        # Удаляем ненужные элементы
        for tag in soup(["script", "style", "img", "table", "iframe", "head", "meta"]):
            tag.decompose()

        # Получаем текст с сохранением структуры
        text = soup.get_text("\n", strip=True)
        return html.unescape(text) if text else ""

    except Exception as e:
        logger.debug(f"Content cleaning failed (type: {'XML' if is_xml else 'HTML'}): {str(e)}")
        # Возвращаем текст с базовой очисткой
        return html.unescape(re.sub(r'<[^>]+>', '', str(text))).strip()


def chunk(text: str, min_len: int = MIN_LEN, max_len: int = MAX_LEN, overlap: int = OVERLAP) -> List[str]:
    """Разбивка текста на чанки с перекрытием"""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i: i + max_len]
        chunk_text = " ".join(chunk)
        if len(chunk_text) >= min_len:
            chunks.append(chunk_text)
        i += max_len - overlap
    return chunks


def parse_jira_date(date_str: str) -> datetime:
    """Парсинг даты из Jira с обработкой неполного формата временной зоны"""
    if not date_str:
        return None

    try:
        # Пробуем стандартный ISO формат
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except ValueError:
        try:
            # Пытаемся исправить неполную временную зону (например, +030 → +0300)
            if len(date_str.split('+')[-1]) == 3:
                date_str = date_str[:-1] + '0' + date_str[-1:]
            elif date_str.endswith('Z'):
                date_str = date_str[:-1] + '+0000'
            return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%f%z')
        except ValueError:
            # Если не удалось распарсить, возвращаем None
            return None


def safe_get(dct: Dict, *keys, default=None):
    """Безопасное получение значения из словаря с вложенностью"""
    for key in keys:
        try:
            dct = dct.get(key, {})
        except AttributeError:
            return default
    return dct if dct != {} else default


def extract_jira_metadata(issue: Dict[str, Any]) -> Dict[str, Any]:
    """Извлечение метаданных из Jira issue с защитой от отсутствующих полей"""
    fields = issue.get("fields", {})

    # Получаем комментарии безопасно
    comment_data = safe_get(fields, "comment", "comments", default=[])

    metadata = {
        "issue_key": issue.get("key", ""),
        "issue_type": safe_get(fields, "issuetype", "name", default=""),
        "status": safe_get(fields, "status", "name", default=""),
        "priority": safe_get(fields, "priority", "name", default=""),
        "assignee": safe_get(fields, "assignee", "displayName", default=""),
        "reporter": safe_get(fields, "reporter", "displayName", default=""),
        "created": parse_jira_date(fields.get("created")),
        "updated": parse_jira_date(fields.get("updated")),
        "resolution": safe_get(fields, "resolution", "name", default=""),
        "resolution_date": parse_jira_date(fields.get("resolutiondate")),
        "labels": ", ".join(fields.get("labels", [])),
        "project": safe_get(fields, "project", "name", default=""),
        "components": ", ".join([c.get("name", "") for c in fields.get("components", [])]),
        "time_original_estimate": fields.get("timeoriginalestimate"),
        "time_spent": fields.get("timespent"),
        "comments_count": len(comment_data),
        "attachments_count": len(fields.get("attachment", [])),
        "url": f"{issue.get('self', '').split('/rest/api')[0]}/browse/{issue.get('key', '')}"
    }

    # Обработка кастомных полей
    for field in fields:
        if field.startswith("customfield_"):
            field_value = fields[field]
            if isinstance(field_value, (dict, list)):
                field_value = str(field_value)[:200]
            metadata[field] = field_value

    return metadata


def parse_jira_issue(file_path: Path) -> Tuple[Dict[str, Any], str]:
    """Парсинг Jira issue файла с защитой от ошибок"""
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        fields = data.get("fields", {})

        # Безопасное извлечение текстовых полей
        description = clean_html(safe_get(fields, "description", default=""))
        summary = clean_html(safe_get(fields, "summary", default=""))

        # Обработка комментариев
        comments = "\n".join([
            clean_html(c.get("body", ""))
            for c in safe_get(fields, "comment", "comments", default=[])
        ])

        full_text = f"Задача: {summary}\n\n{description}\n\nКомментарии:\n{comments}"
        metadata = extract_jira_metadata(data)

        return metadata, full_text

    except Exception as e:
        logger.error(f"Failed to parse Jira issue {file_path}: {str(e)}")
        return {}, ""


def parse_confluence_page(file_path: Path) -> Tuple[Dict[str, Any], str]:
    """Парсинг Confluence страницы"""
    data = json.loads(file_path.read_text(encoding="utf-8"))
    metadata = {
        "title": data["title"],
        "url": data.get("_links", {}).get("base", "") + data.get("_links", {}).get("webui", ""),
        "type": "confluence_page"
    }
    html_text = data["body"]["storage"]["value"]
    return metadata, clean_html(html_text)


def parse_file(file_path: Path) -> List[Dict[str, Any]]:
    """Обработка файла и создание чанков"""
    if file_path.is_dir():
        return []

    try:
        if file_path.suffix == ".json":
            if "fields" in json.loads(file_path.read_text(encoding="utf-8")):
                metadata, text = parse_jira_issue(file_path)
            else:
                metadata, text = parse_confluence_page(file_path)
        else:  # .txt
            metadata = {"title": file_path.stem, "url": "", "type": "manual"}
            text = file_path.read_text(encoding="utf-8")

        chunks = []
        for chunk_text in chunk(text):  # Исправлено: используем функцию chunk()
            chunk_data = metadata.copy()
            chunk_data["chunk"] = chunk_text
            chunks.append(chunk_data)

        return chunks

    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return []


def main():
    """Основная функция обработки файлов"""
    all_chunks = []

    # Собираем все файлы рекурсивно
    files = list(RAW_DIR.rglob("*"))

    # Обрабатываем файлы с прогресс-баром
    for file in tqdm(files, desc="Processing files"):
        all_chunks.extend(parse_file(file))

    # Создаем DataFrame и сохраняем
    if all_chunks:
        df = pd.DataFrame(all_chunks)

        # Оптимизация типов данных
        for col in df.columns:
            if col.endswith("_date") or col in ["created", "updated"]:
                df[col] = pd.to_datetime(df[col])

        OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(OUT_FILE, index=False)
        print(f"✨ Saved {len(df)} chunks → {OUT_FILE}")
    else:
        print("⚠ No chunks were created!")


if __name__ == "__main__":
    main()