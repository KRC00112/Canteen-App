from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserProfile(BaseModel):
    id: int
    institute_id: str
    username: str
    role: str
    account_status: str
    created_at: Optional[datetime]
