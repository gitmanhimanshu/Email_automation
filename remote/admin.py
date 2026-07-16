"""Admin panel API. Plain HTTP + Basic auth, not MCP: the panel is a web page.

Credentials come from ADMIN_EMAIL / ADMIN_PASSWORD env vars; if either is
unset, every route here answers 503 and the panel simply does not exist.

CORS is open on purpose: every route requires credentials in an explicit
Authorization header (never cookies), so the origin adds nothing — and an
open policy means no FRONTEND_ORIGIN to misconfigure per deploy.
"""
import base64
import secrets
from datetime import datetime, timedelta, timezone

from starlette.responses import JSONResponse

from . import config, storage
from .app import mcp

_CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Authorization, Content-Type",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
}


def _gate(request):
    """A JSONResponse to return early, or None when the caller is the admin."""
    if request.method == "OPTIONS":
        return JSONResponse({}, headers=_CORS)

    if not (config.ADMIN_EMAIL and config.ADMIN_PASSWORD):
        return JSONResponse(
            {"error": "admin is not configured on this server"},
            status_code=503,
            headers=_CORS,
        )

    header = request.headers.get("authorization", "")
    if not header.lower().startswith("basic "):
        return JSONResponse({"error": "auth required"}, status_code=401, headers=_CORS)

    try:
        decoded = base64.b64decode(header.split(" ", 1)[1]).decode()
        email, _, password = decoded.partition(":")
    except Exception:
        return JSONResponse({"error": "bad credentials"}, status_code=401, headers=_CORS)

    ok = secrets.compare_digest(
        email.strip().lower(), config.ADMIN_EMAIL
    ) & secrets.compare_digest(password, config.ADMIN_PASSWORD)
    if not ok:
        return JSONResponse({"error": "bad credentials"}, status_code=401, headers=_CORS)

    return None


@mcp.custom_route("/admin/api/overview", methods=["GET", "OPTIONS"])
async def admin_overview(request):
    """Login check + site-wide totals in one call."""
    denied = _gate(request)
    if denied:
        return denied
    return JSONResponse(dict(storage.admin_totals() or {}), headers=_CORS)


@mcp.custom_route("/admin/api/users", methods=["GET", "OPTIONS"])
async def admin_users(request):
    """Every user with plan and send counts."""
    denied = _gate(request)
    if denied:
        return denied
    return JSONResponse({"users": storage.admin_list_users()}, headers=_CORS)


@mcp.custom_route("/admin/api/visitors", methods=["GET", "OPTIONS"])
async def admin_visitors(request):
    """Paginated visitor log, most recently active first."""
    denied = _gate(request)
    if denied:
        return denied

    try:
        page = int(request.query_params.get("page", "1"))
    except ValueError:
        page = 1
    return JSONResponse(dict(storage.admin_list_visitors(page=page)), headers=_CORS)


@mcp.custom_route("/admin/api/plan", methods=["POST", "OPTIONS"])
async def admin_set_plan(request):
    """Change a user's plan. Body: {google_sub, plan: "free"|"pro", months?: int}."""
    denied = _gate(request)
    if denied:
        return denied

    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid JSON body"}, status_code=400, headers=_CORS)

    sub = (payload.get("google_sub") or "").strip()
    plan = (payload.get("plan") or "").strip().lower()
    if not sub or plan not in ("free", "pro"):
        return JSONResponse(
            {"error": "google_sub and plan ('free' or 'pro') are required"},
            status_code=400,
            headers=_CORS,
        )
    if not storage.get_user(sub):
        return JSONResponse({"error": "no such user"}, status_code=404, headers=_CORS)

    if plan == "free":
        storage.set_plan(sub, "free", None, None)
    else:
        months = int(payload.get("months") or 1)
        now = datetime.now(timezone.utc)
        ends = now + timedelta(days=30 * max(1, months))
        storage.set_plan(
            sub,
            "pro",
            now.isoformat(timespec="seconds"),
            ends.isoformat(timespec="seconds"),
        )

    return JSONResponse({"success": True, "user": storage.get_user(sub)}, headers=_CORS)
