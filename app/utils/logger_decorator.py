from functools import wraps
from app.services.users_logger import log_user_action
from app.services.elastic_logger import log_to_elastic


def log_all(func):
    """Вызывает и логгер пользователей, и логгер аудита"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            log_user_action()
        except Exception as e:
            print(f"[UserLogger ERROR] {e}")

        try:
            log_to_elastic()
        except Exception as e:
            print(f"[ElasticLogger ERROR] {e}")

        return await func(*args, **kwargs)
    return wrapper


def log_elastic_only(func):
    """Вызывает только логгер аудита (elastic_logger)"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            log_to_elastic()
        except Exception as e:
            print(f"[ElasticLogger ERROR] {e}")

        return await func(*args, **kwargs)
    return wrapper
