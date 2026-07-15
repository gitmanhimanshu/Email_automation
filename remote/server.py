"""Setu — job applications sent from the user's own Gmail, driven from an AI chat.

A bridge: the client (claude.ai, ChatGPT, any MCP client) does the research and
the writing; this server owns the parts a model should not be trusted with —
who the user is, how much they have already sent, and the actual send.

Run locally:  python -m remote.server
"""
import asyncio
import time

from fastmcp import FastMCP
from fastmcp.server.auth.providers.google import GoogleProvider
from fastmcp.server.dependencies import get_access_token
from pydantic import BaseModel, Field

from . import config, gmail, storage, verify

storage.init()

auth = GoogleProvider(
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
        "Setu sends job application emails from the signed-in user's own Gmail.\n\n"
        "Always work in this order:\n"
        "1. get_my_profile — learn who the user is and whether a resume link is saved.\n"
        "1b. If no resume link is saved, ask the user for it now and call "
        "save_resume_link. Sending is blocked until one exists, so ask early rather "
        "than after you have written everything. Ask the user; never invent a URL.\n"
        "2. Research the companies and find real HR/careers addresses on real pages. "
        "Never construct an address from a naming pattern; a wrong address bounces "
        "and damages the user's Gmail reputation. Prefer published careers@ / jobs@ "
        "addresses over personal ones.\n"
        "3. verify_hr_emails — optional, but call it when you are unsure about an "
        "address. It checks whether the domain can actually receive mail.\n"
        "4. Write one genuinely different email per company, grounded in that "
        "company's actual job posting.\n"
        "5. Show the user the recipient list and at least one full email body, and "
        "get their explicit approval.\n"
        "6. send_applications.\n\n"
        "Sending is irreversible. Never send without showing the user first."
    ),
)

# userinfo costs an HTTP round trip; a short cache keeps it off the hot path
# without letting a revoked token linger.
_IDENTITY_TTL = 300
_identity_cache = {}


class Candidate(BaseModel):
    email: str = Field(description="The HR or careers address")
    company: str | None = Field(default=None, description="Company it belongs to")
    source_url: str | None = Field(
        default=None,
        description=(
            "The exact page URL where you saw this address. Required. If you did "
            "not see it on a page, do not submit it."
        ),
    )


class Application(BaseModel):
    to: str = Field(description="Recipient address")
    subject: str = Field(description="Subject line")
    body: str = Field(description="Plain text body, written for this company specifically")
    company: str | None = Field(default=None)
    source_url: str | None = Field(
        default=None, description="Page URL where the address was found"
    )


async def _identity():
    """The signed-in user, from their access token."""
    token = get_access_token()
    access_token = token.token

    cached = _identity_cache.get(access_token)
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
    _identity_cache[access_token] = {
        "identity": identity,
        "expires": time.monotonic() + _IDENTITY_TTL,
    }
    return access_token, identity


def _append_resume(body, resume_link):
    """Guarantee the resume link is present without letting the model forget it."""
    if not resume_link or resume_link in body:
        return body
    return f"{body.rstrip()}\n\nResume: {resume_link}"


# A job application with no resume wastes the send and burns the contact, so the
# send tools refuse rather than trusting the model to have read get_my_profile.
NO_RESUME_ERROR = (
    "No resume link is saved for this user, and a job application without a resume "
    "is pointless. Ask the user for their resume link — a Google Drive share URL, "
    "Dropbox, personal site, whatever they use — then call save_resume_link with "
    "exactly what they give you and retry. Never invent or guess the URL."
)


@mcp.tool
async def get_my_profile() -> dict:
    """Who the signed-in user is, their saved resume link, and remaining quota.

    Call this first. The emails go out from this Gmail account, so the content
    must match this person.
    """
    _, identity = await _identity()
    user = storage.get_user(identity["sub"]) or {}
    used = storage.sent_today(identity["sub"])

    return {
        "email": identity["email"],
        "name": identity.get("name"),
        "resume_link": user.get("resume_link"),
        "resume_link_saved": bool(user.get("resume_link")),
        "sent_last_24h": used,
        "daily_limit": config.DAILY_SEND_LIMIT,
        "remaining_today": max(0, config.DAILY_SEND_LIMIT - used),
        "max_per_batch": config.MAX_PER_BATCH,
        "next_step": (
            "Ask the user for their resume link (Google Drive, etc.) and call "
            "save_resume_link before sending."
            if not user.get("resume_link")
            else "Ready to send."
        ),
    }


