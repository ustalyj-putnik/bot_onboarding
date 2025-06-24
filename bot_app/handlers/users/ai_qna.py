from aiogram import types
from bot_app.bootstrap import dp
from core import MLGateway

@dp.message_handler(lambda m: m.text and m.text.startswith("?"))  # условный префикс вопроса
async def ai_qna(message: types.Message):
    question = message.text.lstrip("? ").strip()
    # ① мгновенная реакция
    thinking = await message.answer("💭 Думаю…")

    response, kb, _ = await MLGateway.answer(message.from_user.id, question)

    await thinking.edit_text(response, reply_markup=kb)