from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, Command
from aiogram.utils.markdown import bold

from bot_app.bootstrap import dp, bot
from bot_app.states.scenario import ScenarioStates
from bot_app.keyboards.inline.scenario_kb import (
    scenarios_keyboard, SCENARIO_CB_PREFIX
)
from core.services.scenario_loader import get_scenario, Scenario
from core.services.ml_gateway import MLGateway, AnswerRating
from core.services.scenario_analytics import ScenarioAnalytics
import uuid

@dp.message_handler(Command("scenario"), state="*")
async def cmd_scenario(message: types.Message, state: FSMContext):
    """Вывести список доступных тренажёров."""
    await state.finish()   # сбросим любое предыдущее состояние
    await message.answer(
        "Выберите тренировочный сценарий:",
        reply_markup=scenarios_keyboard()
    )
    await ScenarioStates.choosing.set()

@dp.callback_query_handler(
    Text(startswith=SCENARIO_CB_PREFIX),
    state=ScenarioStates.choosing
)
async def scenario_chosen(callback: types.CallbackQuery, state: FSMContext):
    scenario_id = callback.data[len(SCENARIO_CB_PREFIX):]
    scenario: Scenario = get_scenario(scenario_id)

    run_id = str(uuid.uuid4())

    # сохраняем контекст в FSM-storage
    await state.update_data(
        scenario_id=scenario_id,
        current_step="1",
        retries_left=scenario.max_retries,
        run_id = run_id
    )

    # заменяем клавиатуру на интро
    await callback.message.edit_text(
        f"{bold('Сценарий запущен')}: {scenario.title}\n\n"
        f"{scenario.description}\n\n"
        "Отвечайте в чате – я буду оценивать ответы. "
        "Для выхода в любой момент пришлите /cancel.",
        parse_mode="HTML"
    )

    # отправляем первый вопрос
    await send_step(callback.from_user.id, scenario, "1")

    await ScenarioStates.answering.set()
    await callback.answer()    # убираем «часики»

@dp.message_handler(
    lambda m: not m.text.startswith("/"),
    content_types=types.ContentTypes.TEXT,
    state=ScenarioStates.answering
)
async def scenario_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    scenario: Scenario = get_scenario(data["scenario_id"])
    step_id: str = data["current_step"]
    run_id = data["run_id"]
    step = scenario.steps[step_id]

    user_reply = message.text

    attempt_no = (scenario.max_retries - data.get("retries_left", scenario.max_retries))

    # --- вызов Saiga через ML-Gateway ---
    rating = await MLGateway.evaluate_answer(
        user_id=message.from_user.id,
        user_answer=user_reply,
        expected=step.expected_answers,
        mistakes=step.common_mistakes,
        scenario_id=data["scenario_id"],
        step_id=step_id,
        attempt=attempt_no,
        run_id=run_id
    )
    # rating ∈ {"correct", "partial", "incorrect"}

    # --- логика перехода ---
    if rating == AnswerRating.correct:
        next_id = step.on_correct

    else:
        retries_left = data.get("retries_left", scenario.max_retries) - 1
        await state.update_data(retries_left=retries_left)

        if retries_left >= 0 and step.hint:
            # показываем подсказку, остаёмся на том же шаге
            await message.answer(f"{step.hint}\n\nПопробуйте ещё раз.")
            return

        # попытки кончились -> on_incorrect
        next_id = step.on_incorrect
        await state.update_data(retries_left=scenario.max_retries)

    # --- финал или следующий шаг ---
    if next_id.startswith("outcome_"):
        # 1) Сохраняем агрегат
        result = await ScenarioAnalytics.build_and_save(
            user_id=message.from_user.id,
            scenario_id=data["scenario_id"],
            outcome_key=next_id,
            run_id=run_id
        )

        # 2) Формируем текст отчёта
        report = (
            f"🏁 <b>Сценарий завершён</b>\n\n"
            f"Итог: {scenario.outcomes[next_id]}\n\n"
            f"✅ Правильно:   {result.correct_cnt}\n"
            f"➖ Частично:    {result.partial_cnt}\n"
            f"❌ Неверно:     {result.incorrect_cnt}\n"
            f"🔄 Средн. попыток на шаг: {result.avg_attempts}\n"
            f"📈 Навык: {result.skill_score} / 100"
        )

        await message.answer(report, parse_mode="HTML")
        await state.finish()                      # выход из FSM
    else:
        await state.update_data(current_step=next_id)
        await send_step(message.chat.id, scenario, next_id)

@dp.message_handler(Command("cancel"), state=ScenarioStates.answering)
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("🚪 Вы вышли из тренажёра. Возвращаемся к обычным командам.")

async def send_step(chat_id: int, scenario: Scenario, step_id: str):
    """Отправить текст шага пользователю."""
    step = scenario.steps[step_id]
    await bot.send_message(chat_id, step.text)


