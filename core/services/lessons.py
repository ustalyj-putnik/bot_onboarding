from typing import List, Optional
from sqlalchemy import select
from core.db import Lesson, Section
from core.services.base import get_session

class LessonService:
    @staticmethod
    async def first_lesson(section_id: int):
        async with get_session() as s:
            q = (select(Lesson)
                 .where(Lesson.section_id == section_id)
                 .order_by(Lesson.order).limit(1))
            return (await s.execute(q)).scalar_one()

    @staticmethod
    async def get(lesson_id: str):
        async with get_session() as s:
            return (await s.get(Lesson, lesson_id))

    @staticmethod
    async def next_lesson(current_id: int):
        async with get_session() as s:
            cur: Lesson = await s.get(Lesson, current_id)
            q = (select(Lesson)
                 .where(Lesson.section_id == cur.section_id,
                        Lesson.order > cur.order)
                 .order_by(Lesson.order).limit(1))
            return (await s.execute(q)).scalar_one_or_none()

    @staticmethod
    async def prev_lesson(current_id: int):
        async with get_session() as s:
            cur: Lesson = await s.get(Lesson, current_id)
            q = (select(Lesson)
                 .where(Lesson.section_id == cur.section_id,
                        Lesson.order < cur.order)
                 .order_by(Lesson.order.desc()).limit(1))
            return (await s.execute(q)).scalar_one_or_none()