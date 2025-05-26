'''import os
from llama_cpp import Llama
from core.config import settings

MODEL_PATH = settings.MODEL_PATH
N_CTX = settings.N_CTX

_llm = None

def get_llm() -> Llama:
    global _llm
    if _llm is None:
        _llm = Llama(
            model_path=MODEL_PATH,
            n_ctx=N_CTX,
            n_threads=4,
            verbose=False,
        )
    return _llm'''

import os, requests, json, uuid, base64
from core.config import settings

ENDPOINT = settings.LLM_ENDPOINT
LLM_USER = settings.LLM_USER
LLM_PASS = settings.LLM_PASS
BASIC = base64.b64encode(f"{LLM_USER}:{LLM_PASS}".encode()).decode()
def remote_llm(prompt: str, **kw) -> str:
    payload = dict(
        prompt=prompt,
        max_tokens=kw.get("max_tokens", 256),
        temperature=kw.get("temperature", 0.3),
        top_p=kw.get("top_p", 0.9),
        stop=["###"],
        stream=False,
        id=str(uuid.uuid4())  # trace
    )
    headers = {"Content-Type": "application/json",
               "Authorization": f"Basic {BASIC}"}
    r = requests.post(f"{ENDPOINT}/completion", json=payload, headers=headers, timeout=600)
    r.raise_for_status()
    data = r.json()

    # ---- универсальный парсер ----
    if "choices" in data:  # новый формат
        return data["choices"][0]["text"].strip()
    if "content" in data:  # старый формат
        return data["content"].strip()
    raise RuntimeError(f"Unknown response format: {data}")

