from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandHelp

from bot_app.bootstrap import dp


# Хэндлер команды /help
@dp.message_handler(CommandHelp())
async def bot_help(message: types.Message):
    text = ('Список команд:\n\n'
            '1. Команда "/menu" предназначена для вызова меню обучения. С помощью него ты можешь выбирать '
            'интересующее тебя направление обучения, а также разделы и уроки.\n\n'
            '2. Команда "/ai". Так как я умный бот, я могу помочь тебе в поиске нужной информации в нашей '
            'корпоративной информационной системе. Просто напиши эту '
            'команду, а также укажи через пробел интересующий тебя запрос. Если запрос '
            'будет мне понятен, я пришлю тебе ссылку на нужную страницу.\n\n')
    await message.answer(text, protect_content=True)
