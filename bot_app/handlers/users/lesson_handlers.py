from bot_app.bootstrap import dp
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from core.services import DirectionService, LessonService, ProgressService, QuizService
from core.db import Lesson
from bot_app.constants import FIRST_SECTION_CODE, SECOND_INTRO_CODE
from core.services import get_session
from core.db import Section, Direction
from sqlalchemy import select
from scripts.set_second_stage_commands import set_second_stage_commands

@dp.message_handler(commands=["start"])
async def cmd_start(message: Message):
    #sec = DirectionService.section_by_code(FIRST_SECTION_CODE)
    async with get_session() as s:
        sec = (await s.execute(
            select(Section).where(Section.code == FIRST_SECTION_CODE)
        )).scalar_one()
    lesson = await LessonService.first_lesson(sec.id)
    user_name = message.from_user.first_name
    await message.answer(f"Привет, {user_name}!\n\n{lesson.body}")
    kb = InlineKeyboardMarkup()
    nxt = await LessonService.next_lesson(lesson.id)
    kb.add(InlineKeyboardButton("➡️ Далее", callback_data=f"lesson_{nxt.id}"))
    await message.answer("Для продолжения нажмите кнопку ниже:",
                         reply_markup=kb)

@dp.callback_query_handler(text="transition")
async def to_second_stage_intro(cb: CallbackQuery):
    #intro_dir = DirectionService.dir_by_code(SECOND_INTRO_CODE)
    await set_second_stage_commands(dp)
    async with get_session() as s:
        intro_dir = (await s.execute(
            select(Direction).where(Direction.code == SECOND_INTRO_CODE)
        )).scalar_one()
        sec = (await s.execute(
            select(Section).where(Section.code == FIRST_SECTION_CODE)
        )).scalar_one()
    await ProgressService.complete_quiz(cb.from_user.id, sec.id, 1)
    text = intro_dir.intro_text or "Начинаем второй этап!"
    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Открыть меню", callback_data="to_menu")
    )
    await cb.message.edit_text(text, reply_markup=kb)
@dp.message_handler(commands=["menu"])
async def show_menu(msg: Message):
    dirs = await DirectionService.list_directions()
    kb = InlineKeyboardMarkup(row_width=1)
    for d in dirs:
        kb.add(InlineKeyboardButton(d.name, callback_data=f"dir_{d.id}"))
    await msg.answer("Выберите направление обучения:", reply_markup=kb)

# ---------- /progress ---------- #
@dp.message_handler(commands=["progress"])
async def cmd_progress(msg: Message):
    overview = await ProgressService.get_dir_overview(msg.from_user.id)

    text_parts = ["*Ваш прогресс:*"]
    kb = InlineKeyboardMarkup(row_width=1)

    for d, rows in overview.items():
        text_parts.append(f"\n*{d.name}*")
        for sec, done, score in rows:
            mark = "✅" if done else "❌"
            text_parts.append(f"{mark} {sec.name}")
            # кнопка сброса
            cb = f"reset_{sec.id}"
            kb.add(InlineKeyboardButton(f"🔄 Сбросить {sec.name}", callback_data=cb))

    await msg.answer("\n".join(text_parts), parse_mode="Markdown", reply_markup=kb)


# ---------- /reset (inline) ---------- #
@dp.callback_query_handler(lambda c: c.data.startswith("reset_"))
async def reset_section(cb: CallbackQuery):
    sec_id = int(cb.data.split("_")[1])
    await ProgressService.reset_section(cb.from_user.id, sec_id)
    await cb.answer("Прогресс раздела сброшен!", show_alert=True)
    # сразу обновить текст
    await cb.message.delete()
    fake = Message(chat=cb.message.chat, message_id=0)
    await cmd_progress(fake)

@dp.callback_query_handler(lambda c: c.data.startswith("dir_"))
async def choose_direction(cb: CallbackQuery):
    dir_id = int(cb.data.split("_")[1])
    secs = await DirectionService.list_sections(dir_id)
    # получаем вводный текст
    #dir = DirectionService.get(dir_id)
    async with get_session() as s:
        dir = await s.get(Direction, dir_id)
    kb = InlineKeyboardMarkup(row_width=1)
    for s in secs:
        kb.add(InlineKeyboardButton(s.name, callback_data=f"sec_{s.id}"))
    await cb.message.edit_text(dir.intro_text, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("sec_"))
async def section_intro(cb: CallbackQuery):
    sec_id = int(cb.data.split("_")[1])
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Начать раздел", callback_data=f"start_{sec_id}"))
    await cb.message.edit_text("Начинаем!", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("start_"))
