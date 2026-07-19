"""Public HTTP routes - the parts of the server a plain browser talks to.

Not MCP: the frontend dashboard and uptime monitors cannot speak the protocol.
CORS is open (`*`) on purpose - every authenticated route here takes an
explicit Authorization header and never cookies, so origin adds no security.
"""
import re

from starlette.responses import JSONResponse, RedirectResponse

from . import config, geo, gmail, storage, verify
from .app import mcp

_LINK_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,31}$")


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


@mcp.custom_route("/r/{track_id}", methods=["GET"])
async def tracked_link(request):
    url = storage.record_open(request.path_params.get("track_id"))
    if not url:
        return JSONResponse({"error": "unknown tracking id"}, status_code=404)
    return RedirectResponse(url=url, status_code=307)


def _client_ip(request):
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real = request.headers.get("x-real-ip", "").strip()
    if real:
        return real
    return request.client.host if request.client else ""


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
        is_new = storage.touch_visitor(ip, path, user_agent)
        if is_new:
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
