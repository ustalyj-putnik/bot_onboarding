from aiogram import types
from core.db.session import AsyncSessionLocal
from core.db.models import InteractionLog
from bot_app.bootstrap import dp
from monitoring.prometheus import ANS_BAD, ANS_GOOD

@dp.callback_query_handler(lambda c: c.data.startswith("rate_"))
async def handle_rate(callback: types.CallbackQuery):
    _, inter_id, val = callback.data.split("_")
    val = int(val)

    async with AsyncSessionLocal() as s:
        log: InteractionLog | None = await s.get(InteractionLog, int(inter_id))
        if log and log.rating is None:
            log.rating = val
            await s.commit()
            await callback.answer("Спасибо за оценку!", show_alert=False)
            (ANS_GOOD if val == 1 else ANS_BAD).inc()
        else:
            await callback.answer("Уже оценено 🙂", show_alert=False)