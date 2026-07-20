"""The FastMCP application: Google OAuth in front, tool/route modules behind.

This module owns the `mcp` instance and nothing else. Tools live in tools.py,
public HTTP routes in web.py, the admin API in admin.py — they all import
`mcp` from here and register themselves, so the dependency graph stays a tree.
"""
import time

from fastmcp import FastMCP
from fastmcp.server.auth.providers.google import GoogleProvider

from . import config, storage

storage.init()

# Re-recording the same user on every request would be a database write per
# MCP call; once per user per this many seconds is enough to keep the roster
# current without that cost.
_SEEN_TTL = 900
_seen = {}


class _RecordingGoogleProvider(GoogleProvider):
    """A GoogleProvider that writes the user down as soon as they authenticate.

    Signing in with Google does not, by itself, touch the database — user rows
    were only created when a tool ran or the dashboard was opened. So anyone who
    added the connector and granted access, but whose assistant had not yet
    called a Setu tool, was fully registered and completely invisible to the
    admin panel.

    verify_token runs on every authenticated MCP request, and MCP clients list
    tools immediately after connecting, so hooking it here catches a user at the
    moment they finish signing in.
    """

    async def verify_token(self, token):
        access = await super().verify_token(token)
        if access is None:
            return None

        claims = getattr(access, "claims", None) or {}
        sub, email = claims.get("sub"), claims.get("email")
        if sub and email:
            now = time.monotonic()
            if _seen.get(sub, 0) < now:
                _seen[sub] = now + _SEEN_TTL
                try:
                    storage.upsert_user(sub, email, claims.get("name"))
                except Exception:
                    # Never fail authentication because bookkeeping failed.
                    _seen.pop(sub, None)

        return access


auth = _RecordingGoogleProvider(
    client_id=config.GOOGLE_CLIENT_ID,
    client_secret=config.GOOGLE_CLIENT_SECRET,
    base_url=config.BASE_URL,
    redirect_path=config.REDIRECT_PATH,
    required_scopes=config.SCOPES,
)

mcp = FastMCP(
    "Setu",
    auth=auth,
    instructions=(
        "Setu sends email from the signed-in user's own Gmail — not only job "
        "applications. Any email the user asks for is in scope: applications, "
        "meeting requests, follow-ups, introductions, greetings, thank-yous. "
        "The role changes what a good email looks like:\n"
        "  - job_seeker: applying for jobs. Resume link required.\n"
        "  - recruiter: reaching out to candidates about a role they're hiring for.\n"
        "  - professional: everything else — clients, partners, colleagues, "
        "meetings, and everyday professional messages.\n\n"
        "Always work in this order:\n"
        "1. get_my_profile — who they are, their role, plan, and quota.\n"
        "2. If no role is set, ask which one fits and call set_role. Ask; do not "
        "infer it. If their role needs a link and none is saved, ask for it and "
        "call save_link. Do this before writing anything — being told 'no resume "
        "saved' after you've drafted ten emails wastes everyone's time. Never "
        "invent a URL.\n"
        "3. If the user gave you the recipient's address, use it as given. "
        "Research only when you have to find addresses yourself — and then find "
        "real addresses on real pages. Never construct an address from a naming "
        "pattern: a wrong address bounces, and bounces damage the user's Gmail "
        "reputation.\n"
        "4. verify_hr_emails — optional, but call it when unsure about an address "
        "you found yourself. Skip it for addresses the user gave you.\n"
        "5. Write the email for its actual recipient and purpose. For "
        "applications, ground it in the real job posting; for a meeting request "
        "or greeting, keep it natural — not everything is a pitch.\n"
        "6. Show the user the recipient list and at least one full body, and get "
        "explicit approval.\n"
        "7. send_application or send_applications. For casual or general emails "
        "where the saved link does not belong, pass include_link=false.\n\n"
        "Sending is irreversible. Never send without showing the user first. If a "
        "tool reports the free allowance is spent, tell the user to subscribe — "
        "do not try to work around it."
    ),
)
