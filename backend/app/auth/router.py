from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth import service
from app.auth.schemas import LoginRequest, RegisterRequest, RegisterResponse, TokenResponse
from app.auth.security import get_current_user
from app.database.database import get_db
from app.database.models import User
from app.users.schemas import UserProfile
from app.users.service import to_profile

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """Create a canteen account (Register screen: Institute ID, Username, Password, Confirm Password)."""
    user = service.register(db, data)
    return RegisterResponse(
        message="Account created successfully",
        user_id=user.id,
        institute_id=user.institute_id,
        username=user.username,
        role=user.role.name,
    )


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Login with Institute ID + password. Returns a JWT bearer token and the user's role."""
    return service.login(db, data)


@router.get("/me", response_model=UserProfile)
def me(user: User = Depends(get_current_user)):
    """Return the user that owns the current token."""
    return to_profile(user)


@router.post("/logout")
def logout(user: User = Depends(get_current_user)):
    """JWTs are stateless: the client logs out by discarding its token."""
    return {"message": "Logged out. Please discard the access token on the client."}
