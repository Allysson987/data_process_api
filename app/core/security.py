
import base64
import hashlib
import hmac
import secrets
import uuid

from datetime import datetime, timedelta, timezone

import jwt

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pwdlib import PasswordHash

from app.core.config import settings


password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


def normalize_email(email: str) -> str:
    return email.strip().casefold()


def hash_email(email: str) -> str:
    normalized = normalize_email(email)

    return hmac.new(
        settings.EMAIL_HASH_SECRET.encode("utf-8"),
        normalized.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def get_encryption_key() -> bytes:
    try:
        key = base64.b64decode(
            settings.EMAIL_ENCRYPTION_KEY,
            altchars=b"-_",
            validate=True,
        )
    except Exception as error:
        raise RuntimeError(
            "EMAIL_ENCRYPTION_KEY deve ser uma chave Base64 válida."
        ) from error

    if len(key) != 32:
        raise RuntimeError(
            "EMAIL_ENCRYPTION_KEY deve representar exatamente 32 bytes."
        )

    return key


def encrypt_email(email: str) -> str:
    key = get_encryption_key()
    nonce = secrets.token_bytes(12)

    aes = AESGCM(key)

    encrypted = aes.encrypt(
        nonce,
        normalize_email(email).encode("utf-8"),
        None,
    )

    return base64.b64encode(
        nonce + encrypted
    ).decode("utf-8")


def decrypt_email(encrypted_email: str) -> str:
    key = get_encryption_key()

    data = base64.b64decode(encrypted_email)

    nonce = data[:12]
    ciphertext = data[12:]

    aes = AESGCM(key)

    return aes.decrypt(
        nonce,
        ciphertext,
        None,
    ).decode("utf-8")


def create_access_token(user_id: str) -> tuple[str, str, datetime]:
    now = datetime.now(timezone.utc)

    expires_at = now + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )

    jti = str(uuid.uuid4())

    payload = {
        "sub": user_id,
        "jti": jti,
        "iat": now,
        "exp": expires_at,
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return token, jti, expires_at


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
