from aiogram import types


# Устанавливаем список команд на 2 этапе обучения
async def set_second_stage_commands(dp):
    await dp.bot.set_my_commands(
        [
            types.BotCommand("start", "Запустить бота"),
            types.BotCommand("help", "Вывести справку"),
            types.BotCommand("menu", "Меню обучения"),
            types.BotCommand("ai", "Интеллектуальный поиск"),
            types.BotCommand("progress", "Показать прогресс"),
            types.BotCommand("reset", "Сбросить прогресс"),
            types.BotCommand("scenario", "Тренажёр-диалог")
        ]
    )