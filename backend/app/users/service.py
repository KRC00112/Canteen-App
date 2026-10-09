from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import User
from app.users.schemas import UserProfile


def to_profile(user: User) -> UserProfile:
    return UserProfile(
        id=user.id,
        institute_id=user.institute_id,
        username=user.username,
        role=user.role.name,
        account_status=user.account_status,
        created_at=user.created_at,
    )


def list_users(db: Session) -> List[UserProfile]:
    return [to_profile(u) for u in db.scalars(select(User).order_by(User.id))]