async def start_section(cb: CallbackQuery):
    sec_id = int(cb.data.split("_")[1])
    lesson = await LessonService.first_lesson(sec_id)
    await ProgressService.mark_lesson(cb.from_user.id, lesson)
    await send_lesson(cb.message, lesson)

async def send_lesson(dst_msg: Message, lesson: Lesson, first_stage: bool = False):
    text = f"{lesson.body}"
    kb = InlineKeyboardMarkup()
    prev = await LessonService.prev_lesson(lesson.id)
    nxt  = await LessonService.next_lesson(lesson.id)
    if prev and not first_stage:
        kb.add(InlineKeyboardButton("⬅️ Назад", callback_data=f"lesson_{prev.id}"))
    if nxt:
        kb.add(InlineKeyboardButton("➡️ Далее", callback_data=f"lesson_{nxt.id}"))
    else:
        if first_stage:
            # последний урок первого этапа
            kb.add(InlineKeyboardButton("🚀 Перейти на 2-й этап",
                                        callback_data="transition"))
        else:
            kb.add(InlineKeyboardButton("Перейти к тесту",
                                        callback_data=f"quiz_{lesson.section_id}_0"))
    if not first_stage:
        kb.add(InlineKeyboardButton("🔙 В меню", callback_data="to_menu"))
    if lesson.media:
        #await dst_msg.edit_text(" ")  # очистим
        with open(lesson.media, 'rb') as img:
            await dst_msg.answer_photo(photo=img, caption=lesson.body, reply_markup=kb)
    else:
        if first_stage:
            await dst_msg.answer(text, reply_markup=kb)
        else:
            await dst_msg.edit_text(text, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("lesson_"))
async def lesson_nav(cb: CallbackQuery):
    lesson_id = int(cb.data.split("_")[1])
    #lesson = LessonService.get(lesson_id)
    #is_first_stage = (lesson.section.code == FIRST_SECTION_CODE)
    async with get_session() as s:
        lesson = await s.get(Lesson, lesson_id)
        section_code = await s.scalar(
            select(Section.code).where(Section.id == lesson.section_id)
        )
        is_first_stage = (section_code == FIRST_SECTION_CODE)
    await ProgressService.mark_lesson(cb.from_user.id, lesson)
    await send_lesson(cb.message, lesson, first_stage=is_first_stage)

@dp.callback_query_handler(lambda c: c.data.startswith("quiz_"))
async def quiz_flow(cb: CallbackQuery):
    _, sec_id, idx = cb.data.split("_")
    sec_id, idx = int(sec_id), int(idx)
    questions = await QuizService.get_questions(sec_id)
    if idx >= len(questions):
        score = len(questions)  # временно, подсчёт складываем в сессии
        await ProgressService.complete_quiz(cb.from_user.id, sec_id, score)
        await cb.message.edit_text(f"Тест завершён! Ваш результат: {score}/{len(questions)}",
                                   reply_markup=InlineKeyboardMarkup().add(
                                       InlineKeyboardButton("🔙 В меню", callback_data="to_menu"),
                                       InlineKeyboardButton("Пройти снова", callback_data=f"quiz_{sec_id}_0")
                                   ))
        return
    q = questions[idx]
    kb = InlineKeyboardMarkup(row_width=1)
    for i, opt in enumerate(q.options):
        kb.add(InlineKeyboardButton(opt, callback_data=f"ans_{sec_id}_{idx}_{i}"))
    await cb.message.edit_text(f"*Вопрос {idx+1}*\n{q.question_text}",
                               reply_markup=kb, parse_mode="Markdown")

@dp.callback_query_handler(lambda c: c.data.startswith("ans_"))
async def check_answer(cb: CallbackQuery):
    _, sec_id, idx, opt = cb.data.split("_")
    sec_id, idx, opt = int(sec_id), int(idx), int(opt)
    questions = await QuizService.get_questions(sec_id)
    q = questions[idx]
    text = "✅ Верно!" if QuizService.is_correct(q, opt) else "❌ Неверно. Попробуйте ещё."
    # переходим к следующему вопросу
    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Далее", callback_data=f"quiz_{sec_id}_{idx+1}")
    )
    await cb.message.edit_text(text, reply_markup=kb)

@dp.callback_query_handler(text="to_menu")
async def back_to_menu(cb: CallbackQuery):
    await cb.message.delete()
    await show_menu(cb.message)