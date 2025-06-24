from aiogram import types
from aiogram.dispatcher.filters import BoundFilter

from core.config import settings
from bot_app.bootstrap import bot

# Фильтр для проверки доступа к боту. Доступ определяется по тому, состоит ли пользователь в закрытом корпоративном
# чате компании или нет. ID чата см. в .env
class IsNotEmployee(BoundFilter):
    async def check(self, message: types.Message) -> bool:
        access = await bot.get_chat_member(chat_id=settings.ACCESS_ID, user_id=message.from_user.id)
        return access.status == "left"