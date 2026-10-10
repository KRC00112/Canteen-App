"""Read-only SQL views for browsing users in pgAdmin / the Neon console.

Views are computed live from the users and user_sessions tables, so they are never stale.
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
}


def create_views(engine: Engine) -> None:
    if engine.dialect.name != "postgresql":
        return  # FILTER/now() syntax is PostgreSQL-specific
    with engine.begin() as conn:
        for name, query in VIEWS.items():
            conn.execute(text(f"DROP VIEW IF EXISTS {name}"))
            conn.execute(text(f"CREATE VIEW {name} AS {query}"))
