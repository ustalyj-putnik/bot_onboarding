from typing import List
from sqlalchemy import and_

from core.db.database import db
from core.db.models_old import Lesson


# Функция добавления урока в БД
async def add_lesson(**kwargs):
    newlesson = await Lesson(**kwargs).create()
    return newlesson

# Получение из БД список направлений обучения
async def get_study_areas() -> List[Lesson]:
    return await Lesson.query.distinct(Lesson.study_area_code).gino.all()


# Получение из БД списка разделов обучения по коду направления обучения
async def get_study_sections(study_area) -> List[Lesson]:
    return await Lesson.query.distinct(Lesson.study_section_code).where(Lesson.study_area_code == study_area).gino.all()


# Получение из БД списка уроков по коду направления обучения и коду раздела обучения
async def get_lessons(study_area, study_section) -> List[Lesson]:
    lessons = await Lesson.query.where(
        and_(Lesson.study_area_code == study_area,
             Lesson.study_section_code == study_section)
    ).order_by(Lesson.id).gino.all()
    return lessons


# Пересчёт количества уроков в разделе обучения
async def count_lessons(study_section_code):
    conditions = [Lesson.study_section_code == study_section_code]
    total = await db.select([db.func.count()]).where(*conditions).gino.scalar()
    return total


# Получение из БД текста урока по коду направления обучения, раздела обучения и id урока (составной pk)
async def get_lesson(study_area_code, section_code, lesson_id) -> Lesson:
    conditions = [Lesson.study_area_code == study_area_code,
                  Lesson.study_section_code == section_code,
                  Lesson.id == lesson_id]
    lesson = await Lesson.query.where(
        and_(*conditions)
    ).gino.first()
    return lesson
