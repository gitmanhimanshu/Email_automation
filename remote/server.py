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
        "Setu sends email from the signed-in user's own Gmail. It serves three "
        "kinds of people, and the role changes what a good email looks like:\n"
        "  - job_seeker: applying for jobs. Resume link required.\n"
        "  - recruiter: reaching out to candidates about a role they're hiring for.\n"
        "  - professional: general outreach — clients, partners, cold contacts.\n\n"
        "Always work in this order:\n"
        "1. get_my_profile — who they are, their role, plan, and quota.\n"
        "2. If no role is set, ask which one fits and call set_role. Ask; do not "
        "infer it. If their role needs a link and none is saved, ask for it and "
        "call save_link. Do this before writing anything — being told 'no resume "
        "saved' after you've drafted ten emails wastes everyone's time. Never "
        "invent a URL.\n"
        "3. Research the recipients and find real addresses on real pages. Never "
        "construct an address from a naming pattern — a wrong address bounces, and "
        "bounces damage the user's Gmail reputation. Prefer published addresses "
        "over guessed personal ones.\n"
        "4. verify_hr_emails — optional, but call it when unsure about an address.\n"
        "5. Write one genuinely different email per recipient, grounded in "
        "something real about them: the actual job posting, the candidate's actual "
        "work, the company's actual situation.\n"
        "6. Show the user the recipient list and at least one full body, and get "
        "explicit approval.\n"
        "7. send_application or send_applications.\n\n"
        "Sending is irreversible. Never send without showing the user first. If a "
        "tool reports the free allowance is spent, tell the user to subscribe — "
        "do not try to work around it."
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


def _role_of(user):
    role = (user or {}).get("role")
    return role if role in config.ROLES else None


def _append_link(body, link, role):
    """Append the user's link, labelled for who they are — a resume for a job
    seeker, a job description for a recruiter. Same mechanism, different word."""
    if not link or link in body:
        return body
    label = config.ROLES.get(role, {}).get("link_label", "Link")
    return f"{body.rstrip()}\n\n{label}: {link}"


def _link_problem(user):
    """Why this user can't send yet, or None.

    Only job seekers are hard-gated: an application with no resume wastes the
    send and burns the contact. A recruiter emailing a candidate, or a
    professional doing outreach, often has nothing to attach — blocking them
    would be inventing a requirement that isn't real.
    """
    role = _role_of(user)
    if not role:
        return (
            "This user hasn't set a role yet. Ask them which fits — job seeker, "
            "recruiter, or professional — and call set_role. The role decides what "
            "link goes out with their emails."
        )

    spec = config.ROLES[role]
    if spec["link_required"] and not (user or {}).get("link"):
        return (
            f"No {spec['link_label'].lower()} link is saved, and this user is a "
            f"{spec['label'].lower()} — sending without one wastes the contact. "
            f"Ask them for {spec['link_hint']}, call save_link with exactly what "
            "they give you, then retry. Never invent the URL."
        )
    return None


def _plan_problem(user, sub):
    """Free-plan allowance check. Lifetime, not daily."""
    if (user or {}).get("plan", "free") != "free":
        return None

    used = storage.total_sent(sub)
    if used < config.FREE_EMAIL_LIMIT:
        return None

    return (
        f"The free plan covers {config.FREE_EMAIL_LIMIT} emails and this user has "
        f"sent {used}. Tell them to subscribe to keep sending — do not attempt to "
        "work around this."
    )


@mcp.tool
async def get_my_profile() -> dict:
    """Who the signed-in user is, their role, saved link, plan, and quota.

    Call this first. Emails go out from this Gmail account, so the content must
    match this person — and the role decides what kind of email makes sense.
    """
    _, identity = await _identity()
    sub = identity["sub"]
    user = storage.get_user(sub) or {}
    role = _role_of(user)
    spec = config.ROLES.get(role, {})

    used_today = storage.sent_today(sub)
    lifetime = storage.total_sent(sub)
    plan = user.get("plan", "free")

    return {
        "email": identity["email"],
        "name": identity.get("name"),
        "role": role,
        "role_label": spec.get("label"),
        "available_roles": {k: v["label"] for k, v in config.ROLES.items()},
        "link": user.get("link"),
        "link_label": spec.get("link_label"),
        "link_saved": bool(user.get("link")),
        "link_required": spec.get("link_required", False),
        "plan": plan,
        "subscribed_at": user.get("subscribed_at"),
        "subscription_ends_at": user.get("subscription_ends_at"),
        "total_sent": lifetime,
        "free_email_limit": config.FREE_EMAIL_LIMIT,
        "free_remaining": max(0, config.FREE_EMAIL_LIMIT - lifetime) if plan == "free" else None,
        "sent_last_24h": used_today,
        "daily_limit": config.DAILY_SEND_LIMIT,
        "remaining_today": max(0, config.DAILY_SEND_LIMIT - used_today),
        "max_per_batch": config.MAX_PER_BATCH,
        "setup_needed": _link_problem(user) or _plan_problem(user, sub),
    }


