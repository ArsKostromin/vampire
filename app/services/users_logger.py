from elasticsearch import Elasticsearch
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

def fetch_users(limit=100):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, name, record, created_at
            FROM users
            ORDER BY created_at DESC
            LIMIT :limit
        """), {"limit": limit})
        return result.fetchall()

def log_user_action(request=None, response=None, user=None):
    global last_uploaded_user_ids

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

        es.index(index="users_data", document=doc)
        last_uploaded_user_ids.add(str(user.id))

    if new_users:
        print(f"[UserLogger] Uploaded {len(new_users)} new users.")
