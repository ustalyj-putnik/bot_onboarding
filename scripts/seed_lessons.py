import json, asyncio
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from core.services.base import get_session
from core.db import Lesson, Direction, Section

DATA = Path("data/raw/first_stage_texts.json")
FIRST_SECTION_CODE = "FIRST_STAGE"

async def main():
    async with get_session() as s:
        dir_first = Direction(code="INTRO", name="Этап 1: О компании", intro_text="Ух ты!", is_visible=False)
        s.add(dir_first)
        await s.flush()
        sec_first = Section(direction_id=dir_first.id,
                            code=FIRST_SECTION_CODE,
                            name="О компании",
                            order=0,
                            is_visible=False)
        s.add(sec_first)
        await s.flush()
        # привязываем уроки
        for order, item in enumerate(json.loads(DATA.read_text(encoding='utf-8')), start=1):
            s.add(
                Lesson(section_id=sec_first.id, title=item["title"], body=item["body"], order=order, media=item.get("image_path")))
            await s.commit()

'''
async def main():
    async with AsyncSessionLocal() as s:
        for order, item in enumerate(json.loads(DATA.read_text(encoding='utf-8')), start=1):
            s.add(Lesson(stage=1, title=item["title"], body=item["body"], order=order, image_path=item.get("image_path")))
        await s.commit()'''

if __name__ == "__main__":
    asyncio.run(main())