"""Public HTTP routes - the parts of the server a plain browser talks to.

Not MCP: the frontend dashboard and uptime monitors cannot speak the protocol.
CORS is open (`*`) on purpose - every authenticated route here takes an
explicit Authorization header and never cookies, so origin adds no security.
"""
import ipaddress
import json
import re
import secrets
import time
from collections import deque
from datetime import datetime, timezone

from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse, Response

from . import config, geo, gmail, storage, verify
from .app import mcp

_LINK_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,31}$")

# Automated fetchers that follow links in email before any human does: mail
# security gateways (SafeLinks, Proofpoint, Mimecast), preview unfurlers, and
# plain scripts. Counting these as "opens" would tell a user their resume was
# read when nobody read it, which is worse than no tracking at all.
_BOT_UA_RE = re.compile(
    r"bot|crawler|spider|slurp|preview|proofpoint|mimecast|barracuda|symantec"
    r"|forcefield|forcepoint|safelinks|urldefense|scanner|monitor|validator"
    r"|curl|wget|python-requests|httpx|go-http|java/|headless|phantom|okhttp",
    re.IGNORECASE,
)

# A gateway usually fetches within seconds of delivery. A real person opening
# that fast is not plausible, so hits inside this window are not counted.
_PREFETCH_GRACE_SECONDS = 20


class _RateWindow:
    """Counts events in a sliding window. Bounds work that costs money or disk.

    In-memory and therefore per-process: on a multi-instance deploy each
    instance gets its own budget. That is fine here — the point is to cap
    runaway growth, not to meter precisely.
    """

    def __init__(self, limit, seconds):
        self.limit = limit
        self.seconds = seconds
        self._hits = deque()

    def allow(self):
        now = time.monotonic()
        cutoff = now - self.seconds
        while self._hits and self._hits[0] < cutoff:
            self._hits.popleft()
        if len(self._hits) >= self.limit:
            return False
        self._hits.append(now)
        return True


# New visitor rows are the only unbounded thing a stranger can create, and each
# one also costs a geolocation call. ip-api's free tier allows ~45/min.
_NEW_VISITOR_LIMIT = _RateWindow(limit=60, seconds=60)
_GEO_LOOKUP_LIMIT = _RateWindow(limit=30, seconds=60)


async def _bearer_identity(request, cors):
    """(identity, None) for a valid Google access token, else (None, response)."""
    header = request.headers.get("authorization", "")
    if not header.lower().startswith("bearer "):
        return None, JSONResponse(
            {"error": "missing bearer token"}, status_code=401, headers=cors
        )

    access_token = header.split(" ", 1)[1].strip()
    try:
        identity = await gmail.fetch_identity(access_token)
    except Exception:
        return None, JSONResponse(
            {"error": "invalid or expired token"}, status_code=401, headers=cors
        )

    if not identity.get("sub"):
        return None, JSONResponse(
            {"error": "could not identify account"}, status_code=401, headers=cors
        )
    return identity, None


def _clean_link_name(name):
    cleaned = (name or "").strip().lower()
    return cleaned if _LINK_NAME_RE.match(cleaned) else None


def _links_payload(sub, user):
    return {
        "default_link_name": user.get("default_link_name"),
        "link": user.get("link"),
        "links": storage.list_links(sub),
    }


def _parse_extra_data(raw):
    if not raw:
        return {}
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return {"raw": str(raw)}


@mcp.custom_route("/health", methods=["GET"])
async def health(request):
    try:
        storage.get_user("health-check-probe")
        db_ok = True
    except Exception:
        db_ok = False

    return JSONResponse(
        {
            "status": "ok" if db_ok else "degraded",
            "database": {"backend": storage.backend(), "ok": db_ok},
            "service": "setu",
        },
        status_code=200 if db_ok else 503,
    )


