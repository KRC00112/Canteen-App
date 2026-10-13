from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

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
    ADMIN,
    CANTEEN_STAFF,
    FACULTY,
    STUDENT,
    Role,
    User,
    UserSession,
)

# Students and faculty register themselves through their own endpoints.
# Staff/Admin accounts are seeded or assigned by an admin.
ROLE_LABELS = {STUDENT: "Student", FACULTY: "Faculty", CANTEEN_STAFF: "Staff", ADMIN: "Admin"}


def register(db: Session, data: RegisterRequest, role_name: str = STUDENT) -> User:
    institute_id = data.institute_id.strip()

    if db.scalar(select(User).where(User.institute_id == institute_id)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account already exists for this Institute ID",
        )
    if db.scalar(select(User).where(User.username == data.username)) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username is already taken")

    role = db.scalar(select(Role).where(Role.name == role_name))
    user = User(
        institute_id=institute_id,
        username=data.username,
        password_hash=hash_password(data.password),
        role_id=role.id,
        account_status=ACCOUNT_ACTIVE,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login(
    db: Session,
    data: LoginRequest,
    device: Optional[str] = None,
    ip_address: Optional[str] = None,
    portal: Optional[str] = None,
) -> TokenResponse:
    """portal=STUDENT / FACULTY only lets accounts with that role log in; None allows any role."""
    user = db.scalar(select(User).where(User.institute_id == data.institute_id.strip()))
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Institute ID or password"
        )
    if user.account_status != ACCOUNT_ACTIVE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is not active")
    # Checked after the password, so the account type is only revealed to its owner.
    if portal is not None and user.role.name != portal:
        actual = ROLE_LABELS.get(user.role.name, user.role.name)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This is a {actual} account, not a {ROLE_LABELS[portal]} account. "
            f"Please use the {actual} login",
        )

    session = create_session(db, user, device, ip_address)
    return TokenResponse(
        access_token=create_access_token(user, session),
        role=user.role.name,
        user_id=user.id,
        institute_id=user.institute_id,
        username=user.username,
    )


def logout(db: Session, session: UserSession) -> None:
    session.logged_out_at = utcnow()
    db.commit()
