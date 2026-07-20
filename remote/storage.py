"""Per-user state: resume link and send history.

Runs on Postgres (set DATABASE_URL - Neon, Supabase, Railway PG) or on SQLite
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

CREATE TABLE IF NOT EXISTS visitors (
    ip           TEXT PRIMARY KEY,
    country      TEXT,
    region       TEXT,
    city         TEXT,
    org          TEXT,
    user_agent   TEXT,
    path         TEXT,
    visit_count  INTEGER NOT NULL DEFAULT 1,
    first_seen   TEXT NOT NULL,
    last_seen    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_visitors_last_seen ON visitors (last_seen);

CREATE TABLE IF NOT EXISTS links (
    google_sub  TEXT NOT NULL,
    name        TEXT NOT NULL,
    url         TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    PRIMARY KEY (google_sub, name)
);
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

CREATE TABLE IF NOT EXISTS visitors (
    ip           TEXT PRIMARY KEY,
    country      TEXT,
    region       TEXT,
    city         TEXT,
    org          TEXT,
    user_agent   TEXT,
    path         TEXT,
    visit_count  INTEGER NOT NULL DEFAULT 1,
    first_seen   TEXT NOT NULL,
    last_seen    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_visitors_last_seen ON visitors (last_seen);

CREATE TABLE IF NOT EXISTS links (
    google_sub  TEXT NOT NULL,
    name        TEXT NOT NULL,
    url         TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    PRIMARY KEY (google_sub, name)
);
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
    ("users", "default_link_name", "TEXT"),
    ("users", "plan", "TEXT NOT NULL DEFAULT 'free'"),
    ("users", "subscribed_at", "TEXT"),
    ("users", "subscription_ends_at", "TEXT"),
    # Link-open tracking: the appended link is served as /r/{track_id}, and
    # opens are counted on the send row itself.
    ("sends", "track_id", "TEXT"),
    ("sends", "tracked_link", "TEXT"),
    ("sends", "link_name", "TEXT"),
    ("sends", "open_count", "INTEGER NOT NULL DEFAULT 0"),
    ("sends", "first_opened_at", "TEXT"),
    ("sends", "last_opened_at", "TEXT"),
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
            
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sends_track ON sends (track_id)")

        _migrate_resume_link(conn)
        _migrate_default_link(conn)


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


def _migrate_default_link(conn):
    existing_users = _columns(conn, "users")
    if "default_link_name" not in existing_users:
        return
    rows = _rows(conn, "SELECT google_sub, link FROM users WHERE link IS NOT NULL AND default_link_name IS NULL")
    for row in rows:
        sub = row["google_sub"]
        url = row["link"]
        now = _now()
        conn.execute(
            _sql(
                """
                INSERT INTO links (google_sub, name, url, created_at, updated_at)
                VALUES (?, 'default', ?, ?, ?)
                ON CONFLICT DO NOTHING
                """
            ),
            (sub, url, now, now)
        )
        conn.execute(
            _sql("UPDATE users SET default_link_name = 'default' WHERE google_sub = ?"),
            (sub,)
        )

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

# --- Saved Links ---

def save_named_link(google_sub, name, url, make_default=False):
    with _db() as conn:
        now = _now()
        conn.execute(
            _sql(
                """
                INSERT INTO links (google_sub, name, url, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (google_sub, name) DO UPDATE SET
                    url = EXCLUDED.url,
                    updated_at = EXCLUDED.updated_at
                """
            ),
            (google_sub, name, url, now, now),
        )
        if make_default:
            conn.execute(
                _sql("UPDATE users SET link = ?, default_link_name = ?, updated_at = ? WHERE google_sub = ?"),
                (url, name, now, google_sub)
            )

def get_named_link(google_sub, name):
    with _db() as conn:
        row = _one(
            conn,
            "SELECT url FROM links WHERE google_sub = ? AND name = ?",
            (google_sub, name),
        )
    return row["url"] if row else None


def list_links(google_sub):
    with _db() as conn:
        user = _one(conn, "SELECT default_link_name FROM users WHERE google_sub = ?", (google_sub,)) or {}
        default = user.get("default_link_name")
        rows = _rows(
            conn,
            "SELECT name, url FROM links WHERE google_sub = ? ORDER BY updated_at DESC",
            (google_sub,),
        )
        return [{"name": r["name"], "url": r["url"], "is_default": r["name"] == default} for r in rows]

def delete_named_link(google_sub, name):
    """Remove a named link and repoint the default if needed."""
    with _db() as conn:
        user = _one(
            conn,
            "SELECT default_link_name FROM users WHERE google_sub = ?",
            (google_sub,),
        ) or {}
        conn.execute(
            _sql("DELETE FROM links WHERE google_sub = ? AND name = ?"),
            (google_sub, name),
        )
        if user.get("default_link_name") != name:
            return

        replacement = _one(
            conn,
            """
            SELECT name, url
              FROM links
             WHERE google_sub = ?
             ORDER BY updated_at DESC, name
             LIMIT 1
            """,
            (google_sub,),
        )
        if replacement:
            conn.execute(
                _sql(
                    """
                    UPDATE users
                       SET link = ?, default_link_name = ?, updated_at = ?
                     WHERE google_sub = ?
                    """
                ),
                (replacement["url"], replacement["name"], _now(), google_sub),
            )
        else:
            conn.execute(
                _sql(
                    """
                    UPDATE users
                       SET link = NULL, default_link_name = NULL, updated_at = ?
                     WHERE google_sub = ?
                    """
                ),
                (_now(), google_sub),
            )

def set_default_link(google_sub, name):
    with _db() as conn:
        row = _one(
            conn,
            "SELECT url FROM links WHERE google_sub = ? AND name = ?",
            (google_sub, name),
        )
        if not row:
            return False
        conn.execute(
            _sql(
                """
                UPDATE users
                   SET link = ?, default_link_name = ?, updated_at = ?
                 WHERE google_sub = ?
                """
            ),
            (row["url"], name, _now(), google_sub),
        )
    return True

# --- Link-open tracking ---

def lookup_tracked(track_id):
    """(url, sent_at) for a tracking id, or (None, None). Counts nothing.

    Separate from count_open so the redirect can always fire while the caller
    decides whether the hit was a human worth counting.
    """
    if not track_id:
        return None, None
    with _db() as conn:
        row = _one(
            conn,
            "SELECT tracked_link, sent_at FROM sends WHERE track_id = ?",
            (track_id,),
        )
    if not row or not row.get("tracked_link"):
        return None, None
    return row["tracked_link"], row.get("sent_at")


def count_open(track_id):
    """Record one genuine open of a tracked link."""
    now = _now()
    with _db() as conn:
        conn.execute(
            _sql(
                """
                UPDATE sends
                   SET open_count = open_count + 1,
                       first_opened_at = COALESCE(first_opened_at, ?),
                       last_opened_at = ?
                 WHERE track_id = ?
                """
            ),
            (now, now, track_id),
        )


def visitor_exists(ip):
    """Whether this IP is already in the table — i.e. logging it grows nothing."""
    with _db() as conn:
        return _one(conn, "SELECT 1 AS x FROM visitors WHERE ip = ?", (ip,)) is not None


def visitor_needs_geo(ip):
    """True when we have no location for this IP yet.

    The geolocation call is keyed on this rather than on 'first visit today',
    so a returning visitor never burns another lookup against ip-api's quota.
    """
    with _db() as conn:
        row = _one(conn, "SELECT country FROM visitors WHERE ip = ?", (ip,))
    return bool(row) and not row.get("country")

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

def lifetime_stats(google_sub):
    """Lifetime aggregates across all sends for the user (dashboard totals)."""
    with _db() as conn:
        row = _one(
            conn,
            """
            SELECT
                SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) AS total_failed,
                SUM(CASE WHEN success = 1 THEN open_count ELSE 0 END) AS total_opens,
                SUM(CASE WHEN success = 1 AND open_count > 0 THEN 1 ELSE 0 END) AS opened_sends
            FROM sends
            WHERE google_sub = ?
            """,
            (google_sub,)
        )
        companies = _one(
            conn,
            """
            SELECT COUNT(DISTINCT company) AS n
            FROM sends
            WHERE google_sub = ? AND success = 1 AND company IS NOT NULL AND TRIM(company) != ''
            """,
            (google_sub,)
        )
    return {
        "total_failed": (row["total_failed"] or 0) if row else 0,
        "total_opens": (row["total_opens"] or 0) if row else 0,
        "opened_sends": (row["opened_sends"] or 0) if row else 0,
        "companies_reached": companies["n"] if companies else 0,
    }

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
            r.get("track_id"),
            r.get("tracked_link"),
            r.get("link_name"),
            _now(),
        )
        for r in results
    ]
    with _db() as conn:
        query = _sql(
            """
            INSERT INTO sends
                (google_sub, to_email, company, subject, source_url,
                 message_id, success, error, track_id, tracked_link, link_name, sent_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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

def link_activity(google_sub, limit=100):
    """Every tracked send with its open data, including the never-opened ones.

    company_open_stats only returns rows that were opened, which hides the most
    actionable case of all: sent days ago, never opened.
    """
    with _db() as conn:
        return _rows(
            conn,
            """
            SELECT id, to_email, company, subject, sent_at,
                   open_count, first_opened_at, last_opened_at
            FROM sends
            WHERE google_sub = ?
              AND success = 1
              AND track_id IS NOT NULL
            ORDER BY id DESC
            LIMIT ?
            """,
            (google_sub, limit),
        )


def company_open_stats(google_sub, limit=100):
    """Company-level open counts across the user's successful sends."""
    with _db() as conn:
        rows = _rows(
            conn,
            """
            SELECT
                company,
                SUM(open_count) AS total_opens,
                SUM(CASE WHEN open_count > 0 THEN 1 ELSE 0 END) AS opened_sends,
                MAX(last_opened_at) AS last_opened_at
            FROM sends
            WHERE google_sub = ?
              AND success = 1
              AND company IS NOT NULL
              AND TRIM(company) != ''
              AND open_count > 0
            GROUP BY company
            ORDER BY total_opens DESC, company ASC
            LIMIT ?
            """,
            (google_sub, limit),
        )
    return rows

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
    """Returns the subset of `emails` the user has already successfully mailed."""
    if not emails:
        return set()
    lowered = [e.lower() for e in emails]
    placeholders = ",".join(["?"] * len(lowered))
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

def touch_visitor(ip, path, user_agent):
    """Log a site visit. Returns True if this is a new visitor today."""
    today = _now()[:10]  # YYYY-MM-DD
    with _db() as conn:
        row = _one(conn, "SELECT last_seen FROM visitors WHERE ip = ?", (ip,))
        is_new = not row or row["last_seen"][:10] != today
        conn.execute(
            _sql(
                """
                INSERT INTO visitors (ip, path, user_agent, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (ip) DO UPDATE SET
                    visit_count = visitors.visit_count + 1,
                    last_seen = EXCLUDED.last_seen,
                    path = EXCLUDED.path
                """
            ),
            (ip, path, user_agent, _now(), _now()),
        )
    return is_new

def set_visitor_geo(ip, country=None, region=None, city=None, org=None):
    with _db() as conn:
        conn.execute(
            _sql(
                """
                UPDATE visitors
                   SET country = ?, region = ?, city = ?, org = ?
                 WHERE ip = ?
                """
            ),
            (country, region, city, org, ip),
        )

def admin_totals():
    """Site-wide aggregates for the admin dashboard overview."""
    with _db() as conn:
        s = _one(
            conn,
            """
            SELECT
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) AS sent,
                SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) AS failed
            FROM sends
            """,
        )
        u = _one(conn, "SELECT COUNT(*) AS n FROM users")
        v = _one(conn, "SELECT COUNT(*) AS n FROM visitors")
    return {
        "users": u["n"] if u else 0,
        "sent": s["sent"] if s else 0,
        "failed": s["failed"] if s else 0,
        "visitors": v["n"] if v else 0,
    }

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

def admin_list_visitors(page=1, per_page=100):
    """Paginated visitor log, most recently active first."""
    offset = (max(1, page) - 1) * per_page
    with _db() as conn:
        total = _one(conn, "SELECT COUNT(*) AS n FROM visitors")
        unique = _one(conn, "SELECT COUNT(DISTINCT ip) AS n FROM visitors")
        hits = _one(conn, "SELECT COALESCE(SUM(visit_count), 0) AS n FROM visitors")
        rows = _rows(
            conn,
            "SELECT * FROM visitors ORDER BY last_seen DESC LIMIT ? OFFSET ?",
            (per_page, offset),
        )
    return {
        "visitors": rows,
        "total": total["n"] if total else 0,
        "unique_ips": unique["n"] if unique else 0,
        "total_hits": hits["n"] if hits else 0,
        "page": page,
        "pages": ((total["n"] if total else 0) + per_page - 1) // per_page,
    }
