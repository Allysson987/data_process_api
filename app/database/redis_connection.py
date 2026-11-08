from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings


if settings.REDIS_URL:
    redis_client = Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        health_check_interval=30
    )
else:
    redis_client = None


def check_redis() -> bool:
    """
    Verifica se o Redis está acessível.
    """

    if redis_client is None:
        raise RuntimeError("REDIS_URL não configurada.")

    try:
        return bool(redis_client.ping())

    except RedisError as error:
        raise ConnectionError(
            f"Não foi possível conectar ao Redis: {error}"
        ) from error