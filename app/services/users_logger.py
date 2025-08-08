from elasticsearch import Elasticsearch, exceptions as es_exceptions
from sqlalchemy import create_engine, text
from datetime import datetime
import os

# Настройки из .env
ES_HOST = os.getenv("ELASTIC_HOST", "http://localhost:9200")
DB_URL = os.getenv("DATABASE_URL", "postgresql://api_user:password@db:5432/vampire_db")

# Инициализация клиентов
es = Elasticsearch(
    ES_HOST,
    headers={
        "Accept": "application/vnd.elasticsearch+json; compatible-with=8",
        "Content-Type": "application/vnd.elasticsearch+json; compatible-with=8"
    }
)
engine = create_engine(DB_URL)

# Храним ID'шник последнего отправленного юзера
last_uploaded_user_ids = set()

def ensure_index_exists():
    """Создаёт индекс users_data, если его нет"""
    try:
        if not es.indices.exists(index="users_data"):
            es.indices.create(index="users_data", body={
                "mappings": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "name": {"type": "text"},
                        "record": {"type": "float"},
                        "created_at": {"type": "date"},
                        "logged_at": {"type": "date"}
                    }
                }
            })
            print("[Elasticsearch] Created index 'users_data'")
    except es_exceptions.ConnectionError as e:
        print(f"[Elasticsearch] Connection error: {e}")
    except Exception as e:
        print(f"[Elasticsearch] Unexpected error while creating index: {e}")

def fetch_users(limit=100):
    """Забирает последних пользователей из БД"""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, name, record, created_at
            FROM users
            ORDER BY created_at DESC
            LIMIT :limit
        """), {"limit": limit})
        return result.fetchall()

def log_user_action(request=None, response=None, user=None):
    """Загружает новые записи о пользователях в Elasticsearch"""
    global last_uploaded_user_ids

    try:
        ensure_index_exists()
        users = fetch_users()
        new_users = [u for u in users if str(u.id) not in last_uploaded_user_ids]

        for user in new_users:
            doc = {
                "id": str(user.id),
                "name": user.name,
                "record": float(user.record),
                "created_at": user.created_at.isoformat(),
                "logged_at": datetime.utcnow().isoformat()
            }

            # Без указания ID — тогда ES сам придумает уникальный
            es.index(index="users_data", document=doc)
            last_uploaded_user_ids.add(str(user.id))

        if new_users:
            print(f"[UserLogger] Uploaded {len(new_users)} new users.")
        else:
            print("[UserLogger] No new users to upload.")

    except es_exceptions.ConnectionError as e:
        print(f"[Elasticsearch] Connection error during upload: {e}")
    except Exception as e:
        print(f"[UserLogger] Unexpected error: {e}")
