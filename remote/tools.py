"""The MCP tools - the surface the AI assistant sees.

Docstrings here are read by the model as tool descriptions, so they are
written as instructions to it. The rules the model must not be able to talk
its way around (limits, gates) live in rules.py and storage.py, not here.
"""
import asyncio
import re
import secrets

from . import config, gmail, signals, storage, verify
from .app import mcp
from .identity import current_user
from .models import Application, Candidate
from .rules import append_link, link_problem, plan_problem, role_of

_LINK_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,31}$")


def _clean_link_name(name):
    """Normalised link name, or None if it is not usable as one."""
    cleaned = (name or "").strip().lower()
    return cleaned if _LINK_NAME_RE.match(cleaned) else None


def _resolve_link(user, sub, link_name):
    """(url, resolved_name, problem) for the link to attach."""
    if not link_name:
        return (user or {}).get("link"), (user or {}).get("default_link_name"), None

    cleaned = _clean_link_name(link_name)
    url = storage.get_named_link(sub, cleaned) if cleaned else None
    if url:
        return url, cleaned, None

    saved = [row["name"] for row in storage.list_links(sub)]
    return None, None, (
        f"No saved link is named {link_name!r}. "
        + (f"Saved links: {', '.join(saved)}. " if saved else "No links are saved yet. ")
        + "Ask the user which to use, or save it first with save_link."
    )


def _tracked(url):
    """(track_id, wrapped_url) - the /r/ redirect that counts link opens."""
    track_id = secrets.token_urlsafe(8)
    return track_id, f"{config.BASE_URL}/r/{track_id}"


def _clean_or_error(name):
    cleaned = _clean_link_name(name)
    if cleaned:
        return cleaned, None
    return None, (
        "Link names must be 1-32 chars of lowercase letters, numbers, '_' or '-'."
    )


