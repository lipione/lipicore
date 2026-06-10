from datetime import datetime, timedelta
from typing import Any, Union
import hashlib
import hmac
import string
from jose import jwt
from passlib.context import CryptContext
from .config import settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def _is_legacy_pbkdf2_hash(hashed_password: str) -> bool:
    return (
        len(hashed_password) == 96
        and all(char in string.hexdigits for char in hashed_password)
    )


def _verify_legacy_pbkdf2_password(plain_password: str, hashed_password: str) -> bool:
    salt = hashed_password[:32]
    key = hashed_password[32:]
    new_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return hmac.compare_digest(new_key.hex(), key)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if _is_legacy_pbkdf2_hash(hashed_password):
        return _verify_legacy_pbkdf2_password(plain_password, hashed_password)
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except (TypeError, ValueError):
        return False


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def password_hash_needs_rehash(hashed_password: str) -> bool:
    if _is_legacy_pbkdf2_hash(hashed_password):
        return True
    try:
        return pwd_context.needs_update(hashed_password)
    except (TypeError, ValueError):
        return True
