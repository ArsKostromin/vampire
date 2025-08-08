from elasticsearch import Elasticsearch, exceptions as es_exceptions
from sqlalchemy import create_engine, text
from datetime import datetime
import os

ES_HOST = os.getenv("ELASTIC_HOST", "http://localhost:9200")
DB_URL = os.getenv("DATABASE_URL", "postgresql://api_user:password@db:5432/vampire_db")

# Инициализация Elasticsearch клиента
es = Elasticsearch(
    ES_HOST,
    headers={
        "Accept": "application/vnd.elasticsearch+json; compatible-with=8",
        "Content-Type": "application/vnd.elasticsearch+json; compatible-with=8"
    }
)

# SQLAlchemy engine
engine = create_engine(DB_URL)

# Последний загруженный лог
last_uploaded_id = None

def ensure_index_exists():
    """Создаёт индекс audit_logs, если его нет"""
    try:
        if not es.indices.exists(index="audit_logs"):
            es.indices.create(index="audit_logs", body={
                "mappings": {
                    "properties": {
                        "table": {"type": "keyword"},
                        "operation": {"type": "keyword"},
                        "event_time": {"type": "date"},
                        "user_id": {"type": "keyword"},
                        "username": {"type": "text"},
                        "data": {
                            "properties": {
                                "old": {"type": "object"},
                                "new": {"type": "object"}
                            }
                        }
                    }
                }
            })
            print("[Elasticsearch] Created index 'audit_logs'")
    except es_exceptions.ConnectionError as e:
        print(f"[Elasticsearch] Connection error: {e}")
    except Exception as e:
        print(f"[Elasticsearch] Unexpected error while creating index: {e}")

def fetch_new_logs(limit=100):
    """Забираем новые строки из audit_log"""
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
    """Отправляет новые логи в Elasticsearch"""
    global last_uploaded_id

    try:
        ensure_index_exists()

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

            # Без указания ID → уникальный _id генерируется сам
            es.index(index="audit_logs", document=doc)

            last_uploaded_id = log.id

        if logs:
            print(f"[AuditLogger] Uploaded {len(logs)} logs (up to ID {last_uploaded_id})")
        else:
            print("[AuditLogger] No new logs to upload.")

    except es_exceptions.ConnectionError as e:
        print(f"[Elasticsearch] Connection error during upload: {e}")
    except Exception as e:
        print(f"[AuditLogger] Unexpected error: {e}")
