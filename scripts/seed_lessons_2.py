import json, asyncio
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from core.services.base import get_session
from core.db.models import Direction, Section, Lesson, QuizQuestion

JSON_PATH = Path("data/raw/second_stage_texts/structure.json")

async def main():
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    async with get_session() as s:
        # direction intro
        if "introduction" in data:
            intro_dir = Direction(
                code=data["introduction"]["title"],
                name="Введение 2-го этапа",
                intro_text=data["introduction"]["body"],
                is_visible=False,
            )
            s.add(intro_dir)
        for area in data["areas"]:
            dir_obj = Direction(
                code=area["code"],
                name=area["name"],
                intro_text=area["introduction"]["body"],
            )
            s.add(dir_obj)
            await s.flush()          # нужно id
            for sec in area["sections"]:
                sec_obj = Section(
                    direction_id=dir_obj.id,
                    code=sec["code"],
                    name=sec["name"],
                    order=sec["order"]
                )
                s.add(sec_obj)
                await s.flush()
                # уроки
                for idx, l in enumerate(sec["lessons"], start=1):
                    s.add(
                        Lesson(
                            section_id=sec_obj.id,
                            title=l["title"],
                            body=l["body"],
                            order=idx,
                        )
                    )
                # квиз
                for q in sec.get("quiz", []):
                    s.add(
                        QuizQuestion(
                            section_id=sec_obj.id,
                            question_text=q["question"],
                            options=q["options"],
                            correct_option=q["correct"],
                        )
                    )
        await s.commit()

if __name__ == "__main__":
    asyncio.run(main())
