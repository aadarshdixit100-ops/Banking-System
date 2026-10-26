from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings

_client: AsyncIOMotorClient | None = None


def connect():
    global _client
    _client = AsyncIOMotorClient(settings.mongo_uri)


def close():
    global _client
    if _client:
        _client.close()


def get_db():
    if _client is None:
        connect()
    return _client[settings.mongo_db_name]


async def ensure_indexes():
    db = get_db()
    await db.users.create_index("username", unique=True)
    await db.accounts.create_index("account_no", unique=True)
    await db.accounts.create_index("customer_id")
    await db.transactions.create_index("txn_id", unique=True)
    await db.transactions.create_index([("account_no", 1), ("created_at", -1)])
