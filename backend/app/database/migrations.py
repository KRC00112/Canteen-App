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
    ("orders", "payment_status", "NOT NULL DEFAULT 'PAID'"),
]


def add_missing_columns(engine: Engine) -> None:
    insp = inspect(engine)
    with engine.begin() as conn:
        for table, column, constraints in NEW_COLUMNS:
            if column in {c["name"] for c in insp.get_columns(table)}:
                continue
            col_type = Base.metadata.tables[table].c[column].type.compile(dialect=engine.dialect)
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type} {constraints}"))
            if column == "food_type" and engine.dialect.name == "postgresql":
                conn.execute(text(
                    "ALTER TABLE food_items ADD CONSTRAINT ck_food_items_food_type "
                    "CHECK (food_type IN ('VEG', 'NON_VEG'))"
                ))
                conn.execute(text("CREATE INDEX ix_food_items_food_type ON food_items (food_type)"))
        for statement in NEW_INDEXES:
            conn.execute(text(statement))
