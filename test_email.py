"""Send a single test email to yourself.

    python test_email.py
"""
import sys

from core import config, gmail_auth, sent_log
from core.email_sender import EmailSender
from core.gemini_content import GeminiContentGenerator


def main():
    print("Email system test\n")

    missing = config.missing_profile_fields()
    if missing:
        print(f"Missing in .env: {', '.join(missing)}")
        return 1

    your_email = config.your_email()
    print(f"Test email will go to: {your_email}\n")

    service = gmail_auth.get_service(allow_browser=True)
    print("Gmail authenticated.")

    body = GeminiContentGenerator().generate_email_content(
        "Test User", "Test Company", config.resume_link(), config.your_name(), "Software Engineer"
    )

    print("\n" + "=" * 50)
    print("PREVIEW")
    print("=" * 50)
    print(body)
    print("=" * 50)

    if input("\nSend it? (yes/no): ").strip().lower() != "yes":
        print("Cancelled.")
        return 0

    result = EmailSender(service, your_email).send(
        your_email, "Test: Email Automation System", body
    )
    sent_log.record([result])

    if result["success"]:
        print(f"\nSent. Message ID: {result['message_id']}")
        print(f"Check your inbox: {your_email}")
        return 0

    print(f"\nFailed: {result['error']}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
