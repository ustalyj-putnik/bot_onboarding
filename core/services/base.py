from contextlib import asynccontextmanager
from core.db import AsyncSessionLocal

@asynccontextmanager
async def get_session():
    async with AsyncSessionLocal() as session:
        yield session