def _is_prefetch(sent_at):
    """True if this hit landed too soon after the send to be a human."""
    if not sent_at:
        return False
    try:
        sent = datetime.fromisoformat(sent_at)
    except ValueError:
        return False
    if sent.tzinfo is None:
        sent = sent.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - sent).total_seconds() < _PREFETCH_GRACE_SECONDS


def render_expired_link_page(
    title="Link Expired or Unavailable",
    message="This tracking link has expired or is no longer active.",
    subtext="Please check your original email for the candidate's attached resume, or reply directly to their email to request an updated copy.",
    status_code=404,
):
    home_url = config.DASHBOARD_URL.replace("/dashboard", "")
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} — Setu</title>
  <style>
    :root {{
      --plane: #f8fafc;
      --surface: #ffffff;
      --surface-2: #f1f5f9;
      --text-primary: #0f172a;
      --text-secondary: #475569;
      --text-muted: #94a3b8;
      --border: rgba(15, 23, 42, 0.08);
      --border-strong: rgba(15, 23, 42, 0.16);
      --accent: #2563eb;
      --accent-hover: #1d4ed8;
      --accent-glow: rgba(37, 99, 235, 0.12);
      --warning: #d97706;
      --warning-bg: rgba(245, 158, 11, 0.08);
      --warning-border: rgba(245, 158, 11, 0.25);
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{
        --plane: #090d16;
        --surface: #111827;
        --surface-2: #1e293b;
        --text-primary: #f8fafc;
        --text-secondary: #cbd5e1;
        --text-muted: #64748b;
        --border: rgba(255, 255, 255, 0.1);
        --border-strong: rgba(255, 255, 255, 0.18);
        --accent: #3b82f6;
        --accent-hover: #60a5fa;
        --accent-glow: rgba(59, 130, 246, 0.2);
        --warning: #fbbf24;
        --warning-bg: rgba(251, 191, 36, 0.1);
        --warning-border: rgba(251, 191, 36, 0.25);
      }}
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: var(--plane);
      color: var(--text-primary);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 1.5rem;
      line-height: 1.5;
    }}
    .container {{
      max-width: 520px;
      width: 100%;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 20px;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.03);
      padding: 2.5rem 2rem;
      text-align: center;
    }}
    .brand {{
      display: inline-flex;
      align-items: center;
      gap: 0.65rem;
      text-decoration: none;
      color: var(--text-primary);
      font-weight: 700;
      font-size: 1.2rem;
      margin-bottom: 1.75rem;
      letter-spacing: -0.02em;
    }}
    .logo-badge {{
      width: 44px;
      height: 44px;
      border-radius: 12px;
      background: var(--accent-glow);
      display: grid;
      place-items: center;
      border: 1px solid var(--border-strong);
    }}
    .tagline {{
      font-size: 0.75rem;
      color: var(--text-muted);
      font-weight: 500;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }}
    .status-badge {{
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      background: var(--warning-bg);
      border: 1px solid var(--warning-border);
      color: var(--warning);
      font-size: 0.8rem;
      font-weight: 600;
      padding: 0.35rem 0.8rem;
      border-radius: 9999px;
      margin-bottom: 1.25rem;
    }}
    h1 {{
      font-size: 1.55rem;
      font-weight: 700;
      letter-spacing: -0.025em;
      margin-bottom: 0.75rem;
      color: var(--text-primary);
    }}
    .message {{
      color: var(--text-secondary);
      font-size: 0.95rem;
      margin-bottom: 1.5rem;
    }}
    .notice-card {{
      background: var(--surface-2);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.25rem;
      text-align: left;
      font-size: 0.88rem;
      color: var(--text-secondary);
      margin-bottom: 1.75rem;
      line-height: 1.6;
    }}
    .notice-card strong {{
      color: var(--text-primary);
      display: block;
      margin-bottom: 0.4rem;
      font-size: 0.92rem;
    }}
    .btn {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      width: 100%;
      background: var(--accent);
      color: #ffffff;
      font-weight: 600;
      font-size: 0.92rem;
      padding: 0.85rem 1.25rem;
      border-radius: 12px;
      text-decoration: none;
      transition: background 0.15s ease;
    }}
    .btn:hover {{
      background: var(--accent-hover);
    }}
    .footer {{
      margin-top: 1.75rem;
      font-size: 0.8rem;
      color: var(--text-muted);
    }}
    .footer a {{
      color: var(--text-secondary);
      text-decoration: none;
      font-weight: 500;
    }}
    .footer a:hover {{
      text-decoration: underline;
    }}
  </style>
