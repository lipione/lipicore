from datetime import datetime, timedelta, timezone
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError
from sqlmodel import Session, select

from ..db.session import get_session
from ..core import security
from ..core.config import settings
from ..models.user import User
from ..models.token import RevokedToken
from ..schemas.auth import Token
from .deps import get_current_user, get_raw_token, revoked_tokens
from ..services.auth_lockout_service import is_account_login_locked
from ..services.audit_service import log_audit_event, log_security_event
from ..core.limiter import limiter

router = APIRouter()


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
def login_access_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_session),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    user = db.exec(select(User).where(User.email == form_data.username)).first()
    if user and is_account_login_locked(db, user):
        log_security_event(
            db=db,
            event_type="failed_login_locked",
            severity="high",
            description=f"Locked account login attempt for email: {form_data.username}",
            bank_id=user.bank_id,
            user_id=user.id,
            metadata={"email": form_data.username},
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Try again later.",
        )

    if not user or not security.verify_password(form_data.password, user.password_hash):
        log_security_event(
            db=db,
            event_type="failed_login",
            severity="medium",
            description=f"Failed login attempt for email: {form_data.username}",
            bank_id=user.bank_id if user else None,
            user_id=user.id if user else None,
            metadata={"email": form_data.username}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        log_security_event(
            db=db,
            event_type="failed_login_inactive",
            severity="medium",
            description=f"Login attempt by inactive user: {user.email}",
            user_id=user.id,
            bank_id=user.bank_id
        )
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(user.id, expires_delta=access_token_expires)
    if security.password_hash_needs_rehash(user.password_hash):
        user.password_hash = security.get_password_hash(form_data.password)
        db.add(user)
        db.commit()
        db.refresh(user)

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    log_audit_event(
        db=db,
        action="login",
        resource_type="user",
        resource_id=str(user.id),
        bank_id=user.bank_id,
        user_id=user.id
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=dict)
def read_users_me(current_user: User = Depends(get_current_user)) -> Any:
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role,
        "bank_id": current_user.bank_id,
        "department": current_user.department,
    }


@router.post("/logout")
def logout(
    response: Response,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    token: str = Depends(get_raw_token),
) -> Any:
    # Persist token hash so revocation survives restarts
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        exp = payload.get("exp")
        expires_at = datetime.fromtimestamp(exp, tz=timezone.utc) if exp else (
            datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
    except JWTError:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    token_hash = RevokedToken.hash(token)
    if not db.exec(select(RevokedToken).where(RevokedToken.token_hash == token_hash)).first():
        db.add(RevokedToken(token_hash=token_hash, expires_at=expires_at))
        db.commit()

    revoked_tokens.add(token)  # warm in-memory cache
    response.delete_cookie(key="access_token", path="/")
    log_audit_event(
        db=db,
        action="logout",
        resource_type="user",
        resource_id=str(current_user.id),
        bank_id=current_user.bank_id,
        user_id=current_user.id,
    )
    return {"message": "Successfully logged out"}