@mcp.tool
async def get_my_profile() -> dict:
    """Who the signed-in user is, their role, saved link, plan, and quota.

    Call this first. Emails go out from this Gmail account, so the content must
    match this person - and the role decides what kind of email makes sense.
    """
    _, identity = await current_user()
    sub = identity["sub"]
    storage.upsert_user(sub, identity["email"], identity.get("name"))
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
        "default_link_name": user.get("default_link_name"),
        "links": storage.list_links(sub),
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

    Changeable any time - a job seeker who gets hired and starts recruiting just
    calls this again.
    """
    role = role.strip().lower()
    if role not in config.ROLES:
        return {
            "success": False,
            "error": f"Unknown role {role!r}. Pick one of: {', '.join(config.ROLES)}",
        }

    _, identity = await current_user()
    storage.upsert_user(identity["sub"], identity["email"], identity.get("name"))
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
async def save_link(
    link: str,
    name: str | None = None,
    make_default: bool = False,
) -> dict:
    """Save a link the server can attach to emails.

    What it is depends on the role - a resume, a job description, or a
    portfolio. Ask the user for the exact URL; never invent, guess, or
    complete it. If `name` is given, it saves an additional named link the
    assistant can refer to later with `link_name` while sending.
    """
    url = link.strip()
    ok, detail = await verify.check_resume_link(url)
    if not ok:
        return {"success": False, "error": detail, "link": url}

    _, identity = await current_user()
    sub = identity["sub"]
    storage.upsert_user(sub, identity["email"], identity.get("name"))
    user = storage.get_user(sub) or {}
    role = role_of(user)

    if name:
        cleaned, error = _clean_or_error(name)
        if error:
            return {"success": False, "error": error}
        storage.save_named_link(sub, cleaned, url, make_default=make_default)
        return {
            "success": True,
            "name": cleaned,
            "link": url,
            "is_default": bool(make_default or not user.get("link")),
            "default_link_name": (storage.get_user(sub) or {}).get("default_link_name"),
            "link_label": config.ROLES.get(role, {}).get("link_label", "Link"),
            "detail": detail,
            "links": storage.list_links(sub),
        }

    storage.set_link(sub, url)
    return {
        "success": True,
        "name": "default",
        "link": url,
        "is_default": True,
        "default_link_name": "default",
        "link_label": config.ROLES.get(role, {}).get("link_label", "Link"),
        "detail": detail,
        "links": storage.list_links(sub),
    }


@mcp.tool
async def list_saved_links() -> dict:
    """List the saved links for this user, with which one is the default."""
    _, identity = await current_user()
    storage.upsert_user(identity["sub"], identity["email"], identity.get("name"))
    sub = identity["sub"]
    user = storage.get_user(sub) or {}
    return {
        "default_link_name": user.get("default_link_name"),
        "default_link": user.get("link"),
        "links": storage.list_links(sub),
    }


@mcp.tool
async def set_default_link(name: str) -> dict:
    """Choose which saved link is used by default on future sends."""
    cleaned, error = _clean_or_error(name)
    if error:
        return {"success": False, "error": error}

    _, identity = await current_user()
    storage.upsert_user(identity["sub"], identity["email"], identity.get("name"))
    if not storage.set_default_link(identity["sub"], cleaned):
        saved = [row["name"] for row in storage.list_links(identity["sub"])]
        return {
            "success": False,
            "error": (
                f"No saved link is named {name!r}. "
                + (f"Saved links: {', '.join(saved)}." if saved else "No links are saved yet.")
            ),
        }

    user = storage.get_user(identity["sub"]) or {}
    return {
        "success": True,
        "default_link_name": user.get("default_link_name"),
        "link": user.get("link"),
        "links": storage.list_links(identity["sub"]),
    }


@mcp.tool
async def delete_link(name: str) -> dict:
    """Delete one saved link by name."""
    cleaned, error = _clean_or_error(name)
    if error:
        return {"success": False, "error": error}

    _, identity = await current_user()
    storage.upsert_user(identity["sub"], identity["email"], identity.get("name"))
    if not storage.get_named_link(identity["sub"], cleaned):
        return {"success": False, "error": f"No saved link is named {name!r}."}

    storage.delete_named_link(identity["sub"], cleaned)
    user = storage.get_user(identity["sub"]) or {}
    return {
        "success": True,
        "deleted": cleaned,
        "default_link_name": user.get("default_link_name"),
        "link": user.get("link"),
        "links": storage.list_links(identity["sub"]),
    }


@mcp.tool
async def verify_hr_emails(candidates: list[Candidate]) -> dict:
    """Check HR addresses before using them. Advisory - it does not block sending.

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
    link_name: str | None = None,
) -> dict:
    """Send ONE email from the user's Gmail. Irreversible.

    Despite the name, this sends any email the user asks for - a job
    application, a meeting request, a follow-up, a greeting. For a job seeker
    it refuses until a resume link is saved; other roles have no such gate.

    The user's saved link is appended by default. Pass include_link=false for
    general messages where it does not belong. If multiple links are saved,
    pass `link_name` to choose which one to attach for this send.
    """
    access_token, identity = await current_user()
    sub = identity["sub"]
    storage.upsert_user(sub, identity["email"], identity.get("name"))
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

    tracked_link = None
    track_id = None
    resolved_link_name = None
    final_body = body
    if include_link:
        resolved_link, resolved_link_name, problem = _resolve_link(user, sub, link_name)
        if problem:
            return {"success": False, "to": to, "error": problem, "needs": "link_name"}
        if resolved_link:
            track_id, wrapped_link = _tracked(resolved_link)
            tracked_link = resolved_link
            final_body = append_link(body, wrapped_link, role_of(user))

    result = gmail.send(
        access_token,
        to,
        subject,
        final_body,
        sender=identity["email"],
    )
    result.update(
        company=company,
        source_url=source_url,
        track_id=track_id,
        tracked_link=tracked_link,
        link_name=resolved_link_name,
    )
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
    to leave the user's saved link off every message in the batch. If multiple
    links are saved, each application can name its own `link_name`.
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
    storage.upsert_user(sub, identity["email"], identity.get("name"))
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
    role = role_of(user)

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
                        "free plan allowance spent - subscribe to send the rest"
                        if user.get("plan", "free") == "free"
                        else "daily limit reached"
                    ),
                }
            )
            continue

        tracked_link = None
        track_id = None
        resolved_link_name = None
        final_body = application.body
        if include_link:
            resolved_link, resolved_link_name, problem = _resolve_link(
                user, sub, application.link_name
            )
            if problem:
                skipped.append({"to": application.to, "reason": problem})
                continue
            if resolved_link:
                track_id, wrapped_link = _tracked(resolved_link)
                tracked_link = resolved_link
                final_body = append_link(application.body, wrapped_link, role)

        result = gmail.send(
            access_token,
            application.to,
            application.subject,
            final_body,
            sender=identity["email"],
        )
        result.update(
            company=application.company,
            source_url=application.source_url,
            track_id=track_id,
            tracked_link=tracked_link,
            link_name=resolved_link_name,
        )
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
    storage.upsert_user(identity["sub"], identity["email"], identity.get("name"))
    return {
        "sent_last_24h": storage.sent_today(identity["sub"]),
        "daily_limit": config.DAILY_SEND_LIMIT,
        "entries": storage.recent_sends(identity["sub"], limit),
    }


