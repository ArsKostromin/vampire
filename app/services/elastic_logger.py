import os
import logging
from typing import List

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
            CREATE TABLE IF NOT EXISTS elastic_offset (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                last_uploaded_id BIGINT
            )
        """))

        await conn.execute(text("""
            INSERT INTO elastic_offset (id, last_uploaded_id)
            VALUES (1, NULL)
            ON CONFLICT (id) DO NOTHING
        """))


async def get_last_uploaded_id() -> int | None:
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT last_uploaded_id FROM elastic_offset WHERE id = 1")
        )
        row = result.fetchone()
        return row[0] if row else None


async def update_last_uploaded_id(value: int):
    async with engine.begin() as conn:
        await conn.execute(
            text("""
                UPDATE elastic_offset
                SET last_uploaded_id = :value
                WHERE id = 1
            """),
            {"value": value},
        )

# ELASTIC INDEX INIT
async def ensure_index_exists():
    try:
        exists = await es.indices.exists(index="audit_logs")

        if not exists:
            await es.indices.create(
                index="audit_logs",
                mappings={
                    "properties": {
                        "table": {"type": "keyword"},
                        "operation": {"type": "keyword"},
                        "event_time": {"type": "date"},
                        "user_id": {"type": "keyword"},
                        "username": {"type": "text"},
                        "data": {
                            "properties": {
                                "old": {"type": "object"},
                                "new": {"type": "object"},
                            }
                        },
                    }
                },
            )

            logger.info("Created index audit_logs")

    except Exception:
        logger.exception("Failed to ensure index exists")
        raise

# FETCH LOGS
async def fetch_new_logs(limit: int = 500):
    last_id = await get_last_uploaded_id()

    query = """
        SELECT id, table_name, operation, user_id, username,
               old_record, new_record, event_time
        FROM audit_log
        WHERE (:last_id IS NULL OR id > :last_id)
        ORDER BY id ASC
        LIMIT :limit
    """

    async with engine.connect() as conn:
        result = await conn.execute(
            text(query),
            {"last_id": last_id, "limit": limit},
        )

        return result.mappings().all()

# BULK UPLOAD
async def log_to_elastic():
    try:
        logs = await fetch_new_logs()

        if not logs:
            return

        actions = []
        max_id = None

        for log in logs:
            max_id = log["id"]

            actions.append(
                {
                    "_index": "audit_logs",
                    "_source": {
                        "table": log["table_name"],
                        "operation": log["operation"],
                        "event_time": log["event_time"].isoformat(),
                        "user_id": str(log["user_id"]) if log["user_id"] else None,
                        "username": log["username"],
                        "data": {
                            "old": log["old_record"],
                            "new": log["new_record"],
                        },
                    },
                }
            )

        await async_bulk(es, actions)

        if max_id is not None:
            await update_last_uploaded_id(max_id)

        logger.info("Uploaded %s audit logs", len(actions))

    except es_exceptions.ConnectionError:
        logger.exception("Elasticsearch connection error")
    except Exception:
        logger.exception("Unexpected error during elastic upload")
        
# STARTUP / SHUTDOWN
async def startup():
    await ensure_offset_table()
    await ensure_index_exists()


async def shutdown():
    await es.close()
    await engine.dispose()
