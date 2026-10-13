from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.auth import service
from app.auth.schemas import LoginRequest, RegisterRequest, RegisterResponse, TokenResponse
from app.auth.security import get_current_session, get_current_user
from app.database.database import get_db
from app.database.models import FACULTY, STUDENT, User, UserSession
from app.users.schemas import UserProfile
from app.users.service import to_profile

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _register(db: Session, data: RegisterRequest, role_name: str) -> RegisterResponse:
    user = service.register(db, data, role_name)
    return RegisterResponse(
        message=f"{service.ROLE_LABELS[role_name]} account created successfully",
        user_id=user.id,
        institute_id=user.institute_id,
        username=user.username,
        role=user.role.name,
    )


def _login(db: Session, data: LoginRequest, request: Request, portal=None) -> TokenResponse:
    return service.login(
        db,
        data,
        device=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
        portal=portal,
    )


@router.post("/student/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register_student(data: RegisterRequest, db: Session = Depends(get_db)):
    """Create a STUDENT account (Institute ID, Username, Password, Confirm Password)."""
    return _register(db, data, STUDENT)


@router.post("/faculty/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register_faculty(data: RegisterRequest, db: Session = Depends(get_db)):
    """Create a FACULTY account (Institute ID, Username, Password, Confirm Password)."""
    return _register(db, data, FACULTY)


@router.post("/student/login", response_model=TokenResponse)
def login_student(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Student login. Other account types get 403 telling them which login to use."""
    return _login(db, data, request, STUDENT)


@router.post("/faculty/login", response_model=TokenResponse)
def login_faculty(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Faculty login. Other account types get 403 telling them which login to use."""
    return _login(db, data, request, FACULTY)


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    deprecated=True,
)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """Same as /auth/student/register. Kept so older app builds keep working."""
    return _register(db, data, STUDENT)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Login for any account type (used by staff/admin). Returns a JWT bearer token and the role.

    Students and faculty should use /auth/student/login and /auth/faculty/login.
    """
    return _login(db, data, request)


@router.get("/me", response_model=UserProfile)
def me(user: User = Depends(get_current_user)):
    """Return the user that owns the current token."""
    return to_profile(user)


@router.post("/logout")
def logout(session: UserSession = Depends(get_current_session), db: Session = Depends(get_db)):
    """End this login session. The token stops working immediately."""
    service.logout(db, session)
    return {"message": "Logged out successfully"}