@mcp.tool
async def save_resume_link(resume_link: str) -> dict:
    """Save the user's resume link. It is appended to every application sent.

    Ask the user for this directly and paste exactly what they give you — never
    invent, guess, or complete a URL. The link is checked here to make sure HR
    could actually open it.
    """
    link = resume_link.strip()
    ok, detail = await verify.check_resume_link(link)
    if not ok:
        return {"success": False, "error": detail, "resume_link": link}

    _, identity = await _identity()
    storage.set_resume_link(identity["sub"], link)
    return {"success": True, "resume_link": link, "detail": detail}


@mcp.tool
async def verify_hr_emails(candidates: list[Candidate]) -> dict:
    """Check HR addresses before using them. Advisory — it does not block sending.

    Useful when you are unsure about an address: it confirms the domain can
    actually receive mail, and flags addresses that look constructed rather than
    found. Pass the page URL where you saw each address.

    It cannot confirm a mailbox exists, only that the domain accepts mail. Prefer
    published careers@ / jobs@ addresses over personal ones.
    """
    _, identity = await _identity()

    checks = await asyncio.to_thread(
        verify.check_many, [c.model_dump() for c in candidates]
    )

    passed = [c["email"] for c in checks if c["ok"]]
    contacted = storage.already_contacted(identity["sub"], passed)
    for entry in checks:
        if entry["email"].lower() in contacted:
            entry["warnings"].append("you have already emailed this address before")
            entry["already_contacted"] = True

    usable = [c for c in checks if c["ok"] and not c.get("already_contacted")]
    return {
        "checked": len(checks),
        "usable": len(usable),
        "rejected": len([c for c in checks if not c["ok"]]),
        "results": checks,
    }


@mcp.tool
async def send_application(
    to: str,
    subject: str,
    body: str,
    company: str | None = None,
    source_url: str | None = None,
) -> dict:
    """Send ONE job application from the user's Gmail. Irreversible.

    Show the user the full subject and body and get their approval first.
    Refuses until the user has a resume link saved.
    """
    access_token, identity = await _identity()
    user = storage.get_user(identity["sub"]) or {}

    if not user.get("resume_link"):
        return {"success": False, "to": to, "error": NO_RESUME_ERROR, "needs": "resume_link"}

    if config.VERIFY_HR_EMAILS:
        check = await asyncio.to_thread(verify.check, to, source_url, company)
        if not check["ok"]:
            return {"success": False, "to": to, "error": "; ".join(check["reasons"])}

    used = storage.sent_today(identity["sub"])
    if used >= config.DAILY_SEND_LIMIT:
        return {
            "success": False,
            "error": f"Daily limit reached ({used}/{config.DAILY_SEND_LIMIT}). Try tomorrow.",
        }

    result = gmail.send(
        access_token,
        to,
        subject,
        _append_resume(body, user.get("resume_link")),
        sender=identity["email"],
    )
    result.update(company=company, source_url=source_url)
    storage.record_sends(identity["sub"], [result])
    return result


