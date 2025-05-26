import time

from aiogram.utils.exceptions import ChatNotFound

from core.db import InteractionLog, User
from core.services.base import get_session
from bot_app.bootstrap import bot  # для получения имени
from ml_service.inference import answer as rag_answer
from monitoring.prometheus import RAG_LATENCY
from bot_app.keyboards import ml_rating_keyboard


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
