import asyncio

from app.core.db_session import async_session
from app.ai_engine.services.category_resolution_service import (
    CategoryResolutionService,
)


async def main():
    async with async_session() as db:
        service = CategoryResolutionService(db)
        result = await service.run()
        print("Category resolution job completed:", result)


if __name__ == "__main__":
    asyncio.run(main())
