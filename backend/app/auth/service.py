from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import activity
from app.auth.schemas import LoginRequest, RegisterRequest, TokenResponse
from app.auth.security import (
    create_access_token,
    create_session,
    hash_password,
    utcnow,
    verify_password,
)
from app.database.models import (
    ACCOUNT_ACTIVE,
    ACCOUNT_PENDING,
    ADMIN,
    CANTEEN_STAFF,
    FACULTY,
    STUDENT,
    Role,
    User,
    UserSession,
)

# Students, faculty and staff register themselves through their own endpoints.
# Staff accounts stay PENDING until the admin approves them. The one admin is seeded.
ROLE_LABELS = {STUDENT: "Student", FACULTY: "Faculty", CANTEEN_STAFF: "Staff", ADMIN: "Admin"}


def _article(label: str) -> str:
    return f"an {label}" if label[0] in "AEIOU" else f"a {label}"


def ensure_email_free(db: Session, email: Optional[str], except_user_id: Optional[int] = None) -> None:
    if email is None:
        return
    stmt = select(User).where(User.email == email)
    if except_user_id is not None:
        stmt = stmt.where(User.id != except_user_id)
    if db.scalar(stmt) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This email is already used by another account")


def register(
    db: Session, data: RegisterRequest, role_name: str = STUDENT, account_status: str = ACCOUNT_ACTIVE
) -> User:
    institute_id = data.institute_id.strip()

    if db.scalar(select(User).where(User.institute_id == institute_id)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account already exists for this Institute ID",
        )
    if db.scalar(select(User).where(User.username == data.username)) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username is already taken")
    ensure_email_free(db, data.email)

    role = db.scalar(select(Role).where(Role.name == role_name))
    user = User(
        institute_id=institute_id,
        username=data.username,
        password_hash=hash_password(data.password),
        email=data.email,
        role_id=role.id,
        account_status=account_status,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    activity.set_user(user)
    activity.event(f"Registered {ROLE_LABELS[role_name]} account {institute_id} ({user.account_status})")
    return user


def login(
    db: Session,
    data: LoginRequest,
    device: Optional[str] = None,
    ip_address: Optional[str] = None,
    portal: Optional[str] = None,
) -> TokenResponse:
    """portal=STUDENT / FACULTY / CANTEEN_STAFF / ADMIN only lets accounts with that role log in; None allows any role."""
    user = db.scalar(select(User).where(User.institute_id == data.institute_id.strip()))
    if user is None or not verify_password(data.password, user.password_hash):
        activity.event(f"Login failed for Institute ID {data.institute_id.strip()}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Institute ID or password"
        )
    activity.set_user(user)
    if user.account_status == ACCOUNT_PENDING:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your staff account is waiting for admin approval",
        )
    if user.account_status != ACCOUNT_ACTIVE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is not active")
    # Checked after the password, so the account type is only revealed to its owner.
    if portal is not None and user.role.name != portal:
        actual = ROLE_LABELS.get(user.role.name, user.role.name)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This is {_article(actual)} account, not {_article(ROLE_LABELS[portal])} account. "
            f"Please use the {actual} login",
        )

    session = create_session(db, user, device, ip_address)
    activity.event(f"Logged in from {(device or 'unknown device')[:40]}")
    return TokenResponse(
        access_token=create_access_token(user, session),
        role=user.role.name,
        user_id=user.id,
        institute_id=user.institute_id,
        username=user.username,
    )


def logout(db: Session, session: UserSession, portal: Optional[str] = None) -> None:
    """portal works like in login: only that account type can use this logout; None allows any."""
    role = session.user.role.name
    if portal is not None and role != portal:
        actual = ROLE_LABELS.get(role, role)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This is {_article(actual)} account, not {_article(ROLE_LABELS[portal])} account. "
            f"Please use the {actual} logout",
        )
    session.logged_out_at = utcnow()
    db.commit()
    activity.event("Logged out, session ended")
