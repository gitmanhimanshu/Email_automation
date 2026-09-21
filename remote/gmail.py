"""Sending mail with the caller's Google access token.

The OAuth proxy hands us a live access token per request, so nothing is stored
and nothing is refreshed here.
"""
import base64
from email.message import EmailMessage

import httpx
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


def service_for(access_token):
    return build(
        "gmail",
        "v1",
        credentials=Credentials(token=access_token),
        cache_discovery=False,
    )


async def fetch_identity(access_token):
    """The signed-in user's sub/email/name.

    gmail.send alone cannot call users.getProfile, so identity comes from the
    OpenID userinfo endpoint (covered by the openid + userinfo.email scopes).
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}
        )
        response.raise_for_status()
        data = response.json()

    return {
        "sub": data.get("sub"),
        "email": data.get("email"),
        "name": data.get("name"),
    }


def build_message(to, subject, body, sender, cc=None):
    message = EmailMessage()
    message["To"] = to
    message["Subject"] = subject
    if sender:
        message["From"] = sender
    if cc:
        message["Cc"] = cc
        
    text_footer = "\n\n--\n🚀 Powered by Setu (https://setu.mimanasa.online)\n👨‍💻 Developed by Himanshu Yadav | Email: himanshuyada70@gmail.com"
    
    html_body = body.replace("\n", "<br>")
    
    html_footer = """
<br><br>
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 13px; color: #555; border-top: 1px solid #eee; padding-top: 15px; margin-top: 20px;">
  <table cellpadding="0" cellspacing="0" border="0" style="width: 100%;">
    <tr>
      <td style="width: 30px; vertical-align: top;">
        <img src="https://setu.mimanasa.online/_next/image?url=%2Flogo.png&amp;w=64&amp;q=75" alt="Setu" width="20" height="20" style="display: block; border-radius: 4px; background-color: #f0f0f0;">
      </td>
      <td style="vertical-align: top; line-height: 1.4;">
        <span style="font-weight: 600; color: #333;">Powered by <a href="https://setu.mimanasa.online" style="color: #2563eb; text-decoration: none;">Setu</a></span><br>
        Automated with precision • <span style="color: #666;">Developed by <strong>Himanshu Yadav</strong> (<a href="mailto:himanshuyada70@gmail.com" style="color: #666; text-decoration: none;">himanshuyada70@gmail.com</a>)</span>
      </td>
    </tr>
  </table>
</div>
"""
    
    message.set_content(body + text_footer)
    message.add_alternative(html_body + html_footer, subtype='html')
    
    return {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}


def send(access_token, to, subject, body, sender=None, cc=None):
    """Send one email. Failures come back as data so one bad row in a batch
    does not abort the rest."""
    try:
        payload = build_message(to, subject, body, sender, cc)
        sent = (
            service_for(access_token)
            .users()
            .messages()
            .send(userId="me", body=payload)
            .execute()
        )
        return {"success": True, "to": to, "subject": subject, "message_id": sent["id"]}
    except Exception as exc:
        return {"success": False, "to": to, "subject": subject, "error": str(exc)}
