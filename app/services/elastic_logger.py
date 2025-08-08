from elasticsearch import Elasticsearch
from sqlalchemy import create_engine, text
from datetime import datetime
import os

ES_HOST = os.getenv("ELASTIC_HOST", "http://localhost:9200")
DB_URL = os.getenv("DATABASE_URL", "postgresql://api_user:password@db:5432/vampire_db")

es = Elasticsearch(
    ES_HOST,
    headers={
        "Accept": "application/vnd.elasticsearch+json; compatible-with=8",
        "Content-Type": "application/vnd.elasticsearch+json; compatible-with=8"
    }
)
engine = create_engine(DB_URL)

# Храним последнее отправленное событие
last_uploaded_id = None

def fetch_new_logs(limit=100):
    global last_uploaded_id

    query = """
        SELECT id, table_name, operation, user_id, username, old_record, new_record, event_time
        FROM audit_log
        WHERE (:last_id IS NULL OR id > :last_id)
        ORDER BY id ASC
        LIMIT :limit
    """

    with engine.connect() as conn:
        result = conn.execute(text(query), {
            "last_id": last_uploaded_id,
            "limit": limit
        })
        return result.fetchall()

def log_to_elastic(request=None, response=None, user=None):
    global last_uploaded_id

    logs = fetch_new_logs()

    for log in logs:
        doc = {
            "table": log.table_name,
            "operation": log.operation,
            "event_time": log.event_time.isoformat(),
            "user_id": str(log.user_id) if log.user_id else None,
            "username": log.username,
            "data": {
                "old": log.old_record,
                "new": log.new_record
            }
        }
        es.index(index="audit_logs", document=doc)
        last_uploaded_id = log.id

    if logs:
        print(f"[Elastic] Uploaded {len(logs)} logs (up to ID {last_uploaded_id})")