</head>
<body>
  <div class="container">
    <a href="{home_url}" class="brand">
      <div class="logo-badge">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--accent);">
          <path d="M4 19c4-6 12-6 16 0"/>
          <path d="M6 15l2-3"/>
          <path d="M16 12l2 3"/>
          <circle cx="12" cy="7" r="3"/>
        </svg>
      </div>
      <div style="text-align: left;">
        <div>Setu <span style="font-size: 0.9rem; font-weight: 500; color: var(--text-muted);">(सेतु)</span></div>
        <div class="tagline">Bridge AI to Opportunity</div>
      </div>
    </a>

    <div>
      <span class="status-badge">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        Link Expired / समाप्त लिंक
      </span>
    </div>

    <h1>{title}</h1>
    <p class="message">{message}</p>

    <div class="notice-card">
      <strong>Next Steps / आगे क्या करें:</strong>
      <p>{subtext}</p>
      <p style="margin-top: 0.75rem; border-top: 1px solid var(--border); padding-top: 0.75rem; font-size: 0.82rem; color: var(--text-muted);">
        All emails sent via Setu come directly from the sender's own Gmail. When you click <em>Reply</em> in your email client, your message reaches their personal inbox directly.
      </p>
    </div>

    <a href="{home_url}" class="btn">
      Visit Setu Platform
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="5" y1="12" x2="19" y2="12"/>
        <polyline points="12 5 19 12 12 19"/>
      </svg>
    </a>

    <p class="footer">
      Delivered by <a href="{home_url}">Setu</a> · Verified direct Gmail sending
    </p>
  </div>
