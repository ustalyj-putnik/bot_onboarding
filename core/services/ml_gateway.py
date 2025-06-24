import time

from aiogram.utils.exceptions import ChatNotFound

from core.db import InteractionLog, User
from core.services.base import get_session
from bot_app.bootstrap import bot  # для получения имени
from ml_service.inference import answer as rag_answer
from monitoring.prometheus import RAG_LATENCY
from bot_app.keyboards import ml_rating_keyboard
from ml_service.llm_runner import remote_llm
from enum import Enum
from sentence_transformers import SentenceTransformer, util
from core.services.scenario_loader import get_scenario
from core.config import settings

EMB_MODEL = settings.EMB_MODEL_NAME

_st_model = SentenceTransformer(EMB_MODEL)

SIM_CORRECT  = 0.80
SIM_PARTIAL  = 0.60

class AnswerRating(str, Enum):
    correct = "correct"
    partial = "partial"
    incorrect = "incorrect"


class MLGateway:
    @staticmethod
    async def _ensure_user(session, user_id: int) -> None:
        """Вспомогательный метод для проверки пользователя. Использует внешнюю сессию."""
        if await session.get(User, user_id) is None:
            try:
                tg_user = await bot.get_chat(user_id)
                full_name = tg_user.full_name
            except ChatNotFound:
                full_name = None
            session.add(User(id=user_id, full_name=full_name))
            await session.commit()

    @staticmethod
    async def answer(user_id: int, question: str) -> tuple:
        async with get_session() as session:  # ← Одна сессия на весь запрос!
            # 1. Проверяем пользователя
            await MLGateway._ensure_user(session, user_id)
            t0 = time.perf_counter()

            # 2. Запускаем RAG
            response = await rag_answer(question)

            latency_ms = int((time.perf_counter() - t0) * 1000)

            # 3. Логируем взаимодействие
            log = InteractionLog(
                    user_id=user_id,
                    msg_in=question,
                    msg_out=response,
                    is_ai=True,
                    latency_ms=latency_ms,
                )
            session.add(log)
            await session.commit()

            # -- метрика --
            RAG_LATENCY.observe(latency_ms / 1000)

            kb = ml_rating_keyboard(log)

            return response, kb, log.id

    @staticmethod
    async def evaluate_answer(
            user_id: int,
            user_answer: str,
            expected: list[str],
            mistakes: list[str] | None = None,
            *,
            scenario_id: str | None = None,
            step_id: str | None = None,
            attempt: int | None = None,
            run_id: str | None = None
    ) -> AnswerRating:
        async with get_session() as s:
            """
            1) Пытаемся семантически сравнить эмбеддинги (быстро).
            2) Если результат 'partial' – уточняем через Saiga, чтобы
               не завалить пограничные случаи.
            """
            usr_emb = _st_model.encode(user_answer, convert_to_tensor=True)

            # --- косинус к эталону ---
            exp_emb = _st_model.encode(expected, convert_to_tensor=True)
            sim_max = util.cos_sim(usr_emb, exp_emb).max().item()

            if sim_max >= SIM_CORRECT:
                rating = AnswerRating.correct
            elif sim_max >= SIM_PARTIAL:
                rating = AnswerRating.partial
            else:
                rating = AnswerRating.incorrect

            # --- уточняем через Saiga, только если partial ---
            if rating == AnswerRating.partial:
                prompt = (
                    "Ты – обученный ассистент, который оценивает ответы стажёра. Оцени следующее:\n"
                    f"Эталонные ответы:\n{expected}\n\n"
                    f"Ответ стажёра:\n{user_answer}\n\n"
                    "Верни ровно одно слово: correct / partial / incorrect."
                )
                llm_resp = remote_llm(prompt, stop=["###"], max_tokens=20)
                llm_resp = llm_resp.strip().lower()
                if llm_resp.startswith("correct"):
                    rating = AnswerRating.correct
                elif llm_resp.startswith("incorrect"):
                    rating = AnswerRating.incorrect
                # иначе остаётся partial

            # --- логируем ---
            if scenario_id and step_id:
                log = InteractionLog(
                    user_id=user_id,
                    scenario_id=scenario_id,
                    step_id=step_id,
                    attempt_no=attempt,
                    run_id=run_id,
                    msg_in=user_answer,
                    scenario_rating=rating.value,
                    sim_score=sim_max,
                    is_ai=False
                )
                s.add(log)
                await s.commit()

            return rating
    '''@staticmethod
    async def evaluate_answer(
            user_id: int,
            user_answer: str,
            expected: list[str],
            mistakes: list[str] | None = None,
    ) -> AnswerRating:
        """
        Вызывает Saiga LLM с системным промптом:
        «Оцени сходство ответа пользователя с эталонами...».
        Возвращает AnswerRating.
        """
        prompt = (
            "Ты – обученный ассистент, который оценивает ответы стажёра. Оцени следующее:\n"
            f"Эталонные ответы:\n{expected}\n\n"
            f"Ответ стажёра:\n{user_answer}\n\n"
            "Верни ровно одно слово: correct / partial / incorrect."
        )
        # низкоуровневый вызов (пример)
        result = await remote_llm(prompt, stop=["###"], max_tokens=20)
        result = result.strip().lower()

        if "correct" in result:
            return AnswerRating.correct
        if "partial" in result:
            return AnswerRating.partial
        return AnswerRating.incorrect'''

