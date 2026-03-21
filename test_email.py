"""Quick test script to send a single test email"""
import os
from dotenv import load_dotenv
from gmail_auth import GmailAuth
from gemini_content import GeminiContentGenerator
from email_sender import EmailSender

load_dotenv()

def test_single_email():
    """Send a test email to yourself"""
    print("🧪 Testing Email System\n")
    
    # Get your email
    your_email = os.getenv('YOUR_EMAIL')
    your_name = os.getenv('YOUR_NAME')
    resume_link = os.getenv('RESUME_LINK')
    
    # Test recipient (send to yourself)
    test_recipient = {
        'name': 'Test User',
        'email': your_email,  # Sending to yourself
        'company': 'Test Company'
    }
    
    print(f"📧 Sending test email to: {your_email}\n")
    
    # Authenticate Gmail
    print("🔐 Authenticating Gmail...")
    gmail_auth = GmailAuth(os.getenv('GMAIL_CREDENTIALS_PATH'))
    gmail_service = gmail_auth.authenticate()
    print("✅ Gmail authenticated\n")
    
    # Initialize Gemini
    print("🤖 Initializing Gemini...")
    gemini = GeminiContentGenerator()
    print("✅ Gemini ready\n")
    
    # Generate content
    print("✍️ Generating email content...")
    body = gemini.generate_email_content(
        test_recipient['name'],
        test_recipient['company'],
        resume_link,
        your_name
    )
    print("✅ Content generated\n")
    print("="*50)
    print("EMAIL PREVIEW:")
    print("="*50)
    print(body)
    print("="*50)
    
    # Send email
    confirm = input("\n📤 Send this test email? (yes/no): ").strip().lower()
    
    if confirm == 'yes':
        sender = EmailSender(gmail_service, your_email)
        result = sender.send_email(
            test_recipient['email'],
            f"Test: Application for {test_recipient['company']}",
            body
        )
        
        if result['success']:
            print(f"\n✅ Test email sent successfully!")
            print(f"Message ID: {result['message_id']}")
            print(f"\n📬 Check your inbox: {your_email}")
        else:
            print(f"\n❌ Failed to send: {result['error']}")
    else:
        print("\n❌ Test cancelled")

if __name__ == "__main__":
    test_single_email()
