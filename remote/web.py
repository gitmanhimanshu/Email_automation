"""Public HTTP routes — the parts of the server a plain browser talks to.

Not MCP: the frontend dashboard and uptime monitors cannot speak the protocol.
CORS is open (`*`) on purpose — every authenticated route here takes an
explicit Authorization header and never cookies, so origin adds no security.
"""
from starlette.responses import JSONResponse

from . import config, geo, gmail, storage, verify
from .app import mcp


async def _bearer_identity(request, cors):
    """(identity, None) for a valid Google access token, else (None, response).

    Same auth the MCP flow uses: the token itself names the user, resolved
    server-side, so a caller can only ever touch their own row.
    """
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


@mcp.custom_route("/health", methods=["GET"])
async def health(request):
    """Liveness + readiness, no auth. Render/Railway health checks and uptime
    monitors hit this; it answers 200 only when the database is reachable."""
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


def _client_ip(request):
    """The visitor's IP, honouring the proxy chain Render/Railway put in front.

    X-Forwarded-For is 'client, proxy1, proxy2'; the first hop is the real
    client. Falls back to the socket address for a direct connection.
    """
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real = request.headers.get("x-real-ip", "").strip()
    if real:
        return real
    return request.client.host if request.client else ""


@mcp.custom_route("/api/visit", methods=["POST", "OPTIONS"])
async def api_visit(request):
    """Log a page view. Public, unauthenticated, and never fails the visitor.

    Dedupes by IP: a returning visitor bumps a counter rather than adding a row,
    and only a brand-new IP triggers a geolocation lookup.
    """
    cors = {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "Content-Type"}
    if request.method == "OPTIONS":
        return JSONResponse({}, headers=cors)

    ip = _client_ip(request)
    if not ip:
        return JSONResponse({"ok": True}, headers=cors)  # nothing to record; don't complain

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
        # Analytics must never take the site down. Swallow and move on.
        pass

    return JSONResponse({"ok": True}, headers=cors)


@mcp.custom_route("/api/link", methods=["POST", "OPTIONS"])
async def api_link(request):
    """Save or change the user's resume/portfolio link from the dashboard.

    Same validation as the save_link MCP tool: the URL is fetched first, and a
    link the recipient couldn't open (private Drive file, login wall, 404) is
    rejected here instead of silently failing in someone's inbox.
    """
    cors = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Authorization, Content-Type",
    }

    if request.method == "OPTIONS":
        return JSONResponse({}, headers=cors)

    identity, denied = await _bearer_identity(request, cors)
    if denied:
        return denied

    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid JSON body"}, status_code=400, headers=cors)

    url = (payload.get("link") or "").strip()
    if not url:
        return JSONResponse({"error": "link is required"}, status_code=400, headers=cors)

    ok, detail = await verify.check_resume_link(url)
    if not ok:
        return JSONResponse({"success": False, "error": detail}, status_code=422, headers=cors)

    sub = identity["sub"]
    storage.upsert_user(sub, identity["email"], identity.get("name"))
    storage.set_link(sub, url)
    return JSONResponse({"success": True, "link": url, "detail": detail}, headers=cors)


@mcp.custom_route("/api/stats", methods=["GET", "OPTIONS"])
async def api_stats(request):
    """Read-only stats for the web dashboard.

    Auth is the same Google access token the MCP flow issues, resolved to an
    identity server-side, so a caller can only ever see their own rows.
    """
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

    return JSONResponse(
        {
            "email": identity["email"],
            "name": identity.get("name"),
            "role": role,
            "role_label": config.ROLES.get(role, {}).get("label"),
            "link": user.get("link"),
            "link_label": config.ROLES.get(role, {}).get("link_label"),
            "plan": plan,
            "subscribed_at": user.get("subscribed_at"),
            "subscription_ends_at": user.get("subscription_ends_at"),
            "free_email_limit": config.FREE_EMAIL_LIMIT,
            "free_remaining": max(0, config.FREE_EMAIL_LIMIT - lifetime) if plan == "free" else None,
            "total_sent": lifetime,
            "total_failed": sum(1 for r in history if not r["success"]),
            "sent_last_24h": storage.sent_today(sub),
            "daily_limit": config.DAILY_SEND_LIMIT,
            "companies": len({r["company"] for r in history if r["company"] and r["success"]}),
            "recent": [
                {
                    "to_email": r["to_email"],
                    "company": r["company"],
                    "subject": r["subject"],
                    "success": bool(r["success"]),
                    "error": r["error"],
                    "sent_at": r["sent_at"],
                }
                for r in history[:25]
            ],
        },
        headers=cors,
    )
