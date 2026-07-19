"""The MCP tools — the surface the AI assistant sees.

Docstrings here are read by the model as tool descriptions, so they are
written as instructions to it. The rules the model must not be able to talk
its way around (limits, gates) live in rules.py and storage.py, not here.
"""
import asyncio

from . import config, gmail, storage, verify
from .app import mcp
from .identity import current_user
from .models import Application, Candidate
from .rules import append_link, link_problem, plan_problem, role_of


@mcp.tool
async def get_my_profile() -> dict:
    """Who the signed-in user is, their role, saved link, plan, and quota.

    Call this first. Emails go out from this Gmail account, so the content must
    match this person — and the role decides what kind of email makes sense.
    """
    _, identity = await current_user()
    sub = identity["sub"]
    user = storage.get_user(sub) or {}
    role = role_of(user)
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
        "setup_needed": link_problem(user) or plan_problem(user, sub),
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

    _, identity = await current_user()
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

    _, identity = await current_user()
    user = storage.get_user(identity["sub"]) or {}
    storage.set_link(identity["sub"], url)

    role = role_of(user)
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
    _, identity = await current_user()

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
    include_link: bool = True,
) -> dict:
    """Send ONE email from the user's Gmail. Irreversible.

    Despite the name, this sends any email the user asks for — a job
    application, a meeting request, a follow-up, a greeting. For a job seeker
    it refuses until a resume link is saved; other roles have no such gate.

    The user's saved link is appended by default. Pass include_link=false for
    general messages where it does not belong (greetings, meeting requests,
    replies to someone who already has it).

    Show the user the full subject and body and get their approval first.
    """
    access_token, identity = await current_user()
    sub = identity["sub"]
    user = storage.get_user(sub) or {}

    problem = link_problem(user)
    if problem:
        return {"success": False, "to": to, "error": problem, "needs": "role_or_link"}

    problem = plan_problem(user, sub)
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
        append_link(body, user.get("link") if include_link else None, role_of(user)),
        sender=identity["email"],
    )
    result.update(company=company, source_url=source_url)
    storage.record_sends(identity["sub"], [result])
    return result


@mcp.tool
async def send_applications(
    applications: list[Application],
    delay_seconds: int | None = None,
    include_link: bool = True,
) -> dict:
    """Send a batch of emails, pausing between each. Irreversible.

    Works for any kind of email, not only applications. Pass include_link=false
    to leave the user's saved link off every message in the batch.

    Show the user every recipient and at least one full body, and get explicit
    approval, before calling this. Each email should be written for its own
    recipient — do not send the same body to everyone.
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

    access_token, identity = await current_user()
    sub = identity["sub"]
    user = storage.get_user(sub) or {}

    problem = link_problem(user)
    if problem:
        return {"success": False, "error": problem, "needs": "role_or_link"}

    problem = plan_problem(user, sub)
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
    link, role = (user.get("link") if include_link else None), role_of(user)

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
            append_link(application.body, link, role),
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
    _, identity = await current_user()
    return {
        "sent_last_24h": storage.sent_today(identity["sub"]),
        "daily_limit": config.DAILY_SEND_LIMIT,
        "entries": storage.recent_sends(identity["sub"], limit),
    }


@mcp.tool
async def get_my_stats() -> dict:
    """The user's numbers at a glance — call when they ask how it's going.

    "How many emails have I sent?", "show my stats", "how many companies did
    I reach?", "did anything fail?" — this answers all of those in one call:
    lifetime and 24h send counts, companies reached, failures, remaining
    quota, plan, and the last few sends. Summarise it conversationally;
    don't dump the raw dict.
    """
    _, identity = await current_user()
    sub = identity["sub"]
    user = storage.get_user(sub) or {}

    history = storage.recent_sends(sub, limit=200)
    lifetime = storage.total_sent(sub)
    used_today = storage.sent_today(sub)
    plan = user.get("plan", "free")

    return {
        "email": identity["email"],
        "name": identity.get("name"),
        "plan": plan,
        "total_sent": lifetime,
        "total_failed": sum(1 for r in history if not r["success"]),
        "companies_reached": len(
            {r["company"] for r in history if r["company"] and r["success"]}
        ),
        "sent_last_24h": used_today,
        "daily_limit": config.DAILY_SEND_LIMIT,
        "remaining_today": max(0, config.DAILY_SEND_LIMIT - used_today),
        "free_remaining": max(0, config.FREE_EMAIL_LIMIT - lifetime) if plan == "free" else None,
        "subscription_ends_at": user.get("subscription_ends_at"),
        "recent": [
            {
                "to_email": r["to_email"],
                "company": r["company"],
                "subject": r["subject"],
                "success": bool(r["success"]),
                "sent_at": r["sent_at"],
            }
            for r in history[:5]
        ],
    }
