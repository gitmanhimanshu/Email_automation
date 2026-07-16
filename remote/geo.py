"""Best-effort IP geolocation for the visitor log.

Uses ip-api.com's free endpoint (no key, ~45 requests/min). It's only ever
called for an IP we haven't seen before, so a returning visitor costs nothing,
and the rate limit is far above real traffic for a site this size.

Everything here fails soft: geolocation is a nice-to-have for an analytics
panel, never a reason to drop a page hit or slow a visitor down.
"""
import ipaddress

import httpx

# Free tier is HTTP-only. We send no personal data — just the IP being resolved —
# and treat the answer as advisory, so plaintext here is acceptable.
_ENDPOINT = "http://ip-api.com/json/{ip}?fields=status,country,regionName,city,org"


def is_public(ip):
    """False for localhost, LAN, and anything unroutable — no point geolocating."""
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return not (addr.is_private or addr.is_loopback or addr.is_reserved or addr.is_link_local)


async def locate(ip):
    """Return {country, region, city, org} or None. Never raises."""
    if not ip or not is_public(ip):
        return None

    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            response = await client.get(_ENDPOINT.format(ip=ip))
        data = response.json()
    except Exception:
        return None

    if data.get("status") != "success":
        return None

    return {
        "country": data.get("country"),
        "region": data.get("regionName"),
        "city": data.get("city"),
        "org": data.get("org"),
    }