</body>
</html>"""
    return HTMLResponse(content=html, status_code=status_code)


@mcp.custom_route("/r/{track_id}", methods=["GET"])
async def tracked_link(request):
    track_id = request.path_params.get("track_id")
    url, sent_at = storage.lookup_tracked(track_id)
    if not url:
        return render_expired_link_page(
            title="Link Expired or Unavailable",
            message="This tracking link has expired or is no longer active.",
            subtext="Please check your original email for the candidate's attached resume, or reply directly to their email to request an updated copy.",
            status_code=404,
        )

    # Defence in depth: saving a link already requires http(s), but this route
    # emits a redirect to whatever is stored, so never let it emit a scheme a
    # browser would execute (javascript:, data:).
    if not url.lower().startswith(("http://", "https://")):
        return render_expired_link_page(
            title="Unsupported Link Format",
            message="This link does not point to a supported web URL.",
            subtext="Please check your original email for the resume or reply directly to the sender.",
            status_code=400,
        )

    user_agent = request.headers.get("user-agent", "")
    if not _BOT_UA_RE.search(user_agent) and not _is_prefetch(sent_at):
        try:
            storage.count_open(track_id)
        except Exception:
            pass  # a counting failure must never break the recipient's click

    # Redirect regardless of whether the hit counted — the link always works.
    return RedirectResponse(url=url, status_code=307)


@mcp.custom_route("/f/{file_id}", methods=["GET"])
async def serve_file(request):
    """Serve an uploaded file to whoever has the link — the recipient is not
    signed in, so the unguessable id is the only credential."""
    found = storage.read_file(request.path_params.get("file_id", ""))
    if not found:
        return render_expired_link_page(
            title="File Expired or Not Found",
            message="This uploaded document is no longer available.",
            subtext="Please check the original email for the attached resume or contact the sender directly.",
            status_code=404,
        )

    data, filename, content_type = found

    # Never echo a stored content type back: a stored text/html would run as
    # script on our own origin. Only the allow-list is ever emitted, and
    # anything unexpected downgrades to a plain download.
    safe_type = content_type if content_type in config.ALLOWED_FILE_TYPES else "application/octet-stream"

    return Response(
        content=data,
        media_type=safe_type,
        headers={
            # inline so a PDF opens in the browser instead of forcing a download
            "Content-Disposition": f'inline; filename="{_safe_filename(filename)}"',
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, max-age=300",
        },
    )


def _safe_filename(name):
    """A filename safe to put in a header — no quotes, newlines, or paths."""
    cleaned = re.sub(r'[^A-Za-z0-9._ -]', "_", (name or "file").strip())[:80]
    return cleaned or "file"


@mcp.custom_route("/api/files", methods=["GET", "POST", "OPTIONS"])
async def api_files(request):
    """List or upload this user's files. Bearer auth, same as /api/stats."""
    cors = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Authorization, Content-Type",
        "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
    }
    if request.method == "OPTIONS":
        return JSONResponse({}, headers=cors)

    identity, denied = await _bearer_identity(request, cors)
    if denied:
        return denied
    sub = identity["sub"]
    storage.upsert_user(sub, identity["email"], identity.get("name"))

    if request.method == "GET":
        return JSONResponse(
            {
                "files": storage.list_files(sub),
                "storage_used": storage.user_storage_used(sub),
                "storage_limit": config.MAX_STORAGE_PER_USER,
                "max_files": config.MAX_FILES_PER_USER,
                "max_file_bytes": config.MAX_FILE_BYTES,
            },
            headers=cors,
        )

    existing = storage.list_files(sub)
    if len(existing) >= config.MAX_FILES_PER_USER:
        return JSONResponse(
            {"error": f"You can keep {config.MAX_FILES_PER_USER} files. Delete one first."},
            status_code=400,
            headers=cors,
        )

    try:
        form = await request.form()
        upload = form["file"]
        data = await upload.read()
    except Exception:
        return JSONResponse(
            {"error": "Send the file as multipart form data under the field 'file'."},
            status_code=400,
            headers=cors,
        )

    if not data:
        return JSONResponse({"error": "The file is empty."}, status_code=400, headers=cors)

    if len(data) > config.MAX_FILE_BYTES:
        mb = config.MAX_FILE_BYTES / (1024 * 1024)
        return JSONResponse(
            {"error": f"That file is larger than the {mb:.0f} MB limit."},
            status_code=400,
            headers=cors,
        )

    if storage.user_storage_used(sub) + len(data) > config.MAX_STORAGE_PER_USER:
        return JSONResponse(
            {"error": "That would exceed your storage limit. Delete a file first."},
            status_code=400,
            headers=cors,
        )

    content_type = (getattr(upload, "content_type", "") or "").split(";")[0].strip()
    if content_type not in config.ALLOWED_FILE_TYPES:
        return JSONResponse(
            {"error": "Only PDF and Word documents can be uploaded."},
            status_code=400,
            headers=cors,
        )

    # A PDF that isn't a PDF is either a mistake or someone probing; the magic
    # bytes are a cheap check that the content matches what it claims.
    if content_type == "application/pdf" and not data.startswith(b"%PDF"):
        return JSONResponse(
            {"error": "That file says it is a PDF but does not look like one."},
            status_code=400,
            headers=cors,
        )

    file_id = secrets.token_urlsafe(12)
    filename = _safe_filename(getattr(upload, "filename", "") or "resume")
    storage.save_file(file_id, sub, filename, content_type, data)

    return JSONResponse(
        {
            "success": True,
            "id": file_id,
            "filename": filename,
            "size": len(data),
            "url": f"{config.BASE_URL}/f/{file_id}",
        },
        headers=cors,
    )


