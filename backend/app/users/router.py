from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.security import get_current_user, require_role
from app.database.database import get_db
from app.database.models import ADMIN, CANTEEN_STAFF, User
from app.users import service
from app.users.schemas import LoggedInUsersOut, UserProfile
from app.users.service import to_profile

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=List[UserProfile])
def list_users(
    staff: User = Depends(require_role(CANTEEN_STAFF, ADMIN)),
    db: Session = Depends(get_db),
):
    """List all registered users (staff/admin only). Password hashes are never returned."""
    return service.list_users(db)


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
