from aiogram import types

from bot_app.bootstrap import dp
from bot_app import IsNotEmployee

# Хэндлер, который отлавливает ограничения доступа к боту (по фильтру).
@dp.message_handler(IsNotEmployee())
async def access_denied_msg(message: types.Message):
    await message.answer(text="Привет! Для доступа к боту тебе необходимо быть сотрудником компании.\n"
                              "Если ты уверен(-а), что у тебя должен быть доступ, обратись к своему руководителю "
                              "для получения доступа.",
                         protect_content=True)