@mcp.custom_route("/api/files/{file_id}", methods=["DELETE", "OPTIONS"])
async def api_delete_file(request):
    cors = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Authorization, Content-Type",
        "Access-Control-Allow-Methods": "DELETE, OPTIONS",
    }
    if request.method == "OPTIONS":
        return JSONResponse({}, headers=cors)

    identity, denied = await _bearer_identity(request, cors)
    if denied:
        return denied

    removed = storage.delete_file(identity["sub"], request.path_params.get("file_id", ""))
    if not removed:
        return JSONResponse({"error": "no such file"}, status_code=404, headers=cors)
    return JSONResponse({"success": True}, headers=cors)


def _client_ip(request):
    """The visitor's IP, or "" if it isn't a usable public address.

    X-Forwarded-For is attacker-controlled: anyone can post any value. Parsing
    it strictly means a spoofed header can at worst impersonate some other real
    IP, never inject arbitrary text as a primary key.
    """
    candidate = ""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        candidate = forwarded.split(",")[0].strip()
    if not candidate:
        candidate = request.headers.get("x-real-ip", "").strip()
    if not candidate and request.client:
        candidate = request.client.host

    try:
        ipaddress.ip_address(candidate)
    except ValueError:
        return ""
    return candidate


@mcp.custom_route("/api/visit", methods=["POST", "OPTIONS"])
async def api_visit(request):
    cors = {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "Content-Type"}
    if request.method == "OPTIONS":
        return JSONResponse({}, headers=cors)

    ip = _client_ip(request)
    if not ip:
        return JSONResponse({"ok": True}, headers=cors)

    try:
        body = await request.json()
    except Exception:
        body = {}
    path = (body.get("path") or "/")[:400]
    played_video = bool(body.get("played_video"))
    user_agent = request.headers.get("user-agent", "")[:400]

    try:
        known = storage.visitor_exists(ip)

        # Only a brand-new IP grows the table, so that is the one path a
        # stranger could abuse. Past the cap we stop creating rows rather than
        # let anyone fill the database (and burn the geolocation quota) at will.
        if not known and not _NEW_VISITOR_LIMIT.allow():
            return JSONResponse({"ok": True}, headers=cors)

        storage.touch_visitor(ip, path, user_agent, played_video=played_video)

        # Keyed on "we have no location for this IP", not "first visit today" —
        # otherwise every returning visitor costs another lookup every day.
        if storage.visitor_needs_geo(ip) and _GEO_LOOKUP_LIMIT.allow():
            located = await geo.locate(ip)
            if located:
                storage.set_visitor_geo(ip, **located)
    except Exception:
        pass

    return JSONResponse({"ok": True}, headers=cors)


@mcp.custom_route("/api/link", methods=["GET", "POST", "DELETE", "OPTIONS"])
async def api_link(request):
    """List, save, default, or delete saved links from the dashboard."""
    cors = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Authorization, Content-Type",
        "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
    }

    if request.method == "OPTIONS":
        return JSONResponse({}, headers=cors)

    identity, denied = await _bearer_identity(request, cors)
    if denied:
        return denied

    sub = identity["sub"]
    storage.upsert_user(sub, identity["email"], identity.get("name"))

    if request.method == "GET":
        user = storage.get_user(sub) or {}
        return JSONResponse(_links_payload(sub, user), headers=cors)

    try:
        payload = await request.json()
    except Exception:
        payload = {}

    if request.method == "DELETE":
        name = _clean_link_name(payload.get("name"))
        if not name:
            return JSONResponse({"error": "name is required"}, status_code=400, headers=cors)
        if not storage.get_named_link(sub, name):
            return JSONResponse({"error": f"no saved link named {name!r}"}, status_code=404, headers=cors)
        storage.delete_named_link(sub, name)
        user = storage.get_user(sub) or {}
        return JSONResponse({"success": True, **_links_payload(sub, user)}, headers=cors)

    url = (payload.get("link") or "").strip()
    name = _clean_link_name(payload.get("name") or "default")
    make_default = bool(payload.get("make_default")) or name == "default"

    if not url:
        return JSONResponse({"error": "link is required"}, status_code=400, headers=cors)
    if not name:
        return JSONResponse({"error": "name is required"}, status_code=400, headers=cors)

    ok, detail = await verify.check_resume_link(url)
    if not ok:
        return JSONResponse({"success": False, "error": detail}, status_code=422, headers=cors)

    storage.save_named_link(sub, name, url, make_default=make_default)
    user = storage.get_user(sub) or {}
    return JSONResponse(
        {"success": True, "detail": detail, **_links_payload(sub, user)},
        headers=cors,
    )