@mcp.tool
async def set_role(role: str) -> dict:
    """Set what the user does. Ask them; don't infer it from context.

    - job_seeker: applying for jobs. A resume link is required before sending.
    - recruiter: reaching out to candidates. A job description link is optional.
    - professional: general outreach. A portfolio link is optional.

    Changeable any time — a job seeker who gets hired and starts recruiting just
    calls this again.
    """
    role = role.strip().lower()
    if role not in config.ROLES:
        return {
            "success": False,
            "error": f"Unknown role {role!r}. Pick one of: {', '.join(config.ROLES)}",
        }

    _, identity = await _identity()
    storage.set_role(identity["sub"], role)
    spec = config.ROLES[role]

    return {
        "success": True,
        "role": role,
        "role_label": spec["label"],
        "link_label": spec["link_label"],
        "link_required": spec["link_required"],
        "next_step": (
            f"Ask the user for {spec['link_hint']} and call save_link."
            if spec["link_required"]
            else f"Optional: ask if they want a {spec['link_label'].lower()} link on their emails."
        ),
    }


@mcp.tool
async def save_link(link: str) -> dict:
    """Save the URL that rides along with every email this user sends.

    What it is depends on their role — a resume, a job description, a portfolio.
    Ask them for it and paste exactly what they give you; never invent, guess, or
    complete a URL. Setu fetches it to confirm the recipient could actually open
    it, so a private Drive file is rejected here rather than silently failing in
    someone's inbox.
    """
    url = link.strip()
    ok, detail = await verify.check_resume_link(url)
    if not ok:
        return {"success": False, "error": detail, "link": url}

    _, identity = await _identity()
    user = storage.get_user(identity["sub"]) or {}
    storage.set_link(identity["sub"], url)

    role = _role_of(user)
    return {
        "success": True,
        "link": url,
        "link_label": config.ROLES.get(role, {}).get("link_label", "Link"),
        "detail": detail,
    }


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
    sub = identity["sub"]
    user = storage.get_user(sub) or {}

    problem = _link_problem(user)
    if problem:
        return {"success": False, "to": to, "error": problem, "needs": "role_or_link"}

    problem = _plan_problem(user, sub)
    if problem:
        return {"success": False, "to": to, "error": problem, "needs": "subscription"}

    if config.VERIFY_HR_EMAILS:
        check = await asyncio.to_thread(verify.check, to, source_url, company)
        if not check["ok"]:
            return {"success": False, "to": to, "error": "; ".join(check["reasons"])}

    used = storage.sent_today(sub)
    if used >= config.DAILY_SEND_LIMIT:
        return {
            "success": False,
            "error": f"Daily limit reached ({used}/{config.DAILY_SEND_LIMIT}). Try tomorrow.",
        }

    result = gmail.send(
        access_token,
        to,
        subject,
        _append_link(body, user.get("link"), _role_of(user)),
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
    sub = identity["sub"]
    user = storage.get_user(sub) or {}

    problem = _link_problem(user)
    if problem:
        return {"success": False, "error": problem, "needs": "role_or_link"}

    problem = _plan_problem(user, sub)
    if problem:
        return {"success": False, "error": problem, "needs": "subscription"}

    used = storage.sent_today(sub)
    remaining = config.DAILY_SEND_LIMIT - used
    if remaining <= 0:
        return {
            "success": False,
            "error": f"Daily limit reached ({used}/{config.DAILY_SEND_LIMIT}). Try tomorrow.",
        }

    # The free allowance is lifetime, so a batch must not be able to overshoot it.
    if user.get("plan", "free") == "free":
        remaining = min(remaining, config.FREE_EMAIL_LIMIT - storage.total_sent(sub))

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
    link, role = user.get("link"), _role_of(user)

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
            skipped.append(
                {
                    "to": application.to,
                    "reason": (
                        "free plan allowance spent — subscribe to send the rest"
                        if user.get("plan", "free") == "free"
                        else "daily limit reached"
                    ),
                }
            )
            continue

        result = gmail.send(
            access_token,
            application.to,
            application.subject,
            _append_link(application.body, link, role),
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
