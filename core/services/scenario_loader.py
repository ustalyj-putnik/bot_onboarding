from pathlib import Path
import json
from functools import lru_cache
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal
from core.config import settings
from sentence_transformers import SentenceTransformer, util
import numpy as np

SCENARIO_DIR = Path(settings.SCENARIO_DIR).resolve()
EMB_MODEL = settings.EMB_MODEL_NAME
_model = SentenceTransformer(EMB_MODEL)

# ---------- Pydantic модели ----------
class Step(BaseModel):
    text: str
    expected_answers: List[str]
    common_mistakes: List[str] = Field(default_factory=list)
    hint: Optional[str] = None
    on_correct: str
    on_incorrect: str
    max_retries: int | None = None

class Scenario(BaseModel):
    id: str
    title: str
    description: str
    steps: Dict[str, Step]
    outcomes: Dict[str, str]
    max_retries: int = 1


# ---------- Загрузка ----------
@lru_cache                         # кэшируем разбор, чтобы читать 1 раз
def _load_raw() -> Dict[str, Scenario]:
    scenarios: dict[str, Scenario] = {}
    for file in SCENARIO_DIR.glob("*.json"):
        with file.open(encoding="utf-8") as f:
            data = json.load(f)
            scenario = Scenario.model_validate(data)
            scenarios[scenario.id] = scenario
    return scenarios


# ---------- API для бота ----------
def list_scenarios() -> list[tuple[str, str]]:
    """Вернуть [(id, title), ...] для меню выбора."""
    return [(s.id, s.title) for s in _load_raw().values()]


def get_scenario(scenario_id: str) -> Scenario:
    return _load_raw()[scenario_id]

def precompute_embeddings() -> None:
    """Пройтись по всем сценариям и посчитать эмбеддинги эталонных
    и ошибочных ответов. Сохраняем прямо внутрь объектов Step
    (step._exp_emb, step._mist_emb) для быстрого доступа."""
    scenarios = _load_raw()
    for sc in scenarios.values():
        for st in sc.steps.values():
            st._exp_emb = _model.encode(st.expected_answers, convert_to_tensor=True)
            st._mist_emb = _model.encode(st.common_mistakes, convert_to_tensor=True) \
                if st.common_mistakes else None