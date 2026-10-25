from typing import Optional

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.auth import recovery, service
from app.auth.schemas import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    TokenResponse,
)
from app.auth.security import get_current_session, get_current_user
from app.database.database import get_db
from app.database.models import ACCOUNT_PENDING, ADMIN, CANTEEN_STAFF, FACULTY, STUDENT, User, UserSession
from app.users.schemas import UserProfile
from app.users.service import to_profile

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _register(
    db: Session, data: RegisterRequest, role_name: str, message: Optional[str] = None, **kwargs
) -> RegisterResponse:
    user = service.register(db, data, role_name, **kwargs)
    return RegisterResponse(
        message=message or f"{service.ROLE_LABELS[role_name]} account created successfully",
        user_id=user.id,
        institute_id=user.institute_id,
        username=user.username,
        role=user.role.name,
        account_status=user.account_status,
        email=user.email,
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


@router.post("/staff/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register_staff(data: RegisterRequest, db: Session = Depends(get_db)):
    """Create a CANTEEN_STAFF account (same fields). It is PENDING until the admin approves it."""
    return _register(
        db,
        data,
        CANTEEN_STAFF,
        "Staff account created. You can log in once the admin approves it",
        account_status=ACCOUNT_PENDING,
    )


@router.post("/student/login", response_model=TokenResponse)
def login_student(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Student login. Other account types get 403 telling them which login to use."""
    return _login(db, data, request, STUDENT)


@router.post("/faculty/login", response_model=TokenResponse)
def login_faculty(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Faculty login. Other account types get 403 telling them which login to use."""
    return _login(db, data, request, FACULTY)


@router.post("/staff/login", response_model=TokenResponse)
def login_staff(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Canteen staff login. Pending (unapproved) staff and other account types get 403."""
    return _login(db, data, request, CANTEEN_STAFF)


@router.post("/admin/login", response_model=TokenResponse)
def login_admin(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Main canteen admin login. Only ADMIN accounts; everyone else gets 403."""
    return _login(db, data, request, ADMIN)


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


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Step 1 of "Forgot password" (students, faculty, staff): email a 6-digit code to the
    account's saved email. The code expires in 10 minutes; a new one can be asked for after 60 s."""
    return recovery.request_code(db, data)


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Step 2: Institute ID + the emailed code + new password. 5 wrong tries end the code.
    On success the account is logged out on every device; log in with the new password."""
    recovery.reset_password(db, data)
    return {"message": "Password changed. Please log in with your new password"}


@router.get("/me", response_model=UserProfile)
def me(user: User = Depends(get_current_user)):
    """Return the user that owns the current token."""
    return to_profile(user)


@router.post("/logout")
def logout(session: UserSession = Depends(get_current_session), db: Session = Depends(get_db)):
    """End this login session. The token stops working immediately."""
    service.logout(db, session)
    return {"message": "Logged out successfully"}
