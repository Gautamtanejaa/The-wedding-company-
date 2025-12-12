from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings


class Database:
    client: AsyncIOMotorClient | None = None


db_instance = Database()


async def get_database():
    """Return the main MongoDB database handle."""
    if db_instance.client is None:
        db_instance.client = AsyncIOMotorClient(settings.MONGODB_URI)
    return db_instance.client[settings.MONGODB_DB_NAME]
