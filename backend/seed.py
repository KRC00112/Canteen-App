"""Seed the database with roles, a staff account and menu data.

Safe to run multiple times: existing rows are left unchanged.

    python seed.py
"""
from decimal import Decimal

from sqlalchemy import select

from app.auth.security import hash_password
from app.config import SEED_STAFF_INSTITUTE_ID, SEED_STAFF_PASSWORD, SEED_STAFF_USERNAME
from app.database.database import SessionLocal, init_db
from app.database.models import (
    ACCOUNT_ACTIVE,
    ALL_ROLES,
    CANTEEN_STAFF,
    Category,
    FoodItem,
    Inventory,
    Role,
    User,
)

# (name, description, category, price, quantity)
MENU = [
    ("Veg Biryani", "Fragrant basmati rice cooked with vegetables and spices", "Meals", "80", 25),
    ("Masala Dosa", "Crispy dosa with potato masala, chutney and sambar", "South Indian", "50", 30),
    ("Chicken Roll", "Spiced chicken wrapped in a paratha", "Snacks", "70", 20),
    ("Samosa", "Crispy pastry filled with spiced potatoes", "Snacks", "20", 50),
    ("Tea", "Hot masala chai", "Beverages", "15", 100),
    ("Coffee", "Hot filter coffee", "Beverages", "25", 50),
]


def get_or_create(db, model, defaults=None, **filters):
    obj = db.scalar(select(model).filter_by(**filters))
    if obj is None:
        obj = model(**filters, **(defaults or {}))
        db.add(obj)
        db.flush()
    return obj


def seed():
    init_db()
    db = SessionLocal()
    try:
        roles = {name: get_or_create(db, Role, name=name) for name in ALL_ROLES}

        get_or_create(
            db,
            User,
            institute_id=SEED_STAFF_INSTITUTE_ID,
            defaults={
                "username": SEED_STAFF_USERNAME,
                "password_hash": hash_password(SEED_STAFF_PASSWORD),
                "role_id": roles[CANTEEN_STAFF].id,
                "account_status": ACCOUNT_ACTIVE,
            },
        )

        for name, description, category, price, quantity in MENU:
            cat = get_or_create(db, Category, name=category)
            food = get_or_create(
                db,
                FoodItem,
                name=name,
                defaults={"description": description, "category_id": cat.id, "price": Decimal(price)},
            )
            get_or_create(
                db,
                Inventory,
                food_item_id=food.id,
                defaults={"quantity": quantity, "availability": quantity > 0},
            )

        db.commit()
        print("Seed complete.")
        print(f"  Staff login: Institute ID {SEED_STAFF_INSTITUTE_ID} / {SEED_STAFF_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
