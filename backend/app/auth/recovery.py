"""Forgot password: email a one-time 6-digit code, then reset the password with it.

Available to students, faculty and staff. The admin's password comes from the server
config (SEED_ADMIN_PASSWORD), so the admin account can't be reset this way.
"""
import secrets
from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import activity
from app.auth.schemas import ForgotPasswordRequest, ForgotPasswordResponse, ResetPasswordRequest
from app.auth.security import as_utc, hash_password, utcnow, verify_password
from app.config import OTP_EXPIRE_MINUTES, OTP_MAX_ATTEMPTS, OTP_RESEND_SECONDS
from app.database.models import ADMIN, PasswordReset, User
from app.email import EmailError, send_email


def mask_email(email: str) -> str:
    name, _, domain = email.partition("@")
    return f"{name[0]}***@{domain}"


def _get_user(db: Session, institute_id: str) -> User:
    user = db.scalar(select(User).where(User.institute_id == institute_id.strip()))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No account with this Institute ID")
    if user.role.name == ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The admin password can't be reset here; it is set in the server config",
        )
    return user


def _latest_code(db: Session, user: User):
    return db.scalar(
        select(PasswordReset)
        .where(PasswordReset.user_id == user.id, PasswordReset.used_at.is_(None))
        .order_by(PasswordReset.id.desc())
    )


def request_code(db: Session, data: ForgotPasswordRequest) -> ForgotPasswordResponse:
    user = _get_user(db, data.institute_id)
    if not user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No email is saved on this account, so the password can't be reset by email. "
            "Please contact the canteen admin",
        )

    now = utcnow()
    previous = _latest_code(db, user)
    if previous is not None:
        wait = OTP_RESEND_SECONDS - int((now - as_utc(previous.created_at)).total_seconds())
        if wait > 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"A code was just sent. Please wait {wait} seconds before asking for another",
            )
        previous.used_at = now  # only the newest code works

    code = f"{secrets.randbelow(1_000_000):06d}"
    db.add(PasswordReset(
        user_id=user.id,
        code_hash=hash_password(code),
        created_at=now,
        expires_at=now + timedelta(minutes=OTP_EXPIRE_MINUTES),
    ))
    try:
        send_email(
            user.email,
            "Your Canteen App password reset code",
            f"Hi {user.username},\n\nYour password reset code is {code}\n\n"
            f"It expires in {OTP_EXPIRE_MINUTES} minutes. If you didn't ask for this, ignore this email; "
            "your password stays the same.\n",
            f"<p>Hi {user.username},</p><p>Your password reset code is</p>"
            f"<p style=\"font-size:28px;font-weight:bold;letter-spacing:6px\">{code}</p>"
            f"<p>It expires in {OTP_EXPIRE_MINUTES} minutes. If you didn't ask for this, ignore this email; "
            "your password stays the same.</p>",
        )
    except EmailError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The email could not be sent right now. Please try again in a minute",
        )
    db.commit()
    activity.set_user(user)
    activity.event(f"Password reset code emailed to {mask_email(user.email)}")
    return ForgotPasswordResponse(
        message=f"A 6-digit code was sent to {mask_email(user.email)}",
        email=mask_email(user.email),
        expires_in_minutes=OTP_EXPIRE_MINUTES,
    )


def reset_password(db: Session, data: ResetPasswordRequest) -> None:
    user = _get_user(db, data.institute_id)
    reset = _latest_code(db, user)
    now = utcnow()
    if reset is None or as_utc(reset.expires_at) <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This code has expired or was already used. Please ask for a new code",
        )
    activity.set_user(user)
    if not verify_password(data.otp, reset.code_hash):
        reset.attempts += 1
        left = OTP_MAX_ATTEMPTS - reset.attempts
        if left <= 0:
            reset.used_at = now
        db.commit()
        activity.event(f"Password reset: wrong code ({max(left, 0)} attempts left)")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Incorrect code. {left} attempt(s) left" if left > 0
            else "Too many wrong attempts. Please ask for a new code",
        )

    user.password_hash = hash_password(data.new_password)
    reset.used_at = now
    # Log the account out everywhere, in case someone else knew the old password.
    for s in user.sessions:
        if s.logged_out_at is None:
            s.logged_out_at = now
    db.commit()
    activity.event("Password reset with emailed code; all sessions ended")
