from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.services.scenario_loader import list_scenarios

SCENARIO_CB_PREFIX = "SCENARIO_ID:"   # будем фильтровать callback-данные

def scenarios_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    for sid, title in list_scenarios():
        kb.add(
            InlineKeyboardButton(
                text=title,
                callback_data=f"{SCENARIO_CB_PREFIX}{sid}"
            )
        )
    return kb
