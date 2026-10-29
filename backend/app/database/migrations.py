"""Tiny add-column migrations for databases created before a column existed.

create_all() only creates missing tables, never missing columns, so new columns on
existing tables are added here. Safe to run on every start.
"""
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from app.database.database import Base

# Indexes on new columns (create_all only adds indexes for tables it creates).
NEW_INDEXES = ["CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email ON users (email)"]

# (table, column, constraints after the column type)
NEW_COLUMNS = [
    ("food_items", "food_type", "NOT NULL DEFAULT 'VEG'"),
    ("food_items", "ingredients", ""),
    ("food_items", "avg_cooking_time_minutes", "NOT NULL DEFAULT 10"),
    ("cart_items", "reserved_until", ""),
    ("orders", "estimated_ready_at", ""),
    ("food_items", "removed_at", ""),
    ("users", "email", ""),
    ("orders", "payment_method", "NOT NULL DEFAULT 'UPI'"),
    ("orders", "paid_at", ""),
    ("orders", "payment_status", "NOT NULL DEFAULT 'PENDING'"),
    ("orders", "cash_received", ""),
    ("orders", "pickup_code", ""),
    ("payments", "refund_id", ""),
    ("payments", "refunded_at", ""),
    ("notifications", "order_id", ""),
]

# Run once, right after the column is added, to fill it in for existing rows.
BACKFILLS = {
    # Orders placed before this column existed were paid online if they have a payment;
    # the rest (placed while payments were off) are collected at the counter.
    ("orders", "payment_status"): [
        "UPDATE orders SET payment_status = 'PAID', paid_at = created_at "
        "WHERE id IN (SELECT order_id FROM payments WHERE order_id IS NOT NULL)"
    ],
}


# Run on every start; each is a no-op once done.
ALWAYS = [
    # Payment methods were briefly saved as ONLINE / CASH; the app uses UPI / CASH_ON_PICKUP.
    "UPDATE orders SET payment_method = 'UPI' WHERE payment_method = 'ONLINE'",
    "UPDATE orders SET payment_method = 'CASH_ON_PICKUP' WHERE payment_method = 'CASH'",
]
# PostgreSQL only (SQLite doesn't enforce lengths or support ALTER COLUMN).
ALWAYS_POSTGRES = [
    "ALTER TABLE orders ALTER COLUMN payment_method TYPE VARCHAR(30)",
    "ALTER TABLE orders ALTER COLUMN payment_method SET DEFAULT 'UPI'",
]


def add_missing_columns(engine: Engine) -> None:
    insp = inspect(engine)
    with engine.begin() as conn:
        for table, column, constraints in NEW_COLUMNS:
            if column in {c["name"] for c in insp.get_columns(table)}:
                continue
            col_type = Base.metadata.tables[table].c[column].type.compile(dialect=engine.dialect)
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type} {constraints}"))
            for statement in BACKFILLS.get((table, column), []):
                conn.execute(text(statement))
            if column == "food_type" and engine.dialect.name == "postgresql":
                conn.execute(text(
                    "ALTER TABLE food_items ADD CONSTRAINT ck_food_items_food_type "
                    "CHECK (food_type IN ('VEG', 'NON_VEG'))"
                ))
                conn.execute(text("CREATE INDEX ix_food_items_food_type ON food_items (food_type)"))
        for statement in NEW_INDEXES:
            conn.execute(text(statement))
        for statement in ALWAYS + (ALWAYS_POSTGRES if engine.dialect.name == "postgresql" else []):
            conn.execute(text(statement))
