from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class UserProfile(BaseModel):
    id: int
    institute_id: str
    username: str
    role: str
    account_status: str
    created_at: Optional[datetime]


class UserWithLoginStatus(UserProfile):
    is_logged_in: bool
    active_sessions: int
    total_logins: int
    last_login_at: Optional[datetime]
    last_seen_at: Optional[datetime]


class SessionOut(BaseModel):
    session_id: str
    logged_in_at: datetime
    last_seen_at: datetime
    expires_at: datetime
    device: Optional[str]
    ip_address: Optional[str]


class LoggedInUser(BaseModel):
    user_id: int
    institute_id: str
    username: str
    role: str
    active_sessions: int
    last_login_at: datetime
    last_seen_at: datetime
    sessions: List[SessionOut]


class LoggedInUsersOut(BaseModel):
    total_logged_in_users: int
    total_active_sessions: int
    users: List[LoggedInUser]
