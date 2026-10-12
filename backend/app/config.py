import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/canteen"
)
# Hosting providers (Render, Railway, Heroku, Neon) hand out postgres:// URLs,
# which SQLAlchemy doesn't accept; point them at the psycopg2 driver.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql+psycopg2://" + DATABASE_URL[len("postgres://"):]
JWT_SECRET = os.getenv("JWT_SECRET", "dev-only-insecure-secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

SEED_STAFF_INSTITUTE_ID = os.getenv("SEED_STAFF_INSTITUTE_ID", "STAFF001")
SEED_STAFF_USERNAME = os.getenv("SEED_STAFF_USERNAME", "staff01")
SEED_STAFF_PASSWORD = os.getenv("SEED_STAFF_PASSWORD", "Staff@123")

# Testing mode: customer endpoints (cart, orders, notifications) work without a token by
# using one shared guest account. Set GUEST_ACCESS=false once the app sends tokens.
GUEST_ACCESS = os.getenv("GUEST_ACCESS", "true").lower() == "true"
GUEST_INSTITUTE_ID = os.getenv("GUEST_INSTITUTE_ID", "GUEST001")

# Stock rules
# Adding/changing a cart item holds that stock for this long, so nobody else can take it.
CART_HOLD_MINUTES = int(os.getenv("CART_HOLD_MINUTES", "10"))
# At or below this stock an item is "low stock" and the per-customer limit applies.
LOW_STOCK_THRESHOLD = int(os.getenv("LOW_STOCK_THRESHOLD", "5"))
LOW_STOCK_MAX_PER_CUSTOMER = int(os.getenv("LOW_STOCK_MAX_PER_CUSTOMER", "2"))
