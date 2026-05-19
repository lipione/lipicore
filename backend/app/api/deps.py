from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlmodel import Session, select
from pydantic import ValidationError

from ..core.config import settings
from ..db.session import get_session
from ..models.user import User
from ..models.token import RevokedToken
from ..schemas.auth import TokenData

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False,
)

# In-memory fast-path cache; DB is authoritative across restarts.
revoked_tokens: set[str] = set()


def get_raw_token(
    request: Request,
    bearer: Optional[str] = Depends(reusable_oauth2),
) -> str:
    """Extract JWT from Authorization header first, then fall back to httpOnly cookie."""
    token = bearer or request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return token


def _is_token_revoked(token: str, db: Session) -> bool:
    if token in revoked_tokens:
        return True
    token_hash = RevokedToken.hash(token)
    row = db.exec(select(RevokedToken).where(RevokedToken.token_hash == token_hash)).first()
    if row:
        revoked_tokens.add(token)  # warm the in-memory cache
        return True
    return False


def get_current_user(
    db: Session = Depends(get_session), token: str = Depends(get_raw_token)
) -> User:
    if _is_token_revoked(token, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token has been revoked. Please log in again.",
        )
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
            )
        token_data = TokenData(user_id=int(user_id))
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    user = db.get(User, token_data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    return current_user


def get_current_bank_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in ["super_admin", "bank_admin"]:
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    return current_user


def get_current_analytics_user(
    current_user: User = Depends(get_current_user),
) -> User:
    analytics_roles = {"super_admin", "bank_admin", "auditor", "data_auditor"}
    if current_user.role not in analytics_roles:
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    return current_user
