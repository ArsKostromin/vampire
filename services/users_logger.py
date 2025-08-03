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

def fetch_users(limit=100):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, name, record, created_at
            FROM users
            ORDER BY name
            LIMIT :limit
        """), {"limit": limit})
        return result.fetchall()

def push_users_to_elasticsearch():
    users = fetch_users()

    for user in users:
        doc = {
            "id": str(user.id),
            "name": user.name,
            "record": float(user.record),
            "created_at": user.created_at.isoformat(), 
            "timestamp": datetime.utcnow().isoformat()
        }

        # Отправка в Elastic
        es.index(index="users_data", id=str(user.id), document=doc)

    print(f"[OK] Uploaded {len(users)} users to Elasticsearch.")

if __name__ == "__main__":
    push_users_to_elasticsearch()
