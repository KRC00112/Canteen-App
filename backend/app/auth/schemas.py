import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def check_email(value: Optional[str]) -> Optional[str]:
    """Lowercase and validate an email; empty means none."""
    value = (value or "").strip().lower() or None
    if value is not None and not EMAIL_PATTERN.match(value):
        raise ValueError("Enter a valid email address")
    return value


class RegisterRequest(BaseModel):
    """Fields match the app's Register screen. Email is optional; it is needed to reset a
    forgotten password."""

    institute_id: str = Field(
        ..., min_length=1, max_length=30, pattern=r"^[A-Za-z0-9_-]+$", examples=["2621532"]
    )
    username: str = Field(
        ..., min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.]+$", examples=["umar"]
    )
    password: str = Field(..., min_length=6, max_length=128, examples=["Umar@123"])
    confirm_password: str = Field(..., examples=["Umar@123"])
    email: Optional[str] = Field(None, max_length=254, examples=["umar@gmail.com"])

    @field_validator("email")
    @classmethod
    def valid_email(cls, v):
        return check_email(v)

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Password and Confirm Password do not match")
        return self


class RegisterResponse(BaseModel):
    message: str
    user_id: int
    institute_id: str
    username: str
    role: str
    account_status: str = "ACTIVE"
    email: Optional[str] = None


class LoginRequest(BaseModel):
    """Fields match the app's Log In screen."""

    institute_id: str = Field(..., min_length=1, examples=["2621532"])
    password: str = Field(..., min_length=1, examples=["Umar@123"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    institute_id: str
    username: str


# ---------- Forgot password ----------

class ForgotPasswordRequest(BaseModel):
    institute_id: str = Field(..., min_length=1, examples=["2621532"])


class ForgotPasswordResponse(BaseModel):
    message: str
    # Masked, e.g. "u***@gmail.com", so the user knows which inbox to check.
    email: str
    expires_in_minutes: int


class ResetPasswordRequest(BaseModel):
    institute_id: str = Field(..., min_length=1, examples=["2621532"])
    otp: str = Field(..., min_length=6, max_length=6, pattern=r"^[0-9]{6}$", examples=["483920"])
    new_password: str = Field(..., min_length=6, max_length=128, examples=["New@1234"])
    confirm_password: str = Field(..., examples=["New@1234"])

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("New Password and Confirm Password do not match")
        return self


class EmailUpdate(BaseModel):
    """Add or change the recovery email. The current password is required."""

    email: str = Field(..., max_length=254, examples=["umar@gmail.com"])
    password: str = Field(..., min_length=1, examples=["Umar@123"])

    @field_validator("email")
    @classmethod
    def valid_email(cls, v):
        v = check_email(v)
        if v is None:
            raise ValueError("Enter a valid email address")
        return v
