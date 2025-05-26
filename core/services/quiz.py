from typing import List, Tuple
from sqlalchemy import select
from core.db import QuizQuestion
from core.services.base import get_session

class QuizService:
    @staticmethod
    @staticmethod
    async def get_questions(section_id: int):
        async with get_session() as s:
            q = select(QuizQuestion).where(QuizQuestion.section_id == section_id)
            return (await s.execute(q)).scalars().all()

    @staticmethod
    def is_correct(question: QuizQuestion, option_idx: int) -> bool:
        return question.correct_option == option_idx