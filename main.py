"""CLI interface — the standalone mode, with Gemini writing the emails.

    python main.py
"""
import sys
import time

from core import config, gmail_auth, sent_log
from core.email_sender import EmailSender
from core.gemini_content import GeminiContentGenerator, subject_for
from core.sheets_reader import SheetsReader

# Edit this list if you want to send without a Google Sheet.
MANUAL_RECIPIENTS = [
    {
        "name": "Rahul",
        "email": "hr1@example.com",
        "company": "ABC Corp",
        "job_position": "Software Engineer",
        "resume_link": None,  # falls back to RESUME_LINK in .env
    },
    {
        "name": "Priya",
        "email": "hr2@example.com",
        "company": "XYZ Ltd",
        "job_position": "Full Stack Developer",
        "resume_link": None,
    },
]


class EmailAutomation:
    def __init__(self):
        self.gemini = GeminiContentGenerator()
        self.sender = EmailSender(
            gmail_auth.get_service(allow_browser=True), config.your_email()
        )
        self.delay = config.email_delay()

    def send_bulk_emails(self, recipients, use_gemini=True):
        total = len(recipients)
        print(f"\nStarting: {total} recipients\n")

        results = []
        for index, recipient in enumerate(recipients, 1):
            name, company = recipient["name"], recipient["company"]
            job_position = recipient.get("job_position")
            resume_link = recipient.get("resume_link") or config.resume_link()

            suffix = f" - {job_position}" if job_position else ""
            print(f"[{index}/{total}] {name} ({company}{suffix})")

            if use_gemini:
                body = self.gemini.generate_email_content(
                    name, company, resume_link, config.your_name(), job_position
                )
            else:
                body = self.gemini._fallback_template(
                    name, company, resume_link, config.your_name(), job_position
                )

            result = self.sender.send(
                recipient["email"], subject_for(company, job_position), body
            )
            results.append({**result, "name": name, "company": company})

            if result["success"]:
                print(f"  sent (id: {result['message_id']})")
            else:
                print(f"  failed: {result['error']}")

            if index < total and self.delay:
                print(f"  waiting {self.delay}s...\n")
                time.sleep(self.delay)

        sent_log.record(results)
        self._print_summary(results)

    def _print_summary(self, results):
        succeeded = sum(1 for r in results if r["success"])
        print(f"\n{'=' * 50}")
        print("SUMMARY")
        print(f"{'=' * 50}")
        print(f"Total:  {len(results)}")
        print(f"Sent:   {succeeded}")
        print(f"Failed: {len(results) - succeeded}")
        print(f"Log:    {config.SENT_LOG_PATH}")
        print(f"{'=' * 50}\n")


def main():
    print("Email Automation\n")

    missing = config.missing_profile_fields()
    if missing:
        print(f"Missing in .env: {', '.join(missing)}")
        return 1

    print("Select input method:")
    print("  1. Google Sheet (public)")
    print("  2. Manual list (edit MANUAL_RECIPIENTS in main.py)")
    choice = input("\nChoice (1 or 2): ").strip()

    if choice == "1":
        sheet_url = input("\nGoogle Sheet URL: ").strip()
        if not sheet_url:
            print("No URL provided.")
            return 1
        reader = SheetsReader(sheet_url)
        recipients = reader.validate_records(reader.read_public_sheet())
    else:
        recipients = MANUAL_RECIPIENTS

    print(f"\nFound {len(recipients)} recipients. First few:")
    for index, recipient in enumerate(recipients[:3], 1):
        position = f" | {recipient['job_position']}" if recipient.get("job_position") else ""
        print(f"  {index}. {recipient['name']} <{recipient['email']}> - {recipient['company']}{position}")

    if input("\nSend emails? (yes/no): ").strip().lower() != "yes":
        print("Cancelled.")
        return 0

    EmailAutomation().send_bulk_emails(recipients, use_gemini=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
