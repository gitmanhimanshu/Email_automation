"""Settings and file locations shared by every entry point."""
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Claude launches the MCP server from an arbitrary working directory, so the
# .env and every path below are resolved absolutely rather than against the cwd.
load_dotenv(PROJECT_ROOT / ".env")

# Tokens live outside the project folder so all three entry points share one
# login, and so nothing secret can land in the repo by accident.
CONFIG_DIR = Path(os.getenv("EMAIL_AUTOMATION_HOME") or Path.home() / ".email_automation")
TOKEN_PATH = CONFIG_DIR / "token.json"
SENT_LOG_PATH = CONFIG_DIR / "sent_emails.json"


def _get(key, default=""):
    value = os.getenv(key, default)
    return value.strip() if isinstance(value, str) else value


def your_name():
    return _get("YOUR_NAME")


def your_email():
    return _get("YOUR_EMAIL")


def resume_link():
    return _get("RESUME_LINK")


def gemini_api_key():
    return _get("GEMINI_API_KEY")


def gemini_model():
    return _get("GEMINI_MODEL") or "gemini-2.0-flash"


def google_client_id():
    return _get("GOOGLE_CLIENT_ID")


def google_client_secret():
    return _get("GOOGLE_CLIENT_SECRET")


def email_delay():
    try:
        return max(0, int(_get("EMAIL_DELAY", "5")))
    except ValueError:
        return 5


def credentials_file():
    """Path to a downloaded OAuth client JSON, or None if using env vars instead."""
    explicit = _get("GMAIL_CREDENTIALS_PATH")
    candidates = [Path(explicit)] if explicit else []
    candidates += [PROJECT_ROOT / "cred.json", PROJECT_ROOT / "credentials.json"]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR


def missing_profile_fields():
    """Which .env values still need filling in before mail can go out."""
    required = {"YOUR_NAME": your_name(), "YOUR_EMAIL": your_email()}
    return [key for key, value in required.items() if not value]
