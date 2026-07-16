"""The send gates: what must be true before an email may leave.

Everything here returns an explanation string (for the model to relay) or
None. The strings are part of the product — they tell the assistant exactly
what to ask the user for — so treat their wording as an interface.
"""
from . import config, storage


def role_of(user):
    role = (user or {}).get("role")
    return role if role in config.ROLES else None


def append_link(body, link, role):
    """Append the user's link, labelled for who they are — a resume for a job
    seeker, a job description for a recruiter. Same mechanism, different word."""
    if not link or link in body:
        return body
    label = config.ROLES.get(role, {}).get("link_label", "Link")
    return f"{body.rstrip()}\n\n{label}: {link}"


def link_problem(user):
    """Why this user can't send yet, or None.

    Only job seekers are hard-gated: an application with no resume wastes the
    send and burns the contact. A recruiter emailing a candidate, or a
    professional doing outreach, often has nothing to attach — blocking them
    would be inventing a requirement that isn't real.
    """
    role = role_of(user)
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


def plan_problem(user, sub):
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
