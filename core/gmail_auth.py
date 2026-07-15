"""Gmail OAuth using the user's own Google client ID and secret.

Credentials come from either GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET in .env or a
cred.json downloaded from Google Cloud. Nothing here writes to stdout: the MCP
server speaks JSON-RPC over stdout, and a stray print would corrupt it.
"""
import json

from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from . import config

# Send-only. This deliberately cannot read the inbox, so an authorized token
# can never be used to page through the user's mail.
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

OAUTH_PORT = 8080


class AuthError(Exception):
    """Raised when Gmail cannot be authorized without user action."""


def _client_config():
    client_id = config.google_client_id()
    client_secret = config.google_client_secret()
    if not (client_id and client_secret):
        return None
    return {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }


def _build_flow():
    client_config = _client_config()
    if client_config:
        return InstalledAppFlow.from_client_config(client_config, SCOPES)

    cred_file = config.credentials_file()
    if cred_file:
        return InstalledAppFlow.from_client_secrets_file(str(cred_file), SCOPES)

    raise AuthError(
        "No Google OAuth credentials found. Set GOOGLE_CLIENT_ID and "
        "GOOGLE_CLIENT_SECRET in .env, or put cred.json in the project folder."
    )


def _stale_token_message(exc):
    """Turn Google's terse OAuth errors into something the user can act on."""
    text = str(exc)
    if "invalid_client" in text:
        return (
            "Google did not recognize the OAuth client. Check GOOGLE_CLIENT_ID and "
            "GOOGLE_CLIENT_SECRET in .env, then run `python authorize.py` again."
        )
    if "invalid_grant" in text or "expired" in text or "revoked" in text:
        return (
            "Your Gmail login has expired or was revoked. Run `python authorize.py` "
            "again to sign in."
        )
    return f"Gmail authorization failed: {text}"


def _load_token():
    if not config.TOKEN_PATH.exists():
        return None
    try:
        return Credentials.from_authorized_user_file(str(config.TOKEN_PATH), SCOPES)
    except (ValueError, json.JSONDecodeError):
        return None  # corrupt or written by an older version; re-authorize


def _save_token(creds):
    config.ensure_config_dir()
    config.TOKEN_PATH.write_text(creds.to_json())
    try:
        config.TOKEN_PATH.chmod(0o600)
    except OSError:
        pass  # filesystems without POSIX permissions


def has_token():
    """True if a usable login already exists, without hitting the network."""
    creds = _load_token()
    return bool(creds and (creds.valid or creds.refresh_token))


def credentials_source():
    """Human-readable description of where OAuth credentials are coming from."""
    if _client_config():
        return "GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET from .env"
    cred_file = config.credentials_file()
    return str(cred_file) if cred_file else "not configured"


def load_credentials(allow_browser=False):
    """Return valid credentials, opening a browser only if allow_browser is set.

    The MCP server always passes allow_browser=False: it runs headless under
    Claude, where a blocking browser prompt would just hang the tool call.
    """
    creds = _load_token()

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except GoogleAuthError as exc:
            raise AuthError(_stale_token_message(exc)) from exc
        _save_token(creds)
        return creds

    if not allow_browser:
        raise AuthError(
            "Gmail is not authorized yet. Run `python authorize.py` once in a "
            "terminal to sign in, then try again."
        )

    creds = _build_flow().run_local_server(port=OAUTH_PORT)
    _save_token(creds)
    return creds


def get_service(allow_browser=False):
    """An authenticated Gmail API client.

    build() is the first call that actually spends the token, so a revoked or
    mistyped client surfaces here rather than at load_credentials().
    """
    creds = load_credentials(allow_browser)
    try:
        return build("gmail", "v1", credentials=creds, cache_discovery=False)
    except GoogleAuthError as exc:
        raise AuthError(_stale_token_message(exc)) from exc
