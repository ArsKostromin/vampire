# Vampire FastAPI Backend

## Описание
Бэкенд для игрового сервиса с авторизацией, лидербордом и логированием действий в базе данных. Использует PostgreSQL, FastAPI, Grafana/Loki/Elasticsearch для логирования.

## Структура проекта

- `app/` — исходный код FastAPI приложения
  - `main.py` — точка входа
  - `api/` — роуты API
  - `models/` — Pydantic и SQLAlchemy модели
  - `db/` — подключение к базе данных, миграции
  - `core/` — конфиги, авторизация, utils
  - `logging/` — интеграция с системами логирования
- `tests/` — тесты
- `alembic/` — миграции БД
- `requirements.txt` — зависимости
- `README.md` — описание 