@mcp.custom_route("/api/link/default", methods=["POST", "OPTIONS"])
async def api_link_default(request):
    cors = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Authorization, Content-Type",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
    }

    if request.method == "OPTIONS":
        return JSONResponse({}, headers=cors)

    identity, denied = await _bearer_identity(request, cors)
    if denied:
        return denied

    try:
        payload = await request.json()
    except Exception:
        payload = {}

    name = _clean_link_name(payload.get("name"))
    if not name:
        return JSONResponse({"error": "name is required"}, status_code=400, headers=cors)

    if not storage.set_default_link(identity["sub"], name):
        return JSONResponse({"error": f"no saved link named {name!r}"}, status_code=404, headers=cors)

    user = storage.get_user(identity["sub"]) or {}
    return JSONResponse({"success": True, **_links_payload(identity["sub"], user)}, headers=cors)


@mcp.custom_route("/api/profile/metadata", methods=["GET", "POST", "PATCH", "OPTIONS"])
@mcp.custom_route("/api/user/metadata", methods=["GET", "POST", "PATCH", "OPTIONS"])
async def api_profile_metadata(request):
    cors = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Authorization, Content-Type",
        "Access-Control-Allow-Methods": "GET, POST, PATCH, OPTIONS",
    }
    if request.method == "OPTIONS":
        return JSONResponse({}, headers=cors)

    identity, denied = await _bearer_identity(request, cors)
    if denied:
        return denied

    sub = identity["sub"]
    storage.upsert_user(sub, identity["email"], identity.get("name"))

    if request.method == "GET":
        metadata = storage.get_user_metadata(sub)
        return JSONResponse({"success": True, "metadata": metadata}, headers=cors)

    try:
        payload = await request.json()
    except Exception:
        payload = {}

    if not isinstance(payload, dict):
        return JSONResponse(
            {"success": False, "error": "Request body must be a JSON object of key-value pairs"},
            status_code=400,
            headers=cors,
        )

    updated = storage.set_user_metadata(sub, payload, merge=True)
    return JSONResponse(
        {
            "success": True,
            "message": f"Updated {len(payload)} profile field(s)",
            "metadata": updated,
        },
        headers=cors,
    )


