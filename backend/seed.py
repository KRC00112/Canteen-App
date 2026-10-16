"""Seed the database with roles, a staff account, an admin account and menu data.

Safe to run multiple times: existing rows are left unchanged.

    python seed.py
"""
from decimal import Decimal

from sqlalchemy import select, text

from app.auth.security import hash_password
from app.config import (
    SEED_ADMIN_INSTITUTE_ID,
    SEED_ADMIN_PASSWORD,
    SEED_ADMIN_USERNAME,
    SEED_STAFF_INSTITUTE_ID,
    SEED_STAFF_PASSWORD,
    SEED_STAFF_USERNAME,
)
from app.database.database import SessionLocal, init_db
from app.database.models import (
    ACCOUNT_ACTIVE,
    ADMIN,
    ALL_ROLES,
    CANTEEN_STAFF,
    NON_VEG,
    VEG,
    Category,
    FoodItem,
    Inventory,
    Role,
    User,
)

# (name, description, category, price, quantity, food type, ingredients, avg cooking minutes)
MENU = [
    ("Veg Biryani", "Fragrant basmati rice cooked with vegetables and spices", "Meals", "80", 25,
     VEG, ["Basmati rice", "Mixed vegetables", "Onion", "Curd", "Biryani spices"], 20),
    ("Masala Dosa", "Crispy dosa with potato masala, chutney and sambar", "South Indian", "50", 30,
     VEG, ["Rice batter", "Urad dal", "Potato", "Onion", "Coconut chutney", "Sambar"], 10),
    ("Chicken Roll", "Spiced chicken wrapped in a paratha", "Snacks", "70", 20,
     NON_VEG, ["Chicken", "Paratha", "Onion", "Capsicum", "Spices"], 12),
    ("Samosa", "Crispy pastry filled with spiced potatoes", "Snacks", "20", 50,
     VEG, ["Flour", "Potato", "Green peas", "Spices"], 5),
    ("Tea", "Hot masala chai", "Beverages", "15", 100,
     VEG, ["Tea leaves", "Milk", "Sugar", "Ginger", "Cardamom"], 3),
    ("Coffee", "Hot filter coffee", "Beverages", "25", 50,
     VEG, ["Coffee decoction", "Milk", "Sugar"], 3),
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
        # There is exactly one permanent main canteen admin; it never registers.
        admin_role_id = roles[ADMIN].id
        if db.scalar(select(User).where(User.role_id == admin_role_id)) is None:
            db.add(User(
                institute_id=SEED_ADMIN_INSTITUTE_ID,
                username=SEED_ADMIN_USERNAME,
                password_hash=hash_password(SEED_ADMIN_PASSWORD),
                role_id=admin_role_id,
                account_status=ACCOUNT_ACTIVE,
            ))
            db.flush()
        # The database itself refuses a second ADMIN account.
        db.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_users_single_admin "
            f"ON users (role_id) WHERE role_id = {admin_role_id}"
        ))

        for name, description, category, price, quantity, food_type, ingredients, cook_minutes in MENU:
            cat = get_or_create(db, Category, name=category)
            details = {
                "food_type": food_type,
                "ingredients": ingredients,
                "avg_cooking_time_minutes": cook_minutes,
            }
            food = get_or_create(
                db,
                FoodItem,
                name=name,
                defaults={
                    "description": description,
                    "category_id": cat.id,
                    "price": Decimal(price),
                    **details,
                },
            )
            # Items created before these columns existed have no ingredients yet: fill them in once.
            if food.ingredients is None:
                for field, value in details.items():
                    setattr(food, field, value)
            get_or_create(
                db,
                Inventory,
                food_item_id=food.id,
                defaults={"quantity": quantity, "availability": quantity > 0},
            )

        db.commit()
        print("Seed complete.")
        print(f"  Staff login: Institute ID {SEED_STAFF_INSTITUTE_ID} / {SEED_STAFF_PASSWORD}")
        print(f"  Admin login: Institute ID {SEED_ADMIN_INSTITUTE_ID} / {SEED_ADMIN_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
