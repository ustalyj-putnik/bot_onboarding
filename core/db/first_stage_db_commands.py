from core.db.database import db
from core.db.models_old import First_stage_msg


# Функция добавления сообщения первого этапа в БД
async def add_first_stage_msg(**kwargs):
    newmsg = await First_stage_msg(**kwargs).create()
    return newmsg


# Подсчёт сообщений первого этапа
async def count_msgs():
    conditions = [First_stage_msg.id != 0]
    total = await db.func.count(First_stage_msg.id).gino.scalar()
    return total


# Получаем сообщение из БД по id
async def get_msg(msg_id) -> First_stage_msg:
    msg = await First_stage_msg.query.where(First_stage_msg.id == msg_id).gino.first()
    return msg
