#import os, asyncio
from sentence_transformers import SentenceTransformer
from qdrant_client import AsyncQdrantClient
#from qdrant_client.http import models as qdm
from ml_service.llm_runner import remote_llm
from core.config import settings

EMB_MODEL = settings.EMB_MODEL_NAME
QDRANT_URL = settings.QDRANT_URL
COLL = "onboard_docs"
TOP_K = int(settings.TOP_K)

emb_model = SentenceTransformer(EMB_MODEL, device="cpu")
client = AsyncQdrantClient(url=QDRANT_URL)

PROMPT_TEMPLATE = """Ты — помощник-эксперт компании ТЦИ. Используй только контекст,
чтобы ответить строго по делу, кратко, на русском, если проще дать ссылку на страницу в Confluence или Jira - сделай это.

### Контекст
{context}

### Вопрос
{question}

### Ответ
"""

async def answer(question: str) -> str:
    q_vec = emb_model.encode(question, normalize_embeddings=True).tolist()

    hits = await client.search(
        collection_name=COLL,
        query_vector=q_vec,
        limit=TOP_K,
        with_payload=True,
    )

    context_parts = [h.payload["chunk"] for h in hits]
    context = "\n---\n".join(context_parts)

    #llm = get_llm()
    full_prompt = PROMPT_TEMPLATE.format(context=context, question=question)

    resp = remote_llm(full_prompt, stop=["###"] , max_tokens=256)
    return resp.strip()
