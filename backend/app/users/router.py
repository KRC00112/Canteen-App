from fastapi import APIRouter, Depends

from app.auth.security import get_current_user
from app.database.models import User
from app.users.schemas import UserProfile
from app.users.service import to_profile

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserProfile)
def my_profile(user: User = Depends(get_current_user)):
    """View the logged-in user's profile."""
    return to_profile(user)
