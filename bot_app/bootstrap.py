from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from core.config import settings

# В этом файле создаём бота и диспетчер для их запуска в app.py
bot = Bot(token=settings.BOT_TOKEN, parse_mode="HTML")  # Экземпляр бота
dp = Dispatcher(bot, storage=MemoryStorage())   # Экземпляр диспетчера для обработки сообщений
