import pytest
from datetime import datetime
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from core.services import LessonService
from core.services import MLGateway
from core.db import AsyncSessionLocal
from core.db import InteractionLog


@pytest.mark.asyncio
async def test_first_lesson_exists():
    lesson = await LessonService.first_of_stage(1)
    assert lesson is not None
    assert lesson.title == "start_msg"


@pytest.mark.asyncio
async def test_ml_gateway_logs_interaction():
    user_id = 999999  # тестовый
    q = "Тестовый вопрос"
    answer = await MLGateway.answer(user_id, q)
    assert isinstance(answer, str) and answer  # непустая строка

    async with AsyncSessionLocal() as s:
        logs = (
            (
                await s.execute(
                    InteractionLog.__table__.select().where(
                        InteractionLog.user_id == user_id,
                        InteractionLog.msg_in == q,
                    )
                )
            )
            .mappings()
            .all()
        )

    # должно появиться ровно одна запись
    assert len(logs) == 1
    assert logs[0]["msg_out"] == answer
    assert logs[0]["is_ai"] is True
    assert isinstance(logs[0]["ts"], datetime)