@mcp.tool
async def get_my_stats() -> dict:
    """The user's numbers at a glance - call when they ask how it is going."""
    _, identity = await current_user()
    sub = identity["sub"]
    storage.upsert_user(sub, identity["email"], identity.get("name"))
    user = storage.get_user(sub) or {}

    history = storage.recent_sends(sub, limit=200)
    lifetime = storage.total_sent(sub)
    stats = storage.lifetime_stats(sub)
    used_today = storage.sent_today(sub)
    plan = user.get("plan", "free")

    return {
        "email": identity["email"],
        "name": identity.get("name"),
        "plan": plan,
        "total_sent": lifetime,
        "total_failed": stats["total_failed"],
        "total_opens": stats["total_opens"],
        "opened_sends": stats["opened_sends"],
        "companies_reached": stats["companies_reached"],
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
                "open_count": r.get("open_count") or 0,
                "last_opened_at": r.get("last_opened_at"),
                "link_name": r.get("link_name"),
            }
            for r in history[:5]
        ],
    }


@mcp.tool
async def get_link_activity(limit: int = 50) -> dict:
    """Who has been opening the links you sent, and what to do about it.

    Every link Setu sends is tracked, so this shows which recipients actually
    opened yours, how many times, and how recently — ordered so the ones worth
    acting on come first.

    Read the signals as:
      hot     — opened several times. Someone came back to it, or forwarded it.
                The best moment to follow up.
      warm    — opened in the last couple of days.
      opened  — opened, but a while ago.
      cold    — sent days ago and never opened. Usually a wrong address or a
                spam folder, not disinterest.
      waiting — sent too recently to read anything into.

    Tell the user what the numbers are and suggest the follow-up, but do not
    claim the recipient "read" or "definitely saw" anything: an open means the
    link was fetched, which is evidence, not proof. Someone can also read the
    email without ever clicking the link.
    """
    _, identity = await current_user()
    sub = identity["sub"]
    storage.upsert_user(sub, identity["email"], identity.get("name"))

    activity = signals.summarize(storage.link_activity(sub, limit))

    return {
        "counts": activity["counts"],
        "needs_attention": [
            {
                "company": i.get("company"),
                "to_email": i.get("to_email"),
                "signal": i["signal"],
                "headline": i["headline"],
                "action": i["action"],
                "open_count": i.get("open_count") or 0,
                "last_opened_at": i.get("last_opened_at"),
                "sent_at": i.get("sent_at"),
            }
            for i in activity["needs_attention"]
        ],
        "all": [
            {
                "company": i.get("company"),
                "to_email": i.get("to_email"),
                "subject": i.get("subject"),
                "signal": i["signal"],
                "headline": i["headline"],
                "action": i["action"],
                "open_count": i.get("open_count") or 0,
                "sent_at": i.get("sent_at"),
                "last_opened_at": i.get("last_opened_at"),
            }
            for i in activity["items"]
        ],
        "note": (
            "An open means the tracked link was fetched. It is a signal, not "
            "proof that the recipient read the email."
        ),
    }
