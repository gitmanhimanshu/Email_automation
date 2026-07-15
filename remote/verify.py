"""Guard against sending to addresses the model invented.

A model asked to "find the HR email for Acme" will sometimes return a real
address off the careers page, and sometimes a guess built from a naming pattern
it saw elsewhere. Guesses bounce, bounces wreck the user's Gmail reputation, and
the user pays for it with every later email they send. So an address has to earn
its way to being sent to:

  1. It must parse.
  2. Its domain must actually accept mail (MX lookup).
  3. The caller must say where it saw the address, with a real URL.

None of this proves the mailbox exists — only a paid verification API or an
actual send can do that. It does catch invented domains, typos, and the honest
case where the model admits it guessed.
"""
import re
from functools import lru_cache
from urllib.parse import urlparse

import dns.exception
import dns.resolver
import httpx

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+\.)+[A-Za-z]{2,}$")

# Phrases a model reaches for when it is pattern-matching rather than citing.
GUESS_MARKERS = re.compile(
    r"\b(guess|guessed|guessing|inferred|infer|assumed|assume|typical|common"
    r"|standard|pattern|likely|probably|derived|constructed|based on"
    r"|my knowledge|training data|n/?a|unknown|none)\b",
    re.IGNORECASE,
)

# Free mailboxes are never a company's real HR channel; if a model hands one
# back as "the HR address for Acme Corp", it is almost certainly confabulating.
CONSUMER_DOMAINS = {
    "gmail.com", "googlemail.com", "yahoo.com", "yahoo.co.in", "outlook.com",
    "hotmail.com", "live.com", "aol.com", "icloud.com", "proton.me",
    "protonmail.com", "rediffmail.com", "mail.com", "zoho.com", "yandex.com",
}

_resolver = dns.resolver.Resolver()
_resolver.lifetime = 5.0
_resolver.timeout = 5.0


@lru_cache(maxsize=2048)
def domain_accepts_mail(domain):
    """(ok, detail) — whether the domain publishes a usable mail route."""
    try:
        answers = _resolver.resolve(domain, "MX")
        hosts = sorted(str(r.exchange).rstrip(".") for r in answers)
        if not hosts:
            return False, "domain publishes no MX records"
        return True, f"MX: {', '.join(hosts[:3])}"
    except dns.resolver.NXDOMAIN:
        return False, "domain does not exist"
    except dns.resolver.NoAnswer:
        return False, "domain has no MX records (it cannot receive email)"
    except dns.resolver.NoNameservers:
        return False, "domain has no working nameservers"
    except dns.exception.Timeout:
        return False, "DNS lookup timed out"
    except dns.exception.DNSException as exc:
        return False, f"DNS lookup failed: {exc}"


def _source_problem(source_url):
    """Why this citation should not be trusted, or None if it looks real."""
    if not source_url or not source_url.strip():
        return "no source_url given — say which page you saw this address on"

    text = source_url.strip()

    if GUESS_MARKERS.search(text):
        return (
            f"source_url looks like a guess, not a citation ({text!r}). "
            "Only send to addresses you actually saw on a page."
        )

    parsed = urlparse(text)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return f"source_url must be a real http(s) URL, got {text!r}"

    return None


def check(email, source_url=None, company=None):
    """Verify one candidate address. Returns a dict with ok/reasons/warnings."""
    address = (email or "").strip()
    result = {
        "email": address,
        "company": company,
        "source_url": source_url,
        "ok": False,
        "reasons": [],
        "warnings": [],
    }

    if not EMAIL_RE.match(address):
        result["reasons"].append("not a valid email address")
        return result

    domain = address.rsplit("@", 1)[1].lower()

    problem = _source_problem(source_url)
    if problem:
        result["reasons"].append(problem)

    if domain in CONSUMER_DOMAINS:
        result["reasons"].append(
            f"{domain} is a personal mailbox provider, not a company domain. "
            "If this really is the contact's own address, send it via send_application "
            "with the page URL you found it on."
        )

    accepts, detail = domain_accepts_mail(domain)
    if not accepts:
        result["reasons"].append(f"{domain}: {detail}")

    # Not fatal, but worth surfacing: the company name and the mail domain
    # disagreeing is a common shape for a confabulated address.
    if company and accepts:
        slug = re.sub(r"[^a-z0-9]", "", company.lower())
        root = re.sub(r"[^a-z0-9]", "", domain.split(".")[0])
        if slug and root and root not in slug and slug not in root:
            result["warnings"].append(
                f"domain '{domain}' does not obviously match company '{company}' — "
                "double-check this is the right company"
            )

    result["ok"] = not result["reasons"]
    if result["ok"]:
        result["detail"] = detail
    return result


def check_many(candidates):
    """candidates: iterable of dicts with email / source_url / company."""
    return [
        check(c.get("email"), c.get("source_url"), c.get("company")) for c in candidates
    ]


# Hosts that redirect to a sign-in page when a file is not shared publicly.
_LOGIN_HOSTS = ("accounts.google.com", "login.microsoftonline.com", "www.dropbox.com/login")


async def check_resume_link(url):
    """Is this link something an HR person could actually open?

    The usual failure is not a broken link, it is a Google Drive file the user
    forgot to share. HR clicks it, gets "Request access", and the application is
    dead — while the user believes it went out fine. Cheap to catch here.

    Returns (ok, detail). Network trouble resolves to ok=True: an inconclusive
    check should not block someone from applying for jobs.
    """
    link = (url or "").strip()

    if not link.startswith(("http://", "https://")):
        return False, "The resume link must be an http(s) URL."

    try:
        async with httpx.AsyncClient(
            timeout=10.0, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"}
        ) as client:
            response = await client.get(link)
    except httpx.HTTPError as exc:
        return True, f"Could not check the link ({exc}); sending anyway."

    final_host = urlparse(str(response.url)).netloc.lower()
    final_url = str(response.url).lower()

    if any(host.split("/")[0] in final_host for host in _LOGIN_HOSTS):
        return False, (
            "This link is not shared publicly — it redirects to a sign-in page, so "
            "HR would see 'Request access' instead of the resume. Open it in Drive, "
            "click Share, and set 'Anyone with the link' to Viewer."
        )

    if "servicelogin" in final_url or "/login" in final_url:
        return False, (
            "This link redirects to a login page, so HR could not open it. "
            "Make it viewable by anyone with the link."
        )

    if response.status_code in (401, 403):
        return False, (
            "This link is private (HTTP "
            f"{response.status_code}). Share it so anyone with the link can view."
        )

    if response.status_code == 404:
        return False, "This link returns 404 — the file does not exist or was moved."

    if response.status_code >= 400:
        return True, f"Link returned HTTP {response.status_code}; could not confirm."

    return True, "Link is publicly reachable."
