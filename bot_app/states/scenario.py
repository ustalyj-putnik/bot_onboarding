from aiogram.dispatcher.filters.state import State, StatesGroup

class ScenarioStates(StatesGroup):
    choosing  = State()   # список сценариев ↔ выбор
    answering = State()   # внутри конкретного сценария
