
from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    HTTPException,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.redis import redis_client
from app.core.dependencies import get_current_user, require_admin
from app.core.security import (
    hash_email,
    encrypt_email,
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)

from app.models.user import User
from app.models.access_log import AccessLog
from app.models.usage_history import UsageHistory

from app.schemas.auth import (
    UserRegister,
    UserLogin,
    UserUpdate,
    PasswordUpdate,
    UserResponse,
)

from app.use_cases.rate_limit import rate_limit


router = APIRouter(prefix="/auth", tags=["Autenticação"])


# Configuração do cookie de autenticação
COOKIE_NAME = "access_token"
COOKIE_SECURE = True
COOKIE_SAMESITE = "lax"
COOKIE_PATH = "/"


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(3, 60, "ip"))],
)
def register(
    data: UserRegister,
    db: Session = Depends(get_db),
):
    email_hash = hash_email(str(data.email))

    existing_user = db.query(User).filter(
        User.email_hash == email_hash
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail já cadastrado.",
        )

    user = User(
        name=data.name.strip(),
        email_hash=email_hash,
        email_encrypted=encrypt_email(str(data.email)),
        password_hash=hash_password(data.password),
        is_active=True,
        is_admin=False,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post(
    "/login",
    dependencies=[Depends(rate_limit(5, 60, "ip"))],
)
def login(
    data: UserLogin,
    response: Response,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(
        User.email_hash == hash_email(str(data.email))
    ).first()

    if (
        not user
        or not verify_password(data.password, user.password_hash)
        or not user.is_active
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos.",
        )

    token, _, expires_at = create_access_token(str(user.id))

    expires_in = max(
        int(
            (expires_at - datetime.now(timezone.utc)).total_seconds()
        ),
        1,
    )

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=expires_in,
        path=COOKIE_PATH,
    )

    return {
        "message": "Autenticado com sucesso.",
        "expires_in": expires_in,
    }


@router.post("/logout")
def logout(
    response: Response,
    access_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    current_user: User = Depends(get_current_user),
):
    if access_token:
        try:
            payload = decode_access_token(access_token)

            jti = payload["jti"]
            exp = int(payload["exp"])

            now = int(datetime.now(timezone.utc).timestamp())
            ttl = max(exp - now, 1)

            redis_client.setex(
                f"revoked_token:{jti}",
                ttl,
                "1",
            )

        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Não foi possível revogar o token.",
            )

    response.delete_cookie(
        key=COOKIE_NAME,
        path=COOKIE_PATH,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
    )

    return {
        "message": "Logout realizado com sucesso."
    }


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_me(
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if data.name is not None:
        current_user.name = data.name.strip()

    if data.email is not None:
        new_hash = hash_email(str(data.email))

        existing = db.query(User).filter(
            User.email_hash == new_hash,
            User.id != current_user.id,
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este e-mail já está cadastrado.",
            )

        current_user.email_hash = new_hash
        current_user.email_encrypted = encrypt_email(str(data.email))

    db.commit()
    db.refresh(current_user)

    return current_user


@router.patch("/me/password")
def update_password(
    data: PasswordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(
        data.current_password,
        current_user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta.",
        )

    if data.current_password == data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A nova senha deve ser diferente da atual.",
        )

    current_user.password_hash = hash_password(data.new_password)

    db.commit()

    return {
        "message": "Senha atualizada com sucesso."
    }


@router.get("/me/access-history")
def my_access_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    records = (
        db.query(AccessLog)
        .filter(AccessLog.user_id == current_user.id)
        .order_by(AccessLog.accessed_at.desc())
        .limit(100)
        .all()
    )

    return [
        {
            "endpoint": item.endpoint,
            "method": item.method,
            "status_code": item.status_code,
            "ip_address": item.ip_address,
            "accessed_at": item.accessed_at,
        }
        for item in records
    ]


@router.get("/me/usage-history")
def my_usage_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    records = (
        db.query(UsageHistory)
        .filter(UsageHistory.user_id == current_user.id)
        .order_by(UsageHistory.created_at.desc())
        .limit(100)
        .all()
    )

    return [
        {
            "resource": item.resource,
            "action": item.action,
            "resource_id": item.resource_id,
            "execution_time_ms": item.execution_time_ms,
            "details": item.details,
            "created_at": item.created_at,
        }
        for item in records
    ]


@router.get("/admin/access-history")
def admin_access_history(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    records = (
        db.query(AccessLog)
        .order_by(AccessLog.accessed_at.desc())
        .limit(500)
        .all()
    )

    return [
        {
            "user_id": item.user_id,
            "endpoint": item.endpoint,
            "method": item.method,
            "status_code": item.status_code,
            "ip_address": item.ip_address,
            "accessed_at": item.accessed_at,
        }
        for item in records
    ]


@router.get("/admin/usage-history")
def admin_usage_history(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    records = (
        db.query(UsageHistory)
        .order_by(UsageHistory.created_at.desc())
        .limit(500)
        .all()
    )

    return [
        {
            "user_id": item.user_id,
            "resource": item.resource,
            "action": item.action,
            "resource_id": item.resource_id,
            "execution_time_ms": item.execution_time_ms,
            "created_at": item.created_at,
        }
        for item in records
    ]
