"""Setu — job applications sent from the user's own Gmail, driven from an AI chat.

A bridge: the client (claude.ai, ChatGPT, any MCP client) does the research and
the writing; this server owns the parts a model should not be trusted with —
who the user is, how much they have already sent, and the actual send.

This module is only the entry point. The pieces:

    app.py       the FastMCP instance + Google OAuth
    tools.py     the MCP tools the assistant calls
    web.py       public HTTP routes (/health, /api/stats, /api/visit)
    admin.py     the admin panel API (/admin/api/*)
    rules.py     the send gates (role, link, plan)
    identity.py  access token -> Google identity
    storage.py   users, sends, visitors (SQLite or Postgres)

Run locally:  python -m remote.server
"""
from . import admin, tools, web  # noqa: F401  (importing registers their routes/tools)
from . import config
from .app import mcp  # noqa: F401  (re-exported: `from remote.server import mcp` still works)


def main():
    missing = config.missing_settings()
    if missing:
        raise SystemExit(
            f"Missing environment variables: {', '.join(missing)}\n"
            "See remote/README.md for setup."
        )

    # Temporary patch to log raw MCP incoming requests for debugging
    import starlette.requests
    import starlette.responses
    
    orig_body = starlette.requests.Request.body
    async def patched_body(self):
        b = await orig_body(self)
        if "mcp" in self.url.path:
            print(f"===== MCP REQUEST ({self.method} {self.url.path}) =====")
            try:
                print(b.decode("utf-8"))
            except Exception as e:
                print(f"<Could not decode body: {e}>")
        return b
    starlette.requests.Request.body = patched_body

    orig_response = starlette.responses.Response.__call__
    async def patched_response(self, scope, receive, send):
        if scope["type"] == "http" and "mcp" in scope.get("path", ""):
            print(f"===== MCP RESPONSE ({self.status_code}) =====")
            try:
                print(self.body.decode("utf-8"))
            except Exception:
                pass
        return await orig_response(self, scope, receive, send)
    starlette.responses.Response.__call__ = patched_response

    mcp.run(transport="http", host=config.HOST, port=config.PORT)


if __name__ == "__main__":
    main()