@mcp.tool
async def send_applications(
    applications: list[Application],
    delay_seconds: int | None = None,
) -> dict:
    """Send a batch of applications, pausing between each. Irreversible.

    Show the user every recipient and at least one full body, and get explicit
    approval, before calling this. Each application should be written for its own
    company — do not send the same body to everyone.
    """
    if not applications:
        return {"success": False, "error": "No applications provided."}

    if len(applications) > config.MAX_PER_BATCH:
        return {
            "success": False,
            "error": (
                f"{len(applications)} exceeds the {config.MAX_PER_BATCH} per-batch limit. "
                "Send smaller batches so the user can review as they go."
            ),
        }

    access_token, identity = await _identity()
    user = storage.get_user(identity["sub"]) or {}

    if not user.get("resume_link"):
        return {"success": False, "error": NO_RESUME_ERROR, "needs": "resume_link"}

    used = storage.sent_today(identity["sub"])
    remaining = config.DAILY_SEND_LIMIT - used
    if remaining <= 0:
        return {
            "success": False,
            "error": f"Daily limit reached ({used}/{config.DAILY_SEND_LIMIT}). Try tomorrow.",
        }

    verdict = {}
    if config.VERIFY_HR_EMAILS:
        checks = await asyncio.to_thread(
            verify.check_many,
            [
                {"email": a.to, "source_url": a.source_url, "company": a.company}
                for a in applications
            ],
        )
        verdict = {c["email"]: c for c in checks}

    pause = config.DEFAULT_DELAY_SECONDS if delay_seconds is None else max(0, delay_seconds)
    resume_link = user.get("resume_link")

    sent, skipped = [], []
    for application in applications:
        if config.VERIFY_HR_EMAILS:
            check = verdict.get(application.to, {})
            if not check.get("ok"):
                skipped.append(
                    {
                        "to": application.to,
                        "reason": "; ".join(check.get("reasons", ["unverified"])),
                    }
                )
                continue

        if len(sent) >= remaining:
            skipped.append({"to": application.to, "reason": "daily limit reached"})
            continue

        result = gmail.send(
            access_token,
            application.to,
            application.subject,
            _append_resume(application.body, resume_link),
            sender=identity["email"],
        )
        result.update(company=application.company, source_url=application.source_url)
        sent.append(result)

        if pause and len(sent) < len(applications):
            await asyncio.sleep(pause)

    if sent:
        storage.record_sends(identity["sub"], sent)

    succeeded = sum(1 for r in sent if r["success"])
    return {
        "success": True,
        "sent": succeeded,
        "failed": len(sent) - succeeded,
        "skipped": len(skipped),
        "skipped_details": skipped,
        "results": sent,
        "remaining_today": max(0, remaining - succeeded),
    }


@mcp.tool
async def get_sent_history(limit: int = 20) -> dict:
    """The applications this user has already sent, newest first."""
    _, identity = await _identity()
    return {
        "sent_last_24h": storage.sent_today(identity["sub"]),
        "daily_limit": config.DAILY_SEND_LIMIT,
        "entries": storage.recent_sends(identity["sub"], limit),
    }


@mcp.custom_route("/api/stats", methods=["GET", "OPTIONS"])
async def api_stats(request):
    """Read-only stats for the web dashboard.

    Not an MCP tool — the dashboard is a plain web page and cannot speak MCP.
    Auth is the same Google access token, resolved to an identity server-side,
    so a caller can only ever see their own rows.
    """
    from starlette.responses import JSONResponse

    origin = config.FRONTEND_ORIGIN
    cors = {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Headers": "Authorization",
        "Vary": "Origin",
    }

    if request.method == "OPTIONS":
        return JSONResponse({}, headers=cors)

    header = request.headers.get("authorization", "")
    if not header.lower().startswith("bearer "):
        return JSONResponse({"error": "missing bearer token"}, status_code=401, headers=cors)

    access_token = header.split(" ", 1)[1].strip()
    try:
        identity = await gmail.fetch_identity(access_token)
    except Exception:
        return JSONResponse({"error": "invalid or expired token"}, status_code=401, headers=cors)

    if not identity.get("sub"):
        return JSONResponse({"error": "could not identify account"}, status_code=401, headers=cors)

    sub = identity["sub"]
    storage.upsert_user(sub, identity["email"], identity.get("name"))
    user = storage.get_user(sub) or {}
    history = storage.recent_sends(sub, limit=200)

    return JSONResponse(
        {
            "email": identity["email"],
            "name": identity.get("name"),
            "resume_link": user.get("resume_link"),
            "total_sent": sum(1 for r in history if r["success"]),
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


def main():
    missing = config.missing_settings()
    if missing:
        raise SystemExit(
            f"Missing environment variables: {', '.join(missing)}\n"
            "See remote/README.md for setup."
        )
    mcp.run(transport="http", host=config.HOST, port=config.PORT)


if __name__ == "__main__":
    main()
