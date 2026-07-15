"""One-time Gmail sign-in. Run this once before using the MCP server.

The MCP server cannot do this itself: it runs headless under Claude, where a
blocking browser prompt would just hang the tool call.

    python authorize.py
"""
import sys

from core import config, gmail_auth


def main():
    print("Gmail authorization\n")
    print(f"  Credentials : {gmail_auth.credentials_source()}")
    print(f"  Token file  : {config.TOKEN_PATH}")
    print(f"  Scope       : send only (this app cannot read your inbox)\n")

    if gmail_auth.credentials_source() == "not configured":
        print(
            "No Google OAuth credentials found.\n\n"
            "  1. Go to https://console.cloud.google.com/apis/credentials\n"
            "  2. Create an OAuth client ID of type 'Desktop app'\n"
            "  3. Put the client ID and secret in .env as GOOGLE_CLIENT_ID and\n"
            "     GOOGLE_CLIENT_SECRET (or download it and save as cred.json)\n"
        )
        return 1

    if gmail_auth.has_token():
        print("Already authorized.")
        if input("Sign in again? (yes/no): ").strip().lower() != "yes":
            return 0

    print("Opening your browser. Sign in with the Gmail account you want to send from.\n")
    try:
        gmail_auth.load_credentials(allow_browser=True)
    except gmail_auth.AuthError as exc:
        print(f"Failed: {exc}")
        return 1
    except Exception as exc:
        print(f"Failed: {exc}")
        return 1

    print(f"\nDone. Token saved to {config.TOKEN_PATH}")
    print("You can now use the MCP server from Claude.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
