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
    resume_link  TEXT,
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
    resume_link  TEXT,
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


def init():
    with _db() as conn:
        schema = SCHEMA_POSTGRES if using_postgres() else SCHEMA_SQLITE
        if using_postgres():
            # psycopg has no executescript; it accepts multiple statements
            # in one execute() instead.
            conn.execute(schema)
        else:
            conn.executescript(schema)


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


def set_resume_link(google_sub, resume_link):
    with _db() as conn:
        conn.execute(
            _sql("UPDATE users SET resume_link = ?, updated_at = ? WHERE google_sub = ?"),
            (resume_link, _now(), google_sub),
        )


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
