from aiogram import types


# Устанавливаем начальный набор команд
async def set_default_commands(dp):
    await dp.bot.set_my_commands(
        [
            types.BotCommand("start", "Запустить бота заново"),
        ]
    )
