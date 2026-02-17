import os
import logging
from datetime import datetime

from elasticsearch import AsyncElasticsearch
from elasticsearch import exceptions as es_exceptions
from elasticsearch.helpers import async_bulk

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine

# CONFIG
ES_HOST = os.getenv("ELASTIC_HOST", "http://localhost:9200")

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://api_user:password@db:5432/vampire_db"
)

logger = logging.getLogger(__name__)

# CLIENTS
es = AsyncElasticsearch(
    ES_HOST,
    headers={
        "Accept": "application/vnd.elasticsearch+json; compatible-with=8",
        "Content-Type": "application/vnd.elasticsearch+json; compatible-with=8",
    },
)

engine: AsyncEngine = create_async_engine(DB_URL, pool_pre_ping=True)

# OFFSET STORAGE
async def ensure_offset_table():
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users_offset (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                last_created_at TIMESTAMPTZ
            )
        """))

        await conn.execute(text("""
            INSERT INTO users_offset (id, last_created_at)
            VALUES (1, NULL)
            ON CONFLICT (id) DO NOTHING
        """))


async def get_last_created_at():
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT last_created_at FROM users_offset WHERE id = 1")
        )
        row = result.fetchone()
        return row[0] if row else None


async def update_last_created_at(value):
    async with engine.begin() as conn:
        await conn.execute(
            text("""
                UPDATE users_offset
                SET last_created_at = :value
                WHERE id = 1
            """),
            {"value": value},
        )

# INDEX INIT
async def ensure_index_exists():
    try:
        exists = await es.indices.exists(index="users_data")

        if not exists:
            await es.indices.create(
                index="users_data",
                mappings={
                    "properties": {
                        "id": {"type": "keyword"},
                        "name": {"type": "text"},
                        "record": {"type": "float"},
                        "created_at": {"type": "date"},
                        "logged_at": {"type": "date"},
                    }
                },
            )

            logger.info("Created index users_data")

    except Exception:
        logger.exception("Failed to ensure users_data index")
        raise

# FETCH USERS
async def fetch_new_users(limit: int = 500):
    last_created_at = await get_last_created_at()

    query = """
        SELECT id, name, record, created_at
        FROM users
        WHERE (:last_created_at IS NULL OR created_at > :last_created_at)
        ORDER BY created_at ASC
        LIMIT :limit
    """

    async with engine.connect() as conn:
        result = await conn.execute(
            text(query),
            {"last_created_at": last_created_at, "limit": limit},
        )

        return result.mappings().all()

# BULK UPLOAD
async def log_user_action():
    try:
        users = await fetch_new_users()

        if not users:
            return

        actions = []
        max_created_at = None

        for user in users:
            max_created_at = user["created_at"]

            actions.append(
                {
                    "_index": "users_data",
                    "_id": str(user["id"]),  # чтобы не было дублей
                    "_source": {
                        "id": str(user["id"]),
                        "name": user["name"],
                        "record": float(user["record"]),
                        "created_at": user["created_at"].isoformat(),
                        "logged_at": datetime.utcnow().isoformat(),
                    },
                }
            )

        await async_bulk(es, actions)

        if max_created_at:
            await update_last_created_at(max_created_at)

        logger.info("Uploaded %s new users", len(actions))

    except es_exceptions.ConnectionError:
        logger.exception("Elasticsearch connection error")
    except Exception:
        logger.exception("Unexpected error in user logger")

# STARTUP / SHUTDOWN
async def startup():
    await ensure_offset_table()
    await ensure_index_exists()


async def shutdown():
    await es.close()
    await engine.dispose()
