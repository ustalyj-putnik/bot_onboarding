# Это главный файл проекта. Для запуска бота необходимо запустить сборку данного файла.
from aiogram import executor

from bot_app.bootstrap import dp
from bot_app import on_startup_notify
from scripts import set_default_commands
import bot_app.handlers  # noqa: F401  (нужен для side-effects)
from prometheus_client import start_http_server

async def on_startup(dispatcher):
    # Устанавливаем дефолтные команды
    await set_default_commands(dispatcher)

    # Уведомляем админов о запуске бота
    await on_startup_notify(dispatcher)


if __name__ == '__main__':
    start_http_server(9100)  # /metrics   (docker: проверь порт)
    executor.start_polling(dp, on_startup=on_startup)
