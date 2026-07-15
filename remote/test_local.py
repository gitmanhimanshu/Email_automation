"""End-to-end test of the hosted server on localhost, against your own Gmail.

Drives the real thing: real Google consent, real Gmail send. The only shortcut
is that the server is on localhost instead of a deployed domain.

    Terminal 1:  python -m remote.server
    Terminal 2:  python -m remote.test_local

A browser opens for Google sign-in. The test email goes to your own address, so
nothing reaches a stranger.
"""
import asyncio
import json
import sys

from fastmcp import Client

SERVER_URL = "http://localhost:8000/mcp"


def show(title, payload):
    print(f"\n--- {title} ---")
    print(json.dumps(payload, indent=2, default=str)[:900])


def unwrap(result):
    """Tool results come back wrapped; dig out the dict."""
    data = getattr(result, "data", None)
    if data is not None:
        return data
    content = getattr(result, "content", None)
    if content:
        text = getattr(content[0], "text", None)
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"raw": text}
    return {"raw": str(result)}


async def main():
    print("Connecting to", SERVER_URL)
    print("A browser will open for Google sign-in.\n")

    async with Client(SERVER_URL, auth="oauth") as client:
        tools = await client.list_tools()
        print("Connected. Tools:", ", ".join(t.name for t in tools))

        profile = unwrap(await client.call_tool("get_my_profile", {}))
        show("get_my_profile", profile)

        my_email = profile.get("email")
        if not my_email:
            print("\nCould not read your email from the token. Check the openid and")
            print("userinfo.email scopes in remote/config.py.")
            return 1

        # The resume gate should block a send before a link is saved.
        blocked = unwrap(
            await client.call_tool(
                "send_application",
                {
                    "to": my_email,
                    "subject": "should not send",
                    "body": "gate test",
                    "company": "Test",
                    "source_url": "https://example.com/careers",
                },
            )
        )
        if blocked.get("success"):
            print("\nPROBLEM: the resume gate did not block this send.")
            return 1
        print(f"\nResume gate works — send refused: {blocked.get('needs')}")

        role = unwrap(await client.call_tool("set_role", {"role": "job_seeker"}))
        show("set_role", role)
        if not role.get("success"):
            print("\nPROBLEM: set_role failed.")
            return 1

        link = input("\nYour resume link (public Drive/Dropbox URL): ").strip()
        saved = unwrap(await client.call_tool("save_link", {"link": link}))
        show("save_link", saved)
        if not saved.get("success"):
            print("\nFix the link's sharing settings and run this again.")
            return 1

        checks = unwrap(
            await client.call_tool(
                "verify_hr_emails",
                {
                    "candidates": [
                        {
                            "email": my_email,
                            "company": "Yourself",
                            "source_url": "https://example.com/careers",
                        },
                        {
                            "email": "hr@this-domain-does-not-exist-9z8y7x.com",
                            "company": "Fake Co",
                            "source_url": "https://example.com/careers",
                        },
                        {
                            "email": "someone@bigcompany.com",
                            "company": "Big Company",
                            "source_url": "guessed from their naming pattern",
                        },
                    ]
                },
            )
        )
        show("verify_hr_emails (1 real, 2 that must be rejected)", checks)
        if checks.get("rejected") != 2:
            print("\nPROBLEM: the email guard should have rejected exactly 2.")
            return 1

        if input(f"\nSend a real test email to {my_email}? (yes/no): ").strip().lower() != "yes":
            print("Stopped before sending. Everything up to the send works.")
            return 0

        sent = unwrap(
            await client.call_tool(
                "send_application",
                {
                    "to": my_email,
                    "subject": "Test: hosted MCP server",
                    "body": (
                        "This is a test from your own hosted MCP server.\n\n"
                        "If you are reading this in your inbox, the whole chain works: "
                        "OAuth, identity, verification, and Gmail send."
                    ),
                    "company": "Yourself",
                    "source_url": "https://example.com/careers",
                },
            )
        )
        show("send_application", sent)

        if sent.get("success"):
            print(f"\nSent. Check your inbox: {my_email}")
            print("The resume link should be appended at the bottom.")
        else:
            print(f"\nFailed: {sent.get('error')}")
            return 1

        show("get_sent_history", unwrap(await client.call_tool("get_sent_history", {"limit": 5})))
        return 0


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        sys.exit(130)
