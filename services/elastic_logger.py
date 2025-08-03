# services/elastic_logger.py
from elasticsearch import Elasticsearch
from sqlalchemy import create_engine, text
from datetime import datetime
import os

# Настройки из .env
ES_HOST = os.getenv("ELASTIC_HOST", "http://localhost:9200")
DB_URL = os.getenv("DATABASE_URL", "postgresql://api_user:password@db:5432/vampire_db")

# Подключения
es = Elasticsearch(
    "http://elasticsearch:9200",
    headers={"Accept": "application/vnd.elasticsearch+json; compatible-with=8",
             "Content-Type": "application/vnd.elasticsearch+json; compatible-with=8"}
)
engine = create_engine(DB_URL)

def fetch_recent_logs(limit=100):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, table_name, operation, user_id, username, old_record, new_record, event_time
            FROM audit_log
            ORDER BY event_time DESC
            LIMIT :limit
        """), {"limit": limit})
        return result.fetchall()

def push_logs_to_elasticsearch():
    logs = fetch_recent_logs()

    for log in logs:
        log_doc = {
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

        # Отправка в Elastic
        es.index(index="audit_logs", document=log_doc)

    print(f"[OK] Uploaded {len(logs)} audit logs to Elasticsearch.")

if __name__ == "__main__":
    push_logs_to_elasticsearch()
