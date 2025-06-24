from core.db.models import UserProgress, Lesson, Direction
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from core.services.base import get_session

class ProgressService:
    @staticmethod
    async def get_or_create(user_id: int, section_id: int):
        async with get_session() as s:
            p = (await s.execute(select(UserProgress)
                    .where(UserProgress.user_id==user_id,
                           UserProgress.section_id==section_id))).scalar_one_or_none()
            if not p:
                p = UserProgress(user_id=user_id, section_id=section_id)
                s.add(p)
                await s.commit()
                await s.refresh(p)
            return p

    @staticmethod
    async def mark_lesson(user_id:int, lesson:Lesson):
        async with get_session() as s:
            p = await ProgressService.get_or_create(user_id, lesson.section_id)
            p.lesson_index = lesson.order
            s.add(p)
            await s.commit()
            await s.refresh(p)

    @staticmethod
    async def complete_quiz(user_id:int, section_id:int, score:int):
        async with get_session() as s:
            p = await ProgressService.get_or_create(user_id, section_id)
            p.quiz_passed = True
            p.score = score
            s.add(p)
            await s.commit()
            await s.refresh(p)

    @staticmethod
    async def get_dir_overview(user_id: int):
        """
        Возвращает словарь {direction: [(section, done_bool, score), …]}
        """
        async with get_session() as s:
            dirs = (await s.execute(select(Direction).options(selectinload(Direction.sections))))
            result = {}
            for d in dirs.scalars():
                rows = []
                for sec in sorted(d.sections, key=lambda x: x.order):
                    p = (
                        await s.execute(
                            select(UserProgress).where(
                                UserProgress.user_id == user_id,
                                UserProgress.section_id == sec.id,
                            )
                        )
                    ).scalar_one_or_none()
                    rows.append((sec, bool(p and p.quiz_passed), p.score if p else 0))
                result[d] = rows
            return result

    @staticmethod
    async def reset_section(user_id: int, section_id: int):
        async with get_session() as s:
            await s.execute(
                delete(UserProgress).where(
                    UserProgress.user_id == user_id,
                    UserProgress.section_id == section_id,
                )
            )
            await s.commit()