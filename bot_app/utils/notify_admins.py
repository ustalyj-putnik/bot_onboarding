import logging

from aiogram import Dispatcher

from core.config import settings

# Уведомляем админов о запуске бота
async def on_startup_notify(dp: Dispatcher):
    for admin in settings.ADMINS:
        try:
            await dp.bot.send_message(admin, "Бот Запущен")

        except Exception as err:
            logging.exception(err)
