"""Who is calling. Resolves the request's access token to a Google identity.

The OAuth proxy hands us a live token per request; nothing is stored beyond a
short in-process cache, so a revoked token stops working within minutes.
"""
import time

from fastmcp.server.dependencies import get_access_token

from . import gmail, storage

# userinfo costs an HTTP round trip; a short cache keeps it off the hot path
# without letting a revoked token linger.
_IDENTITY_TTL = 300
_cache = {}


async def current_user():
    """(access_token, identity) for the signed-in user, upserted into storage."""
    token = get_access_token()
    access_token = token.token

    cached = _cache.get(access_token)
    if cached and cached["expires"] > time.monotonic():
        return access_token, cached["identity"]

    claims = getattr(token, "claims", None) or {}
    if claims.get("sub") and claims.get("email"):
        identity = {
            "sub": claims["sub"],
            "email": claims["email"],
            "name": claims.get("name"),
        }
    else:
        identity = await gmail.fetch_identity(access_token)

    if not identity.get("sub"):
        raise ValueError("Could not identify the signed-in Google account.")

    storage.upsert_user(identity["sub"], identity["email"], identity.get("name"))
    _cache[access_token] = {
        "identity": identity,
        "expires": time.monotonic() + _IDENTITY_TTL,
    }
    return access_token, identity
