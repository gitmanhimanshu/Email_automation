"""Public HTTP routes - the parts of the server a plain browser talks to.

Not MCP: the frontend dashboard and uptime monitors cannot speak the protocol.
CORS is open (`*`) on purpose - every authenticated route here takes an
explicit Authorization header and never cookies, so origin adds no security.
"""
import ipaddress
import re
import secrets
import time
from collections import deque
from datetime import datetime, timezone

from starlette.responses import JSONResponse, RedirectResponse, Response

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


@mcp.custom_route("/r/{track_id}", methods=["GET"])
async def tracked_link(request):
    track_id = request.path_params.get("track_id")
    url, sent_at = storage.lookup_tracked(track_id)
    if not url:
        return JSONResponse({"error": "unknown tracking id"}, status_code=404)

    # Defence in depth: saving a link already requires http(s), but this route
    # emits a redirect to whatever is stored, so never let it emit a scheme a
    # browser would execute (javascript:, data:).
    if not url.lower().startswith(("http://", "https://")):
        return JSONResponse({"error": "unsupported link"}, status_code=400)

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
        return JSONResponse({"error": "file not found"}, status_code=404)

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
    user_agent = request.headers.get("user-agent", "")[:400]

    try:
        known = storage.visitor_exists(ip)

        # Only a brand-new IP grows the table, so that is the one path a
        # stranger could abuse. Past the cap we stop creating rows rather than
        # let anyone fill the database (and burn the geolocation quota) at will.
        if not known and not _NEW_VISITOR_LIMIT.allow():
            return JSONResponse({"ok": True}, headers=cors)

        storage.touch_visitor(ip, path, user_agent)

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
    history = storage.recent_sends(sub, limit=200)
    role = user.get("role") if user.get("role") in config.ROLES else None
    plan = user.get("plan", "free")
    lifetime = storage.total_sent(sub)
    stats = storage.lifetime_stats(sub)

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
            "plan": plan,
            "subscribed_at": user.get("subscribed_at"),
            "subscription_ends_at": user.get("subscription_ends_at"),
            "free_email_limit": config.FREE_EMAIL_LIMIT,
            "free_remaining": max(0, config.FREE_EMAIL_LIMIT - lifetime) if plan == "free" else None,
            "total_sent": lifetime,
            "total_failed": stats["total_failed"],
            "total_opens": stats["total_opens"],
            "opened_sends": stats["opened_sends"],
            "sent_last_24h": storage.sent_today(sub),
            "daily_limit": config.DAILY_SEND_LIMIT,
            "companies": stats["companies_reached"],
            "company_opens": storage.company_open_stats(sub),
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
                for r in history[:25]
            ],
        },
        headers=cors,
    )
