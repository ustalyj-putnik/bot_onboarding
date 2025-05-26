import uuid
import asyncio
import pandas as pd
from sentence_transformers import SentenceTransformer
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qdm
from core.config import settings
import logging
from datetime import datetime
from tqdm.auto import tqdm

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHUNKS_PATH = "ml_service/data_ingest/chunks.parquet"
COLL = "onboard_docs"
QDRANT_URL = settings.QDRANT_URL

BATCH = 256
EMB_MODEL = settings.EMB_MODEL_NAME


def clean_payload(payload: dict) -> dict:
    """Очистка payload от проблемных типов данных"""
    cleaned = {}
    for key, value in payload.items():
        if pd.isna(value):
            cleaned[key] = None
        elif isinstance(value, (datetime, pd.Timestamp)):
            cleaned[key] = value.isoformat()
        elif isinstance(value, (int, str, bool)):
            cleaned[key] = value
        elif isinstance(value, float):
            # Проверяем, является ли float целым числом
            if value.is_integer():
                cleaned[key] = int(value)
            else:
                cleaned[key] = value
        else:
            cleaned[key] = str(value)
    return cleaned


async def main():
    # Загрузка данных
    df = pd.read_parquet(CHUNKS_PATH)
    logger.info(f"Loaded {len(df)} chunks from {CHUNKS_PATH}")

    # Инициализация модели
    model = SentenceTransformer(EMB_MODEL, device="cpu")
    logger.info(f"Initialized model: {EMB_MODEL}")

    # Инициализация клиента Qdrant
    client = AsyncQdrantClient(url=QDRANT_URL)
    dim = model.get_sentence_embedding_dimension()
    logger.info(f"Qdrant client connected, embedding dimension: {dim}")

    # Создание коллекции (современный способ)
    collection_exists = await client.collection_exists(COLL)
    if collection_exists:
        await client.delete_collection(COLL)
    await client.create_collection(
        collection_name=COLL,
        vectors_config=qdm.VectorParams(size=dim, distance=qdm.Distance.COSINE),
    )
    logger.info(f"Collection {COLL} created/recreated")

    # Обработка батчами
    total = len(df)
    for i in tqdm(range(0, total, BATCH), desc="Processing batches"):
        batch = df.iloc[i: i + BATCH]

        # Генерация эмбеддингов
        embeds = model.encode(
            batch["chunk"].tolist(),
            show_progress_bar=True,
            normalize_embeddings=True,
            batch_size=32
        )

        # Подготовка точек
        points = []
        for idx, emb in enumerate(embeds):
            payload = clean_payload(batch.iloc[idx].to_dict())
            points.append(
                qdm.PointStruct(
                    id=str(uuid.uuid4()),  # Используем строковый UUID
                    vector=emb.tolist(),
                    payload=payload,
                )
            )

        # Загрузка в Qdrant
        try:
            await client.upsert(collection_name=COLL, points=points)
            logger.info(f"Processed batch {i // BATCH + 1}/{(total // BATCH) + 1} ({i + len(batch)}/{total})")
        except Exception as e:
            logger.error(f"Error processing batch {i // BATCH + 1}: {str(e)}")
            raise

    await client.close()
    logger.info("✅ Index built successfully")


if __name__ == "__main__":
    asyncio.run(main())