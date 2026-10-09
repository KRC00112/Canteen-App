from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.cart import service
from app.cart.service import AddCartItem, CartOut, UpdateCartItem
from app.database.database import get_db
from app.database.models import User

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.get("", response_model=CartOut)
def view_cart(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """View the current user's cart with subtotal and total."""
    return service.get_cart(db, user)


@router.post("/items", response_model=CartOut, status_code=status.HTTP_201_CREATED)
def add_to_cart(
    data: AddCartItem, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Add a food item to the cart (adds to the quantity if it is already in the cart)."""
    return service.add_item(db, user, data)


@router.put("/items/{item_id}", response_model=CartOut)
def update_cart_item(
    item_id: int,
    data: UpdateCartItem,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change the quantity of a cart item."""
    return service.update_item(db, user, item_id, data)


@router.delete("/items/{item_id}", response_model=CartOut)
def remove_cart_item(
    item_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Remove an item from the cart."""
    return service.remove_item(db, user, item_id)


@router.delete("", response_model=CartOut)
def clear_cart(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Remove all items from the cart."""
    return service.clear_cart(db, user)