@mcp.custom_route("/api/stats", methods=["GET", "OPTIONS"])
async def api_stats(request):
    cors = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Authorization",
    }

    if request.method == "OPTIONS":
        return JSONResponse({}, headers=cors)

    identity, denied = await _bearer_identity(request, cors)
    if denied:
        return denied

    sub = identity["sub"]
    storage.upsert_user(sub, identity["email"], identity.get("name"))
    user = storage.get_user(sub) or {}
    role = user.get("role") if user.get("role") in config.ROLES else None
    plan = user.get("plan", "free")
    is_free = (plan == "free")
    lifetime = storage.total_sent(sub)
    stats = storage.lifetime_stats(sub)
    used_today = storage.sent_today(sub)

    try:
        sends_page = max(1, int(request.query_params.get("sends_page", request.query_params.get("page", 1))))
    except (ValueError, TypeError):
        sends_page = 1
    try:
        sends_limit = max(1, min(100, int(request.query_params.get("sends_limit", request.query_params.get("limit", 20)))))
    except (ValueError, TypeError):
        sends_limit = 20

    try:
        company_page = max(1, int(request.query_params.get("company_page", 1)))
    except (ValueError, TypeError):
        company_page = 1
    try:
        company_limit = max(1, min(100, int(request.query_params.get("company_limit", 20))))
    except (ValueError, TypeError):
        company_limit = 20

    sends_offset = (sends_page - 1) * sends_limit
    company_offset = (company_page - 1) * company_limit

    company_sort = request.query_params.get("company_sort", "latest")
    sends_sort = request.query_params.get("sends_sort", "recent")

    total_sends = storage.total_sends_count(sub)
    history = storage.recent_sends(sub, limit=sends_limit, offset=sends_offset, sort=sends_sort)

    total_companies_opened = storage.total_company_opens_count(sub)
    company_opens = storage.company_open_stats(sub, limit=company_limit, offset=company_offset, sort=company_sort)

    return JSONResponse(
        {
            "email": identity["email"],
            "name": identity.get("name"),
            "role": role,
            "role_label": config.ROLES.get(role, {}).get("label"),
            "link": user.get("link"),
            "default_link_name": user.get("default_link_name"),
            "links": storage.list_links(sub),
            "link_label": config.ROLES.get(role, {}).get("link_label"),
            "metadata": user.get("metadata") or {},
            "linkedin_url": user.get("linkedin_url"),
            "github_url": user.get("github_url"),
            "reason_for_job_change": user.get("reason_for_job_change"),
            "extra_data": _parse_extra_data(user.get("extra_data")),
            "plan": plan,
            "subscribed_at": user.get("subscribed_at"),
            "subscription_ends_at": user.get("subscription_ends_at"),
            "free_email_limit": config.FREE_DAILY_SEND_LIMIT if is_free else None,
            "free_remaining": max(0, config.FREE_DAILY_SEND_LIMIT - used_today) if is_free else None,
            "total_sent": lifetime,
            "total_failed": stats["total_failed"],
            "total_opens": stats["total_opens"],
            "opened_sends": stats["opened_sends"],
            "sent_last_24h": used_today,
            "daily_limit": config.FREE_DAILY_SEND_LIMIT if is_free else None,
            "companies": stats["companies_reached"],
            "company_opens": company_opens,
            "company_opens_total": total_companies_opened,
            "company_opens_page": company_page,
            "company_opens_limit": company_limit,
            "company_opens_total_pages": max(1, (total_companies_opened + company_limit - 1) // company_limit),
            "recent": [
                {
                    "to_email": r["to_email"],
                    "company": r["company"],
                    "subject": r["subject"],
                    "success": bool(r["success"]),
                    "error": r["error"],
                    "sent_at": r["sent_at"],
                    "open_count": r.get("open_count") or 0,
                    "first_opened_at": r.get("first_opened_at"),
                    "last_opened_at": r.get("last_opened_at"),
                    "link_name": r.get("link_name"),
                }
                for r in history
            ],
            "recent_total": total_sends,
            "recent_page": sends_page,
            "recent_limit": sends_limit,
            "recent_total_pages": max(1, (total_sends + sends_limit - 1) // sends_limit),
        },
        headers=cors,
    )


@mcp.custom_route("/api/sends", methods=["GET", "OPTIONS"])
async def api_sends(request):
    cors = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Authorization",
    }
    if request.method == "OPTIONS":
        return JSONResponse({}, headers=cors)

    identity, denied = await _bearer_identity(request, cors)
    if denied:
        return denied

    sub = identity["sub"]
    try:
        page = max(1, int(request.query_params.get("page", 1)))
    except (ValueError, TypeError):
        page = 1
    try:
        limit = max(1, min(100, int(request.query_params.get("limit", 20))))
    except (ValueError, TypeError):
        limit = 20

    sort = request.query_params.get("sort", "recent")

    offset = (page - 1) * limit
    total = storage.total_sends_count(sub)
    history = storage.recent_sends(sub, limit=limit, offset=offset, sort=sort)

    items = [
        {
            "to_email": r["to_email"],
            "company": r["company"],
            "subject": r["subject"],
            "success": bool(r["success"]),
            "error": r["error"],
            "sent_at": r["sent_at"],
            "open_count": r.get("open_count") or 0,
            "first_opened_at": r.get("first_opened_at"),
            "last_opened_at": r.get("last_opened_at"),
            "link_name": r.get("link_name"),
        }
        for r in history
    ]

    return JSONResponse(
        {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": max(1, (total + limit - 1) // limit),
        },
        headers=cors,
    )


@mcp.custom_route("/api/company_opens", methods=["GET", "OPTIONS"])
@mcp.custom_route("/api/company-opens", methods=["GET", "OPTIONS"])
async def api_company_opens(request):
    cors = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Authorization",
    }
    if request.method == "OPTIONS":
        return JSONResponse({}, headers=cors)

    identity, denied = await _bearer_identity(request, cors)
    if denied:
        return denied

    sub = identity["sub"]
    try:
        page = max(1, int(request.query_params.get("page", 1)))
    except (ValueError, TypeError):
        page = 1
    try:
        limit = max(1, min(100, int(request.query_params.get("limit", 20))))
    except (ValueError, TypeError):
        limit = 20

    sort = request.query_params.get("sort", "latest")

    offset = (page - 1) * limit
    total = storage.total_company_opens_count(sub)
    rows = storage.company_open_stats(sub, limit=limit, offset=offset, sort=sort)

    return JSONResponse(
        {
            "items": rows,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": max(1, (total + limit - 1) // limit),
        },
        headers=cors,
    )


