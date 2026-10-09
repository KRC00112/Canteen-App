from pydantic import BaseModel, Field, model_validator


class RegisterRequest(BaseModel):
    """Fields match the app's Register screen."""

    institute_id: str = Field(
        ..., min_length=1, max_length=30, pattern=r"^[A-Za-z0-9_-]+$", examples=["2621532"]
    )
    username: str = Field(
        ..., min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.]+$", examples=["umar"]
    )
    password: str = Field(..., min_length=6, max_length=128, examples=["Umar@123"])
    confirm_password: str = Field(..., examples=["Umar@123"])

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
