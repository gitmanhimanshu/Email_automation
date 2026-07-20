"""Turning link opens into something the user can act on.

An open count on its own says nothing. The same number means different things
depending on when the mail went out and how recently it was read: four opens in
an afternoon is someone forwarding your resume around, one open a week ago is
nothing, and zero opens after five days usually means the mail never arrived
where a human would see it.

A word on honesty: an open is a *signal*, not proof. Link prefetchers and mail
gateways are filtered out in web.py, but no tracking is exact, and a person can
read an email without ever clicking the link. Everything here is phrased as
evidence to act on, never as "they definitely read it" — and the tool
description says so, so the assistant doesn't overclaim to the user either.
"""
from datetime import datetime, timezone

# Repeat opens are the strongest thing we can see: someone came back, or passed
# it on. Three is where a pattern starts rather than a coincidence.
HOT_OPENS = 3

# Opened within this window is still "live" — a follow-up now lands while the
# recipient still remembers the email.
RECENT_HOURS = 48

# Below this, silence means nothing: people don't read mail instantly.
COLD_AFTER_DAYS = 4


def _parse(value):
    if not value:
        return None
    try:
        moment = datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None
    return moment.replace(tzinfo=timezone.utc) if moment.tzinfo is None else moment


def _hours_since(value):
    moment = _parse(value)
    if not moment:
        return None
    return (datetime.now(timezone.utc) - moment).total_seconds() / 3600


def classify(send):
    """One send -> {signal, headline, action, priority}.

    priority orders a mixed list so the assistant leads with what matters.
    """
    opens = send.get("open_count") or 0
    hours_since_open = _hours_since(send.get("last_opened_at"))
    hours_since_sent = _hours_since(send.get("sent_at"))
    who = send.get("company") or send.get("to_email") or "this contact"

    if opens >= HOT_OPENS:
        recent = hours_since_open is not None and hours_since_open <= RECENT_HOURS
        return {
            "signal": "hot",
            "headline": f"{who} opened your link {opens} times",
            "action": (
                "Strong interest — following up now is well timed."
                if recent
                else "Repeated opens. Worth a follow-up if you haven't already."
            ),
            "priority": 0 if recent else 1,
        }

    if opens > 0:
        if hours_since_open is not None and hours_since_open <= RECENT_HOURS:
            return {
                "signal": "warm",
                "headline": f"{who} opened your link {_ago(hours_since_open)}",
                "action": "Recently looked at it — a short follow-up is reasonable.",
                "priority": 2,
            }
        return {
            "signal": "opened",
            "headline": f"{who} opened your link {opens}x",
            "action": "Opened, but not recently. Follow up if it's been a while.",
            "priority": 3,
        }

    if hours_since_sent is not None and hours_since_sent >= COLD_AFTER_DAYS * 24:
        return {
            "signal": "cold",
            "headline": f"{who} — sent {_ago(hours_since_sent)}, never opened",
            "action": (
                "No opens at all. Check the address is right, or that the mail "
                "didn't land in spam. A different subject line may help."
            ),
            "priority": 4,
        }

    return {
        "signal": "waiting",
        "headline": f"{who} — sent {_ago(hours_since_sent) if hours_since_sent else 'recently'}",
        "action": "Too early to read anything into this.",
        "priority": 5,
    }


def _ago(hours):
    if hours is None:
        return "recently"
    if hours < 1:
        return "just now"
    if hours < 24:
        n = int(hours)
        return f"{n} hour{'s' if n != 1 else ''} ago"
    days = int(hours / 24)
    return f"{days} day{'s' if days != 1 else ''} ago"


def summarize(sends):
    """Classify a list of sends and order it by what deserves attention."""
    items = []
    for send in sends:
        item = dict(send)
        item.update(classify(send))
        items.append(item)

    items.sort(key=lambda i: (i["priority"], -(i.get("open_count") or 0)))

    counts = {}
    for item in items:
        counts[item["signal"]] = counts.get(item["signal"], 0) + 1

    return {
        "counts": counts,
        "needs_attention": [i for i in items if i["priority"] <= 2],
        "items": items,
    }
