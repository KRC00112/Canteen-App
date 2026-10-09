from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.schemas import LoginRequest, RegisterRequest, TokenResponse
from app.auth.security import create_access_token, hash_password, verify_password
from app.database.models import ACCOUNT_ACTIVE, STUDENT, Role, User

# Self-registered accounts are customers. Faculty/Staff/Admin roles are assigned by an admin.
DEFAULT_ROLE = STUDENT


def register(db: Session, data: RegisterRequest) -> User:
    institute_id = data.institute_id.strip()

    if db.scalar(select(User).where(User.institute_id == institute_id)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account already exists for this Institute ID",
        )
    if db.scalar(select(User).where(User.username == data.username)) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username is already taken")

    role = db.scalar(select(Role).where(Role.name == DEFAULT_ROLE))
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


def login(db: Session, data: LoginRequest) -> TokenResponse:
    user = db.scalar(select(User).where(User.institute_id == data.institute_id.strip()))
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Institute ID or password"
        )
    if user.account_status != ACCOUNT_ACTIVE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is not active")

    return TokenResponse(
        access_token=create_access_token(user),
        role=user.role.name,
        user_id=user.id,
        institute_id=user.institute_id,
        username=user.username,
    )
