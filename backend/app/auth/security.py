import uuid
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import GUEST_ACCESS, GUEST_INSTITUTE_ID, JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET
from app.database.database import get_db
from app.database.models import ACCOUNT_ACTIVE, STUDENT, Role, User, UserSession

_hasher = PasswordHasher()
_bearer = HTTPBearer(auto_error=False)

# Avoid a DB write on every request: refresh last_seen_at at most once a minute.
LAST_SEEN_UPDATE_INTERVAL = timedelta(seconds=60)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(dt: datetime) -> datetime:
    # SQLite returns naive datetimes; PostgreSQL returns aware ones.
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


# ---------- Passwords (Argon2) ----------

def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


# ---------- Sessions + JWT ----------

def create_session(
    db: Session, user: User, device: Optional[str] = None, ip_address: Optional[str] = None
) -> UserSession:
    now = utcnow()
    session = UserSession(
        session_id=uuid.uuid4().hex,
        user_id=user.id,
        created_at=now,
        last_seen_at=now,
        expires_at=now + timedelta(minutes=JWT_EXPIRE_MINUTES),
        device=(device or "")[:255] or None,
        ip_address=ip_address,
    )
    db.add(session)
    db.commit()
    return session


def create_access_token(user: User, session: UserSession) -> str:
    payload = {
        "sub": str(user.id),
        "role": user.role.name,
        "jti": session.session_id,
        "iat": session.created_at,
        "exp": session.expires_at,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


# ---------- Dependencies ----------

def get_current_session(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> UserSession:
    """Resolve the login session from the `Authorization: Bearer <token>` header."""
    if credentials is None:
        raise _unauthorized("Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = int(payload["sub"])
        session_id = payload["jti"]
    except jwt.ExpiredSignatureError:
        raise _unauthorized("Token has expired")
    except (jwt.PyJWTError, KeyError, ValueError):
        raise _unauthorized("Invalid token")

    session = db.scalar(select(UserSession).where(UserSession.session_id == session_id))
    if session is None or session.user_id != user_id or session.logged_out_at is not None:
        raise _unauthorized("Session has ended. Please log in again")

    user = session.user
    if user.account_status != ACCOUNT_ACTIVE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is not active")

    now = utcnow()
    if now - as_utc(session.last_seen_at) > LAST_SEEN_UPDATE_INTERVAL:
        session.last_seen_at = now
        db.commit()
    return session


def get_current_user(session: UserSession = Depends(get_current_session)) -> User:
    return session.user


def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Like get_current_user, but returns None for public endpoints called without a token."""
    if credentials is None:
        return None
    return get_current_session(credentials, db).user


def get_or_create_guest(db: Session) -> User:
    """The shared guest account used by requests without a token (see GUEST_ACCESS)."""
    guest = db.scalar(select(User).where(User.institute_id == GUEST_INSTITUTE_ID))
    if guest is not None:
        return guest
    role = db.scalar(select(Role).where(Role.name == STUDENT))
    guest = User(
        institute_id=GUEST_INSTITUTE_ID,
        username=GUEST_INSTITUTE_ID.lower(),
        # Random password: nobody can log in as the guest.
        password_hash=hash_password(uuid.uuid4().hex),
        role_id=role.id,
        account_status=ACCOUNT_ACTIVE,
    )
    db.add(guest)
    try:
        db.commit()
    except IntegrityError:  # created by a concurrent request
        db.rollback()
        guest = db.scalar(select(User).where(User.institute_id == GUEST_INSTITUTE_ID))
    return guest


def get_customer(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Customer endpoints: the logged-in user, or the shared guest when no token is sent
    and GUEST_ACCESS is on. An invalid or expired token is still rejected with 401."""
    if credentials is None and GUEST_ACCESS:
        return get_or_create_guest(db)
    return get_current_session(credentials, db).user


def get_optional_customer(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Public endpoints (menu): like get_customer, but None when guest access is off."""
    if credentials is None and not GUEST_ACCESS:
        return None
    return get_customer(credentials, db)


def require_role(*roles: str) -> Callable[..., User]:
    """Dependency factory for role-based authorization, e.g. Depends(require_role("CANTEEN_STAFF"))."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role.name not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource",
            )
        return user

    return checker
