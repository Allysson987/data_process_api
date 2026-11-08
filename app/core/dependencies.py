
from uuid import UUID

import jwt

from fastapi import Cookie, Depends, HTTPException, status
from redis.exceptions import RedisError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.redis import redis_client
from app.core.security import decode_access_token
from app.models.user import User


COOKIE_NAME = "access_token"


def get_current_user(
    access_token: str | None = Cookie(
        default=None,
        alias=COOKIE_NAME,
    ),
    db: Session = Depends(get_db),
) -> User:

    # 1. Validar presença do cookie
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação necessária. Faça login novamente.",
        )

    # 2. Validar assinatura e conteúdo do JWT
    try:
        payload = decode_access_token(access_token)

        user_id = payload.get("sub")
        jti = payload.get("jti")
        exp = payload.get("exp")

        if not isinstance(user_id, str):
            raise ValueError("Identificador do usuário inválido.")

        if not isinstance(jti, str) or not jti:
            raise ValueError("Identificador da sessão inválido.")

        if not isinstance(exp, (int, float)):
            raise ValueError("Expiração do token inválida.")

        user_uuid = UUID(user_id)

    except (
        jwt.InvalidTokenError,
        ValueError,
        TypeError,
        AttributeError,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
        )

    # 3. Verificar revogação no Redis
    try:
        is_revoked = redis_client.exists(
            f"revoked_token:{jti}"
        )

    except RedisError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de autenticação temporariamente indisponível.",
        )

    if is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão revogada. Faça login novamente.",
        )

    # 4. Consultar usuário no banco
    user = (
        db.query(User)
        .filter(
            User.id == user_uuid,
            User.is_active.is_(True),
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou inativo.",
        )

    return user


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:

    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores.",
        )

    return current_user
