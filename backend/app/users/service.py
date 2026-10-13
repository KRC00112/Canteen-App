from typing import Dict, List, Optional

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.auth.security import utcnow
from app.database.models import Role, User, UserSession
from app.users.schemas import (
    LoggedInUser,
    LoggedInUsersOut,
    SessionOut,
    UserProfile,
    UserWithLoginStatus,
)


def to_profile(user: User) -> UserProfile:
    return UserProfile(
        id=user.id,
        institute_id=user.institute_id,
        username=user.username,
        role=user.role.name,
        account_status=user.account_status,
        created_at=user.created_at,
    )


def list_users(db: Session, role: Optional[str] = None) -> List[UserWithLoginStatus]:
    """Every registered user, combined with their login status."""
    active = (UserSession.logged_out_at.is_(None)) & (UserSession.expires_at > utcnow())
    stats = {
        row.user_id: row
        for row in db.execute(
            select(
                UserSession.user_id,
                func.sum(case((active, 1), else_=0)).label("active_sessions"),
                func.count(UserSession.id).label("total_logins"),
                func.max(UserSession.created_at).label("last_login_at"),
                func.max(UserSession.last_seen_at).label("last_seen_at"),
            ).group_by(UserSession.user_id)
        )
    }
    result = []
    stmt = select(User).order_by(User.id)
    if role is not None:
        stmt = stmt.join(Role).where(Role.name == role)
    for u in db.scalars(stmt):
        st = stats.get(u.id)
        active_sessions = int(st.active_sessions) if st else 0
        result.append(
            UserWithLoginStatus(
                **to_profile(u).model_dump(),
                is_logged_in=active_sessions > 0,
                active_sessions=active_sessions,
                total_logins=st.total_logins if st else 0,
                last_login_at=st.last_login_at if st else None,
                last_seen_at=st.last_seen_at if st else None,
            )
        )
    return result


def list_logged_in_users(db: Session) -> LoggedInUsersOut:
    """Users with at least one session that is not logged out and not expired."""
    sessions = db.scalars(
        select(UserSession)
        .where(UserSession.logged_out_at.is_(None), UserSession.expires_at > utcnow())
        .order_by(UserSession.created_at.desc())
    ).all()

    by_user: Dict[int, List[UserSession]] = {}
    for s in sessions:
        by_user.setdefault(s.user_id, []).append(s)

    users = []
    for user_sessions in by_user.values():
        u = user_sessions[0].user
        users.append(
            LoggedInUser(
                user_id=u.id,
                institute_id=u.institute_id,
                username=u.username,
                role=u.role.name,
                active_sessions=len(user_sessions),
                last_login_at=max(s.created_at for s in user_sessions),
                last_seen_at=max(s.last_seen_at for s in user_sessions),
                sessions=[
                    SessionOut(
                        session_id=s.session_id,
                        logged_in_at=s.created_at,
                        last_seen_at=s.last_seen_at,
                        expires_at=s.expires_at,
                        device=s.device,
                        ip_address=s.ip_address,
                    )
                    for s in user_sessions
                ],
            )
        )
    users.sort(key=lambda x: x.last_seen_at, reverse=True)
    return LoggedInUsersOut(
        total_logged_in_users=len(users), total_active_sessions=len(sessions), users=users
    )
