from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Клавиатура для оценки ответа ML-модели

def ml_rating_keyboard(log):
    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("👍", callback_data=f"rate_{log.id}_1"),
        InlineKeyboardButton("👎", callback_data=f"rate_{log.id}_0"),
    )
    return kb