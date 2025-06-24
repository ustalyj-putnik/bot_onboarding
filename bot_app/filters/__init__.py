from .access_check import IsNotEmployee

from bot_app.bootstrap import dp

if __name__ == "filters":
    dp.filters_factory.bind(IsNotEmployee)  # Регистрируем фильтр проверки доступа
