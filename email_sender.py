"""Email Sending Module with Gmail API"""
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailSender:
    def __init__(self, gmail_service, your_email):
        self.service = gmail_service
        self.your_email = your_email
    
    def create_message(self, to, subject, body):
        """Create email message"""
        message = MIMEMultipart()
        message['to'] = to
        message['from'] = self.your_email
        message['subject'] = subject
        
        msg = MIMEText(body, 'plain')
        message.attach(msg)
        
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return {'raw': raw}
    
    def send_email(self, to, subject, body):
        """Send email via Gmail API"""
        try:
            message = self.create_message(to, subject, body)
            sent_message = self.service.users().messages().send(
                userId='me', 
                body=message
            ).execute()
            
            return {
                'success': True,
                'message_id': sent_message['id'],
                'to': to
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'to': to
            }
