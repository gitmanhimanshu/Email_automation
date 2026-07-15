"""Sending mail through the Gmail API."""
import base64
from email.message import EmailMessage


def _encode(to, subject, body, sender, cc=None):
    message = EmailMessage()
    message["To"] = to
    message["Subject"] = subject
    if sender:
        message["From"] = sender
    if cc:
        message["Cc"] = cc
    message.set_content(body)
    return {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}


class EmailSender:
    def __init__(self, gmail_service, sender_email):
        self.service = gmail_service
        self.sender_email = sender_email

    def send(self, to, subject, body, cc=None):
        """Send one email. Returns a result dict rather than raising, so a bad
        address in a batch fails that row instead of the whole run."""
        try:
            payload = _encode(to, subject, body, self.sender_email, cc)
            sent = self.service.users().messages().send(userId="me", body=payload).execute()
            return {"success": True, "to": to, "subject": subject, "message_id": sent["id"]}
        except Exception as exc:
            return {"success": False, "to": to, "subject": subject, "error": str(exc)}

    # Kept for the older call sites that used send_email().
    send_email = send
