"""Per-user state: resume link and send history.

Runs on Postgres (set DATABASE_URL — Neon, Supabase, Railway PG) or on SQLite
(the default, so local dev needs no database at all). Same API either way.

Deliberately stores no Google tokens. The OAuth proxy hands us a fresh access
token on every request, so there is nothing here worth stealing.
"""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from . import config

# `id` is the only real dialect split; everything else is portable SQL.
SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS users (
    google_sub   TEXT PRIMARY KEY,
    email        TEXT NOT NULL,
    name         TEXT,
    role         TEXT,
    link         TEXT,
    plan         TEXT NOT NULL DEFAULT 'free',
    subscribed_at        TEXT,
    subscription_ends_at TEXT,
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sends (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    google_sub  TEXT NOT NULL,
    to_email    TEXT NOT NULL,
    company     TEXT,
    subject     TEXT,
    source_url  TEXT,
    message_id  TEXT,
    success     INTEGER NOT NULL,
    error       TEXT,
    sent_at     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sends_user ON sends (google_sub, sent_at);
CREATE INDEX IF NOT EXISTS idx_sends_target ON sends (google_sub, to_email);
"""

SCHEMA_POSTGRES = """
CREATE TABLE IF NOT EXISTS users (
    google_sub   TEXT PRIMARY KEY,
    email        TEXT NOT NULL,
    name         TEXT,
    role         TEXT,
    link         TEXT,
    plan         TEXT NOT NULL DEFAULT 'free',
    subscribed_at        TEXT,
    subscription_ends_at TEXT,
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sends (
    id          BIGSERIAL PRIMARY KEY,
    google_sub  TEXT NOT NULL,
    to_email    TEXT NOT NULL,
    company     TEXT,
    subject     TEXT,
    source_url  TEXT,
    message_id  TEXT,
    success     INTEGER NOT NULL,
    error       TEXT,
    sent_at     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sends_user ON sends (google_sub, sent_at);
CREATE INDEX IF NOT EXISTS idx_sends_target ON sends (google_sub, to_email);
"""


def using_postgres():
    return bool(config.DATABASE_URL)


def backend():
    return "postgres" if using_postgres() else "sqlite"


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sql(query):
    """Queries are written with ? and rewritten for Postgres, which wants %s."""
    return query.replace("?", "%s") if using_postgres() else query


@contextmanager
def _db():
    if using_postgres():
        import psycopg
        from psycopg.rows import dict_row

        conn = psycopg.connect(config.DATABASE_URL, row_factory=dict_row)
    else:
        config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row

    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _rows(conn, query, params=()):
    cur = conn.execute(_sql(query), params)
    return [dict(r) for r in cur.fetchall()]


def _one(conn, query, params=()):
    rows = _rows(conn, query, params)
    return rows[0] if rows else None


# Columns added after the first release. CREATE TABLE IF NOT EXISTS won't add
# them to a database that already exists, so they're applied separately.
MIGRATIONS = [
    ("users", "role", "TEXT"),
    ("users", "link", "TEXT"),
    ("users", "plan", "TEXT NOT NULL DEFAULT 'free'"),
    ("users", "subscribed_at", "TEXT"),
    ("users", "subscription_ends_at", "TEXT"),
]


def init():
    with _db() as conn:
        schema = SCHEMA_POSTGRES if using_postgres() else SCHEMA_SQLITE
        if using_postgres():
            # psycopg has no executescript; it accepts multiple statements
            # in one execute() instead.
            conn.execute(schema)
        else:
            conn.executescript(schema)

        for table, column, decl in MIGRATIONS:
            _add_column(conn, table, column, decl)

        _migrate_resume_link(conn)


def _columns(conn, table):
    if using_postgres():
        rows = _rows(
            conn,
            "SELECT column_name AS name FROM information_schema.columns WHERE table_name = ?",
            (table,),
        )
    else:
        rows = [dict(r) for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    return {r["name"] for r in rows}


def _add_column(conn, table, column, decl):
    if column in _columns(conn, table):
        return
    # SQLite rejects a non-constant default on ALTER; both accept this form.
    conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")


def _migrate_resume_link(conn):
    """Carry old resume_link values into the role-agnostic `link` column.

    resume_link predates recruiters and professionals, for whom the attached URL
    isn't a resume at all. Existing rows keep their value and are tagged as job
    seekers, which is what they were.
    """
    existing = _columns(conn, "users")
    if "resume_link" not in existing:
        return

    conn.execute("UPDATE users SET link = resume_link WHERE link IS NULL AND resume_link IS NOT NULL")
    conn.execute("UPDATE users SET role = 'job_seeker' WHERE role IS NULL AND resume_link IS NOT NULL")


def upsert_user(google_sub, email, name=None):
    with _db() as conn:
        conn.execute(
            _sql(
                """
                INSERT INTO users (google_sub, email, name, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (google_sub) DO UPDATE SET
                    email = EXCLUDED.email,
                    name = COALESCE(EXCLUDED.name, users.name),
                    updated_at = EXCLUDED.updated_at
                """
            ),
            (google_sub, email, name, _now(), _now()),
        )


def get_user(google_sub):
    with _db() as conn:
        return _one(conn, "SELECT * FROM users WHERE google_sub = ?", (google_sub,))


def set_link(google_sub, link):
    """The URL appended to every email. What it *is* depends on the user's role."""
    with _db() as conn:
        conn.execute(
            _sql("UPDATE users SET link = ?, updated_at = ? WHERE google_sub = ?"),
            (link, _now(), google_sub),
        )


def set_role(google_sub, role):
    with _db() as conn:
        conn.execute(
            _sql("UPDATE users SET role = ?, updated_at = ? WHERE google_sub = ?"),
            (role, _now(), google_sub),
        )


def set_plan(google_sub, plan, subscribed_at=None, subscription_ends_at=None):
    """Set the billing plan. Called by whatever records a payment — there is no
    payment processor wired up yet, so today this is an admin action."""
    with _db() as conn:
        conn.execute(
            _sql(
                """
                UPDATE users
                   SET plan = ?, subscribed_at = ?, subscription_ends_at = ?, updated_at = ?
                 WHERE google_sub = ?
                """
            ),
            (plan, subscribed_at, subscription_ends_at, _now(), google_sub),
        )


def total_sent(google_sub):
    """Lifetime successful sends — what the free-plan allowance is counted against."""
    with _db() as conn:
        row = _one(
            conn,
            "SELECT COUNT(*) AS n FROM sends WHERE google_sub = ? AND success = 1",
            (google_sub,),
        )
    return row["n"] if row else 0


def record_sends(google_sub, results):
    rows = [
        (
            google_sub,
            r.get("to"),
            r.get("company"),
            r.get("subject"),
            r.get("source_url"),
            r.get("message_id"),
            1 if r.get("success") else 0,
            r.get("error"),
            _now(),
        )
        for r in results
    ]
    with _db() as conn:
        query = _sql(
            """
            INSERT INTO sends
                (google_sub, to_email, company, subject, source_url,
                 message_id, success, error, sent_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
        )
        if using_postgres():
            with conn.cursor() as cur:
                cur.executemany(query, rows)
        else:
            conn.executemany(query, rows)


def recent_sends(google_sub, limit=20):
    with _db() as conn:
        return _rows(
            conn,
            "SELECT * FROM sends WHERE google_sub = ? ORDER BY id DESC LIMIT ?",
            (google_sub, limit),
        )


def sent_today(google_sub):
    """Successful sends in the last 24h — the daily cap is enforced on this."""
    since = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(timespec="seconds")
    with _db() as conn:
        row = _one(
            conn,
            "SELECT COUNT(*) AS n FROM sends WHERE google_sub = ? AND success = 1 AND sent_at > ?",
            (google_sub, since),
        )
    return row["n"] if row else 0


def admin_totals():
    """Site-wide counters for the admin panel."""
    since = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(timespec="seconds")
    with _db() as conn:
        return _one(
            conn,
            """
            SELECT
                (SELECT COUNT(*) FROM users)                                        AS users,
                (SELECT COUNT(*) FROM users WHERE plan != 'free')                   AS subscribed,
                (SELECT COUNT(*) FROM sends WHERE success = 1)                      AS sent,
                (SELECT COUNT(*) FROM sends WHERE success = 0)                      AS failed,
                (SELECT COUNT(*) FROM sends WHERE success = 1 AND sent_at > ?)      AS sent_24h
            """,
            (since,),
        )


def admin_list_users():
    """Every user with their send counts, most active first. Admin panel only."""
    since = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(timespec="seconds")
    with _db() as conn:
        return _rows(
            conn,
            """
            SELECT u.google_sub, u.email, u.name, u.role, u.link, u.plan,
                   u.subscribed_at, u.subscription_ends_at, u.created_at,
                   COALESCE(SUM(CASE WHEN s.success = 1 THEN 1 ELSE 0 END), 0) AS sent,
                   COALESCE(SUM(CASE WHEN s.success = 0 THEN 1 ELSE 0 END), 0) AS failed,
                   COALESCE(SUM(CASE WHEN s.success = 1 AND s.sent_at > ? THEN 1 ELSE 0 END), 0) AS sent_24h,
                   MAX(s.sent_at) AS last_sent_at
            FROM users u
            LEFT JOIN sends s ON s.google_sub = u.google_sub
            GROUP BY u.google_sub, u.email, u.name, u.role, u.link, u.plan,
                     u.subscribed_at, u.subscription_ends_at, u.created_at
            ORDER BY sent DESC, u.created_at DESC
            """,
            (since,),
        )


def already_contacted(google_sub, emails):
    """Which of these addresses this user has already successfully mailed."""
    if not emails:
        return set()
    lowered = [e.strip().lower() for e in emails]
    placeholders = ",".join("?" * len(lowered))
    with _db() as conn:
        rows = _rows(
            conn,
            f"""
            SELECT DISTINCT LOWER(to_email) AS e FROM sends
            WHERE google_sub = ? AND success = 1
              AND LOWER(to_email) IN ({placeholders})
            """,
            (google_sub, *lowered),
        )
    return {r["e"] for r in rows}
