
import json
import logging

from redis.exceptions import RedisError

from app.database.redis_connection import redis_client


logger = logging.getLogger(__name__)


class DiaryCacheService:

    CACHE_TTL = 3600

    @staticmethod
    def cache_key(uf: str, limit: int) -> str:
        return f"diary:cache:{uf.upper()}:{limit}"

    def get(self, uf: str, limit: int):

        if redis_client is None:
            return None

        try:
            cached = redis_client.get(
                self.cache_key(uf, limit)
            )

            if cached is None:
                return None

            return json.loads(cached)

        except (RedisError, ValueError) as error:
            logger.warning(
                "Falha ao consultar cache de %s: %s",
                uf,
                error
            )
            return None

    def set(
        self,
        uf: str,
        limit: int,
        data: list[dict]
    ) -> None:

        if redis_client is None:
            return

        try:
            redis_client.setex(
                self.cache_key(uf, limit),
                self.CACHE_TTL,
                json.dumps(
                    data,
                    ensure_ascii=False
                )
            )

        except RedisError:
            logger.exception(
                "Falha ao gravar cache de %s",
                uf
            )

    def invalidate(self, uf: str) -> None:

        if redis_client is None:
            return

        try:
            pattern = f"diary:cache:{uf.upper()}:*"

            keys = list(
                redis_client.scan_iter(
                    match=pattern,
                    count=100
                )
            )

            if keys:
                redis_client.delete(*keys)

        except RedisError:
            logger.exception(
                "Falha ao invalidar cache de %s",
                uf
            )
