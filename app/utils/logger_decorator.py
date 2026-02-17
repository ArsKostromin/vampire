from functools import wraps
import logging
import asyncio

from app.services.elastic_logger import log_to_elastic
from app.services.users_logger import log_user_action

logger = logging.getLogger(__name__)


def log_all(func):
    """Вызывает логгер пользователей и логгер аудита"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Запускаем логгеры в фоне, не блокируя основной handler
        tasks = []

        try:
            tasks.append(asyncio.create_task(log_user_action()))
        except Exception:
            logger.exception("UserLogger scheduling error")

        try:
            tasks.append(asyncio.create_task(log_to_elastic()))
        except Exception:
            logger.exception("ElasticLogger scheduling error")

        # Выполняем основной handler
        result = await func(*args, **kwargs)

        return result

    return wrapper


def log_elastic_only(func):
    """Вызывает только логгер аудита"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            asyncio.create_task(log_to_elastic())
        except Exception:
            logger.exception("ElasticLogger scheduling error")

        return await func(*args, **kwargs)

    return wrapper
