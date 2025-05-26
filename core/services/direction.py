from core.services.base import get_session
from sqlalchemy import select
from core.db.models import Direction, Section

class DirectionService:
    @staticmethod
    async def list_directions():
        async with get_session() as s:
            q = select(Direction).where(Direction.is_visible.is_(True))
            return (await s.execute(q)).scalars().all()

    @staticmethod
    async def get(direction_id: int):
        async with get_session() as s:
            return (await s.get(Direction, direction_id)).scalar_one()

    @staticmethod
    async def dir_by_code(dir_code: str):
        async with get_session() as s:
            q = select(Direction).where(Direction.code == dir_code)
            return (await s.execute(q)).scalar_one()
    @staticmethod
    async def list_sections(direction_id: int):
        async with get_session() as s:
            q = select(Section).where(Section.direction_id == direction_id and Section.is_visible.is_(True)).order_by(Section.order)
            return (await s.execute(q)).scalars().all()

    @staticmethod
    async def section_by_code(section_code: str):
        async with get_session() as s:
            q = select(Section).where(Section.code == section_code)
            await (await s.execute(q)).scalar_one()