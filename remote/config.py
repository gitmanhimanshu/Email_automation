"""Settings for the hosted server, all from environment variables."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# The one Google OAuth app that every user signs into. Unlike the local server,
# users never bring their own client ID here.
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()

# Public HTTPS origin of this server. Must match the redirect URI registered in
# Google Cloud Console, and is what users paste into Claude as the connector URL.
def _base_url():
    explicit = os.getenv("PUBLIC_BASE_URL", "").strip()
    if explicit:
        return explicit.rstrip("/")

    # Railway/Render inject the public domain, so a deploy works before anyone
    # has wired up PUBLIC_BASE_URL by hand.
    for var in ("RAILWAY_PUBLIC_DOMAIN", "RENDER_EXTERNAL_HOSTNAME"):
        domain = os.getenv(var, "").strip()
        if domain:
            return f"https://{domain}".rstrip("/")

    return "http://localhost:8000"


BASE_URL = _base_url()
REDIRECT_PATH = "/auth/callback"

HOST = os.getenv("HOST", "0.0.0.0")
# Hosts assign the port at runtime; never hardcode it in the Dockerfile CMD.
PORT = int(os.getenv("PORT", "8000"))

# /api/stats and /admin/api serve CORS `*`: they authenticate via an explicit
# Authorization header (no cookies), so origin allowlisting adds no security
# and was one more env var to get wrong. No FRONTEND_ORIGIN needed.

# Set DATABASE_URL (Neon, Supabase, Railway PG) and Postgres is used. Leave it
# unset and it falls back to SQLite, so local dev needs no database running.
#
# Postgres is what you want in production: no volume to mount, nothing lost on
# redeploy, and backups you did not have to build.
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "data/app.db"))

# gmail.send is a *sensitive* scope. gmail.readonly/compose/modify are
# *restricted*, which would drag this app into an annual paid CASA security
# assessment. Never widen this list past send.
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/gmail.send",
]

# Per-user guardrails. Gmail's own ceiling for a free account is roughly 500/day;
# staying well under it protects the user's account reputation.
MAX_PER_BATCH = 25
DAILY_SEND_LIMIT = int(os.getenv("DAILY_SEND_LIMIT", "80"))
DEFAULT_DELAY_SECONDS = int(os.getenv("EMAIL_DELAY", "5"))

# Free plan: this many successful sends, lifetime, then a subscription is needed.
FREE_EMAIL_LIMIT = int(os.getenv("FREE_EMAIL_LIMIT", "5"))

# Who's using Setu. The role decides what link rides along with each email and
# what the tools call it — the machinery underneath is identical.
ROLES = {
    "job_seeker": {
        "label": "Job seeker",
        "link_label": "Resume",
        "link_hint": "your resume — a public Google Drive, Dropbox, or personal site URL",
        "link_required": True,
    },
    "recruiter": {
        "label": "Recruiter",
        "link_label": "Job description",
        "link_hint": "the job posting or careers page you're hiring for",
        "link_required": False,
    },
    "professional": {
        "label": "Professional",
        "link_label": "Portfolio",
        "link_hint": "your portfolio, website, or LinkedIn — optional",
        "link_required": False,
    },
}

DEFAULT_ROLE = "job_seeker"

# Admin panel login. Both must be set or every /admin/api route answers 503 —
# there is no default password, so an unconfigured deploy has no admin door.
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "").strip().lower()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

# Off by default: sends go out to whatever address the model supplies.
#
# Set VERIFY_HR_EMAILS=true to require, before every send, that the domain has MX
# records and that the caller cited a real page URL for the address. That blocks
# addresses a model guessed from a naming pattern, which bounce — and bounces are
# what get a Gmail account's sending reputation downgraded. Worth turning on if
# bounce rates start hurting deliverability.
VERIFY_HR_EMAILS = os.getenv("VERIFY_HR_EMAILS", "false").strip().lower() == "true"


def missing_settings():
    missing = []
    if not GOOGLE_CLIENT_ID:
        missing.append("GOOGLE_CLIENT_ID")
    if not GOOGLE_CLIENT_SECRET:
        missing.append("GOOGLE_CLIENT_SECRET")
    if os.getenv("ENV") == "production" and BASE_URL.startswith("http://"):
        # OAuth over plaintext in production would leak tokens, and MCP clients
        # refuse the connector anyway.
        missing.append("PUBLIC_BASE_URL (must be https:// in production)")
    return missing