@mcp.custom_route("/api/profile", methods=["GET", "POST", "OPTIONS"])
async def api_profile(request):
    """Get or update profile fields: linkedin_url, github_url, reason_for_job_change, extra_data."""
    cors = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Authorization, Content-Type",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    }

    if request.method == "OPTIONS":
        return JSONResponse({}, headers=cors)

    identity, denied = await _bearer_identity(request, cors)
    if denied:
        return denied

    sub = identity["sub"]
    storage.upsert_user(sub, identity["email"], identity.get("name"))

    if request.method == "GET":
        user = storage.get_user(sub) or {}
        return JSONResponse(
            {
                "linkedin_url": user.get("linkedin_url"),
                "github_url": user.get("github_url"),
                "reason_for_job_change": user.get("reason_for_job_change"),
                "extra_data": _parse_extra_data(user.get("extra_data")),
                "role": user.get("role"),
                "name": user.get("name"),
                "email": user.get("email"),
            },
            headers=cors,
        )

    try:
        payload = await request.json()
    except Exception:
        payload = {}

    to_update = {}
    if "linkedin_url" in payload:
        url = (payload.get("linkedin_url") or "").strip()
        if url and not url.lower().startswith(("http://", "https://")):
            return JSONResponse(
                {"error": "LinkedIn URL must start with http:// or https://"},
                status_code=400,
                headers=cors,
            )
        to_update["linkedin_url"] = url or None

    if "github_url" in payload:
        url = (payload.get("github_url") or "").strip()
        if url and not url.lower().startswith(("http://", "https://")):
            return JSONResponse(
                {"error": "GitHub URL must start with http:// or https://"},
                status_code=400,
                headers=cors,
            )
        to_update["github_url"] = url or None

    if "reason_for_job_change" in payload:
        reason = (payload.get("reason_for_job_change") or "").strip()
        to_update["reason_for_job_change"] = reason or None

    if "extra_data" in payload:
        extra = payload.get("extra_data")
        to_update["extra_data"] = extra

    if to_update:
        storage.update_user_profile(sub, **to_update)

    user = storage.get_user(sub) or {}
    return JSONResponse(
        {
            "success": True,
            "linkedin_url": user.get("linkedin_url"),
            "github_url": user.get("github_url"),
            "reason_for_job_change": user.get("reason_for_job_change"),
            "extra_data": _parse_extra_data(user.get("extra_data")),
        },
        headers=cors,
    )
