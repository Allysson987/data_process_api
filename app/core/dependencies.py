
from uuid import UUID

import jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from redis.exceptions import RedisError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.redis import redis_client
from app.core.security import decode_access_token
from app.models.user import User


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:

    # 1. Validar presença do token
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação necessária.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # 2. Validar assinatura e conteúdo do JWT
    try:
        payload = decode_access_token(token)

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

    except (jwt.InvalidTokenError, ValueError, TypeError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Verificar revogação no Redis
    try:
        is_revoked = redis_client.exists(f"revoked_token:{jti}")

    except RedisError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de autenticação temporariamente indisponível.",
        )

    if is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão revogada. Faça login novamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4. Consultar usuário no banco
    user = db.query(User).filter(
        User.id == user_uuid,
        User.is_active.is_(True),
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou inativo.",
            headers={"WWW-Authenticate": "Bearer"},
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
