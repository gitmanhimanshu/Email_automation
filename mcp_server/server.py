"""MCP server that lets Claude send job-application emails from the user's Gmail.

Claude writes the emails itself, so there is no Gemini call anywhere in here —
it already knows the user's background from the conversation, which a fixed
prompt template never would. Gemini stays behind the local Flask/CLI apps,
which have no model of their own.

Run:  python -m mcp_server.server
"""
import sys
import time
from pathlib import Path

# Claude launches this from an arbitrary working directory, so make the project
# importable before touching core.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import BaseModel, Field  # noqa: E402

from core import config, gmail_auth, sent_log  # noqa: E402
from core.email_sender import EmailSender  # noqa: E402
from core.sheets_reader import SheetsReader  # noqa: E402

try:  # The SDK renamed FastMCP to MCPServer; support both.
    from mcp.server.mcpserver import MCPServer
except ImportError:  # pragma: no cover
    from mcp.server.fastmcp import FastMCP as MCPServer

mcp = MCPServer("email-automation")

# A single tool call should never be able to mail a hundred strangers.
MAX_PER_BATCH = 25


class OutgoingEmail(BaseModel):
    to: str = Field(description="Recipient email address")
    subject: str = Field(description="Subject line")
    body: str = Field(description="Plain text body, already personalized")


def _sender():
    """An EmailSender, or an AuthError telling the user how to fix it."""
    return EmailSender(gmail_auth.get_service(), config.your_email())


def _profile_problems():
    missing = config.missing_profile_fields()
    if missing:
        return f"Missing in .env: {', '.join(missing)}. Fill them in and restart the server."
    if not gmail_auth.has_token():
        return "Gmail is not authorized. Run `python authorize.py` once in a terminal."
    return None


@mcp.tool()
def get_sender_profile() -> dict:
    """Who the emails will be sent as, and whether Gmail is ready.

    Call this before writing any email — use the returned name and resume link
    so the content matches the account the mail actually goes out from.
    """
    return {
        "your_name": config.your_name(),
        "your_email": config.your_email(),
        "resume_link": config.resume_link(),
        "gmail_authorized": gmail_auth.has_token(),
        "credentials_source": gmail_auth.credentials_source(),
        "default_delay_seconds": config.email_delay(),
        "max_emails_per_batch": MAX_PER_BATCH,
        "setup_needed": _profile_problems(),
    }


@mcp.tool()
def load_recipients_from_sheet(sheet_url: str) -> dict:
    """Load HR contacts from a public Google Sheet.

    The sheet must be shared as 'Anyone with the link can view' and needs an
    email column; name, company, job position and resume link are optional and
    matched flexibly against the headers.
    """
    try:
        reader = SheetsReader(sheet_url)
        recipients = reader.validate_records(reader.read_public_sheet())
    except Exception as exc:
        return {"success": False, "error": str(exc)}

    return {"success": True, "count": len(recipients), "recipients": recipients}


@mcp.tool()
def check_already_contacted(emails: list[str]) -> dict:
    """Which of these addresses have already been mailed successfully before.

    Worth calling before a batch — the send log persists across sessions, so
    this is the only way to avoid mailing the same HR twice.
    """
    contacted = [e for e in emails if sent_log.already_sent_to(e)]
    return {
        "already_contacted": contacted,
        "new": [e for e in emails if e not in contacted],
    }


@mcp.tool()
def send_email(to: str, subject: str, body: str, cc: str | None = None) -> dict:
    """Send ONE email immediately from the user's Gmail.

    This is irreversible — the mail is delivered as soon as this returns. Show
    the user the exact subject and body and get their approval before calling
    this for the first time in a conversation.
    """
    problem = _profile_problems()
    if problem:
        return {"success": False, "error": problem}

    try:
        result = _sender().send(to, subject, body, cc)
    except Exception as exc:
        # Return the failure as data. Raising here would surface to Claude as an
        # opaque tool crash instead of something the user can act on.
        return {"success": False, "to": to, "error": str(exc)}

    sent_log.record([result])
    return result


@mcp.tool()
def send_bulk_emails(
    emails: list[OutgoingEmail],
    delay_seconds: int | None = None,
) -> dict:
    """Send a batch of already-written emails, pausing between each one.

    Irreversible. Show the user the full list of recipients and at least one
    complete sample body, and get explicit approval, before calling this.

    Each email should already be personalized — pass one entry per recipient
    rather than the same body to everyone. The pause keeps Gmail from treating
    the run as spam; it defaults to EMAIL_DELAY from .env.
    """
    problem = _profile_problems()
    if problem:
        return {"success": False, "error": problem}

    if not emails:
        return {"success": False, "error": "No emails provided."}

    if len(emails) > MAX_PER_BATCH:
        return {
            "success": False,
            "error": (
                f"{len(emails)} emails in one call exceeds the {MAX_PER_BATCH} limit. "
                "Split them into smaller batches so the user can review as they go."
            ),
        }

    try:
        sender = _sender()
    except Exception as exc:
        return {"success": False, "error": str(exc)}

    pause = config.email_delay() if delay_seconds is None else max(0, delay_seconds)

    results = []
    for index, email in enumerate(emails):
        results.append(sender.send(email.to, email.subject, email.body))
        if index < len(emails) - 1 and pause:
            time.sleep(pause)

    sent_log.record(results)
    succeeded = sum(1 for r in results if r["success"])

    return {
        "success": True,
        "total": len(results),
        "sent": succeeded,
        "failed": len(results) - succeeded,
        "results": results,
    }


@mcp.tool()
def get_sent_log(limit: int = 20) -> dict:
    """The most recent emails this tool has sent, newest last."""
    entries = sent_log.read(limit=limit)
    return {"count": len(entries), "log_file": str(config.SENT_LOG_PATH), "entries": entries}


if __name__ == "__main__":
    mcp.run()
