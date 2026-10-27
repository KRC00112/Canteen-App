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

SEED_ADMIN_INSTITUTE_ID = os.getenv("SEED_ADMIN_INSTITUTE_ID", "ADMIN001")
SEED_ADMIN_USERNAME = os.getenv("SEED_ADMIN_USERNAME", "canteen_admin")
SEED_ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "Admin@123")

# Password recovery ("Forgot password" emails a one-time code)
OTP_EXPIRE_MINUTES = int(os.getenv("OTP_EXPIRE_MINUTES", "10"))
OTP_MAX_ATTEMPTS = int(os.getenv("OTP_MAX_ATTEMPTS", "5"))
OTP_RESEND_SECONDS = int(os.getenv("OTP_RESEND_SECONDS", "60"))

# Email sending. Render's free plan blocks SMTP, so production uses Brevo's HTTP API
# (free: 300 emails/day). SMTP is for local use. With neither set, emails are printed
# to the server log instead (for testing).
EMAIL_FROM = os.getenv("EMAIL_FROM", "")
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "Canteen App")
BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

# Razorpay payment orders. The secret must remain server-side.
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")

# Stock rules
# Adding/changing a cart item holds that stock for this long, so nobody else can take it.
CART_HOLD_MINUTES = int(os.getenv("CART_HOLD_MINUTES", "10"))
# At or below this stock an item is "low stock" and the per-customer limit applies.
LOW_STOCK_THRESHOLD = int(os.getenv("LOW_STOCK_THRESHOLD", "5"))
LOW_STOCK_MAX_PER_CUSTOMER = int(os.getenv("LOW_STOCK_MAX_PER_CUSTOMER", "2"))
