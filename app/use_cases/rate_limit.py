
from fastapi import Request, HTTPException, Depends

from app.core.redis import redis_client
from app.core.dependencies import get_current_user
from app.models.user import User


RATE_LIMIT_SCRIPT = """
local current = redis.call('INCR', KEYS[1])

if current == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end

local ttl = redis.call('TTL', KEYS[1])

return {current, ttl}
"""


def _apply_rate_limit(
    request: Request,
    identifier: str,
    identity: str,
    limit: int,
    window_seconds: int,
):
    if redis_client is None:
        raise HTTPException(
            status_code=503,
            detail="Serviço de proteção temporariamente indisponível.",
        )

    key = (
        f"rate_limit:{identity}:"
        f"{identifier}:{request.url.path}"
    )

    try:
        result = redis_client.eval(
            RATE_LIMIT_SCRIPT,
            1,
            key,
            window_seconds,
        )

        current_count = int(result[0])
        ttl = int(result[1])

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Serviço de proteção temporariamente indisponível.",
        )

    if current_count > limit:
        raise HTTPException(
            status_code=429,
            detail="Limite de requisições excedido.",
            headers={
                "Retry-After": str(max(ttl, 1))
            },
        )


def rate_limit(
    limit: int,
    window_seconds: int,
    identity: str = "ip",
):
    if identity == "user":

        def user_dependency(
            request: Request,
            current_user: User = Depends(get_current_user),
        ):
            _apply_rate_limit(
                request=request,
                identifier=str(current_user.id),
                identity=identity,
                limit=limit,
                window_seconds=window_seconds,
            )

        return user_dependency

    def ip_dependency(request: Request):
        identifier = (
            request.client.host
            if request.client
            else "unknown"
        )

        _apply_rate_limit(
            request=request,
            identifier=identifier,
            identity=identity,
            limit=limit,
            window_seconds=window_seconds,
        )

    return ip_dependency
