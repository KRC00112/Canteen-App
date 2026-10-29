"""Read-only SQL views for browsing users, orders and food items in pgAdmin / the Neon console.

Views are computed live from the underlying tables, so they are never stale.
"""
from sqlalchemy import text
from sqlalchemy.engine import Engine

# A session counts as "logged in" until it is logged out or its token expires.
_ACTIVE = "s.logged_out_at IS NULL AND s.expires_at > now()"

VIEWS = {
    # Every registered user, combined with their login status.
    "users_overview": f"""
        SELECT
            u.id                                      AS user_id,
            u.institute_id,
            u.username,
            u.email,
            r.name                                    AS role,
            u.account_status,
            u.created_at                              AS registered_at,
            COUNT(s.id) FILTER (WHERE {_ACTIVE}) > 0  AS is_logged_in,
            COUNT(s.id) FILTER (WHERE {_ACTIVE})      AS active_sessions,
            COUNT(s.id)                               AS total_logins,
            MAX(s.created_at)                         AS last_login_at,
            MAX(s.last_seen_at)                       AS last_seen_at
        FROM users u
        JOIN roles r ON r.id = u.role_id
        LEFT JOIN user_sessions s ON s.user_id = u.id
        GROUP BY u.id, r.name
        ORDER BY u.id
    """,
    # Only people logged in right now: one row per active login (phone, Postman, ...).
    "logged_in_users": f"""
        SELECT
            u.id            AS user_id,
            u.institute_id,
            u.username,
            r.name          AS role,
            s.created_at    AS logged_in_at,
            s.last_seen_at,
            s.expires_at,
            s.device,
            s.ip_address,
            s.session_id
        FROM user_sessions s
        JOIN users u ON u.id = s.user_id
        JOIN roles r ON r.id = u.role_id
        WHERE {_ACTIVE}
        ORDER BY s.last_seen_at DESC
    """,
    # The one permanent main canteen admin account (no password hash).
    "admin_account": f"""
        SELECT
            u.id                                      AS user_id,
            u.institute_id,
            u.username,
            r.name                                    AS role,
            u.account_status,
            u.created_at,
            COUNT(s.id) FILTER (WHERE {_ACTIVE}) > 0  AS is_logged_in,
            MAX(s.created_at)                         AS last_login_at
        FROM users u
        JOIN roles r ON r.id = u.role_id
        LEFT JOIN user_sessions s ON s.user_id = u.id
        WHERE r.name = 'ADMIN'
        GROUP BY u.id, r.name
    """,
    # Every order, newest first, with the customer and what they ordered.
    "orders_overview": """
        SELECT
            o.order_id,
            u.institute_id,
            u.username                                   AS customer,
            r.name                                       AS role,
            o.status,
            o.total_amount,
            o.payment_method,
            o.payment_status,
            o.paid_at,
            o.cash_received,
            p.razorpay_payment_id                        AS payment_id,
            STRING_AGG(f.name || ' x' || oi.quantity, ', ' ORDER BY oi.id) AS items,
            o.created_at                                 AS placed_at,
            o.estimated_ready_at
        FROM orders o
        JOIN users u ON u.id = o.user_id
        JOIN roles r ON r.id = u.role_id
        JOIN order_items oi ON oi.order_id = o.id
        JOIN food_items f ON f.id = oi.food_item_id
        LEFT JOIN payments p ON p.order_id = o.id
        GROUP BY o.id, u.id, r.name, p.razorpay_payment_id
        ORDER BY o.created_at DESC
    """,
    # Every order's timeline, newest first: placed, preparing, ready, served/cancelled,
    # cash received, refunded, and which staff member did it.
    "order_timeline": """
        SELECT
            o.order_id,
            cu.username                                  AS customer,
            e.event,
            e.created_at                                 AS at,
            by_u.username                                AS done_by,
            by_r.name                                    AS done_by_role,
            e.note
        FROM order_events e
        JOIN orders o ON o.id = e.order_id
        JOIN users cu ON cu.id = o.user_id
        LEFT JOIN users by_u ON by_u.id = e.changed_by_id
        LEFT JOIN roles by_r ON by_r.id = by_u.role_id
        ORDER BY e.created_at DESC, e.id DESC
    """,
    # Every food item with its category, Veg / Non-Veg type and live stock.
    "items_overview": """
        SELECT
            f.id                         AS food_id,
            f.name,
            c.name                       AS category,
            f.food_type,
            f.price,
            f.avg_cooking_time_minutes,
            f.ingredients,
            i.quantity                   AS stock,
            i.availability               AS available
        FROM food_items f
        JOIN categories c ON c.id = f.category_id
        LEFT JOIN inventory i ON i.food_item_id = f.id
        WHERE f.removed_at IS NULL
        ORDER BY c.id, f.food_type, f.name
    """,
}


# Views that were renamed; dropped so the old name doesn't linger in the database.
RETIRED_VIEWS = ["menu_overview"]


def create_views(engine: Engine) -> None:
    if engine.dialect.name != "postgresql":
        return  # FILTER/now() syntax is PostgreSQL-specific
    with engine.begin() as conn:
        for name in RETIRED_VIEWS:
            conn.execute(text(f"DROP VIEW IF EXISTS {name}"))
        for name, query in VIEWS.items():
            conn.execute(text(f"DROP VIEW IF EXISTS {name}"))
            conn.execute(text(f"CREATE VIEW {name} AS {query}"))
