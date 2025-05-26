from gino import Gino
from gino.schema import GinoSchemaVisitor

from core.config import settings

db = Gino()


async def create_db():
    await db.set_bind(settings.POSTGRESURI)  # Подвязываем БД по нашей ссылке
    db.gino: GinoSchemaVisitor  # Режим работы gino
    await db.gino.create_all()  # Создаем все таблицы
