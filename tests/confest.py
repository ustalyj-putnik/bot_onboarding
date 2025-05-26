import sys
import asyncio
import pytest
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from core.db.session import engine, AsyncSessionLocal
from core.db.models import Base, Lesson

# ---------- корректный event loop для Windows ----------
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


# ---------- session-wide БД + один урок ----------
@pytest.fixture(scope="session", autouse=True)
async def _prepare_db():
    # создаём схему
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # добавляем 1 урок, если его нет
    async with AsyncSessionLocal() as s:
        if not await s.get(Lesson, 1):
            s.add(Lesson(id=1, stage=1, title="Первый урок", body="Текст урока", order=1))
            await s.commit()

    yield  # --- тесты выполняются здесь ---

    # подчистим соединения, чтобы asyncio не ругался
    await engine.dispose()