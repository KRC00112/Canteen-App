from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.security import get_current_user, require_role
from app.database.database import get_db
from app.database.models import ADMIN, CANTEEN_STAFF, User
from app.users import service
from app.users.schemas import UserProfile
from app.users.service import to_profile

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=List[UserProfile])
def list_users(
    staff: User = Depends(require_role(CANTEEN_STAFF, ADMIN)),
    db: Session = Depends(get_db),
):
    """List all registered users (staff/admin only). Password hashes are never returned."""
    return service.list_users(db)


@router.get("/me", response_model=UserProfile)
def my_profile(user: User = Depends(get_current_user)):
    """View the logged-in user's profile."""
    return to_profile(user)
