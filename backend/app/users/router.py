from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import activity
from app.auth.schemas import EmailUpdate
from app.auth.security import get_current_user, require_role, verify_password
from app.auth.service import ensure_email_free
from app.database.database import get_db
from app.database.models import ADMIN, CANTEEN_STAFF, User
from app.users import service
from app.users.schemas import LoggedInUsersOut, UserProfile, UserWithLoginStatus
from app.users.service import to_profile

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=List[UserWithLoginStatus])
def list_users(
    role: Optional[Literal["STUDENT", "FACULTY", "CANTEEN_STAFF", "ADMIN"]] = Query(
        None, description="Only users with this role"
    ),
    staff: User = Depends(require_role(CANTEEN_STAFF, ADMIN)),
    db: Session = Depends(get_db),
):
    """All registered users with their login status (staff/admin only). No password hashes."""
    return service.list_users(db, role)


@router.get("/logged-in", response_model=LoggedInUsersOut)
def logged_in_users(
    staff: User = Depends(require_role(CANTEEN_STAFF, ADMIN)),
    db: Session = Depends(get_db),
):
    """All users currently logged in (active, not logged out, not expired), staff/admin only."""
    return service.list_logged_in_users(db)


@router.get("/me", response_model=UserProfile)
def my_profile(user: User = Depends(get_current_user)):
    """View the logged-in user's profile."""
    return to_profile(user)


@router.put("/me/email", response_model=UserProfile)
def set_my_email(data: EmailUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Add or change the email used for "Forgot password". Needs the current password."""
    if not verify_password(data.password, user.password_hash):
        # 400, not 401: the app treats 401 as "logged out".
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password")
    ensure_email_free(db, data.email, except_user_id=user.id)
    user.email = data.email
    db.commit()
    activity.event("Recovery email saved")
    return to_profile(user)
