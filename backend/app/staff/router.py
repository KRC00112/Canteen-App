from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.security import require_role
from app.database.database import get_db
from app.database.models import ADMIN, CANTEEN_STAFF, User
from app.staff import service
from app.staff.service import StaffOrderOut

router = APIRouter(prefix="/staff", tags=["Staff"])


@router.get("/orders", response_model=List[StaffOrderOut])
def incoming_orders(
    status: Optional[str] = Query(None, description="Filter by status, e.g. PLACED"),
    staff: User = Depends(require_role(CANTEEN_STAFF, ADMIN)),
    db: Session = Depends(get_db),
):
    """Incoming orders for canteen staff. Students/Faculty get 403 Forbidden."""
    return service.list_orders(db, status)
