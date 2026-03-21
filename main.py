"""Main Email Automation Script"""
import os
import time
import json
from datetime import datetime
from dotenv import load_dotenv

from gmail_auth import GmailAuth
from gemini_content import GeminiContentGenerator
from email_sender import EmailSender
from sheets_reader import SheetsReader

# Load environment variables
load_dotenv()

class EmailAutomation:
    def __init__(self):
        self.resume_link = os.getenv('RESUME_LINK')
        self.your_name = os.getenv('YOUR_NAME')
        self.your_email = os.getenv('YOUR_EMAIL')
        self.email_delay = int(os.getenv('EMAIL_DELAY', 5))
        
        # Initialize components
        self.gmail_auth = GmailAuth(os.getenv('GMAIL_CREDENTIALS_PATH'))
        self.gemini = GeminiContentGenerator()
        
        # Authenticate Gmail
        gmail_service = self.gmail_auth.authenticate()
        self.email_sender = EmailSender(gmail_service, self.your_email)
        
        # Track sent emails
        self.sent_log = []
    
    def get_recipients_from_sheet(self):
        """Get recipients from Google Sheet"""
        sheets_creds = os.getenv('SHEETS_CREDENTIALS_PATH')
        sheet_name = os.getenv('SHEET_NAME')
        
        if not sheets_creds or not sheet_name:
            raise ValueError("Sheet credentials or name not configured")
        
        reader = SheetsReader(sheets_creds)
        records = reader.read_sheet(sheet_name)
        reader.validate_records(records)
        
        return records
    
    def get_recipients_manual(self):
        """Get recipients from manual list"""
        # You can modify this list or load from a JSON file
        return [
            {
                "name": "Rahul", 
                "email": "himanshu.prpwebs@gmail.com", 
                "company": "ABC Corp",
                "job_position": "Software Engineer",  # Optional
                "resume_link": None  # Optional - will use default from .env
            },
            {
                "name": "Priya", 
                "email": "hr2@example.com", 
                "company": "XYZ Ltd",
                "job_position": "Full Stack Developer",  # Optional
                "resume_link": None  # Optional
            },
        ]
    
    def send_bulk_emails(self, recipients, use_gemini=True):
        """Send emails to all recipients"""
        total = len(recipients)
        print(f"\n📧 Starting email campaign: {total} recipients\n")
        
        for i, recipient in enumerate(recipients, 1):
            name = recipient['name']
            email = recipient['email']
            company = recipient['company']
            job_position = recipient.get('job_position')
            resume_link = recipient.get('resume_link') or self.resume_link
            
            position_text = f" - {job_position}" if job_position else ""
            print(f"[{i}/{total}] Processing: {name} ({company}{position_text})")
            
            # Generate content
            if use_gemini:
                try:
                    body = self.gemini.generate_email_content(
                        name, company, resume_link, self.your_name, job_position
                    )
                    print(f"  ✅ Content generated via Gemini")
                except Exception as e:
                    print(f"  ⚠️ Gemini failed, using fallback: {e}")
                    body = self.gemini._fallback_template(
                        name, company, resume_link, self.your_name, job_position
                    )
            else:
                body = self.gemini._fallback_template(
                    name, company, resume_link, self.your_name, job_position
                )
            
            # Send email
            if job_position:
                subject = f"Application for {job_position} at {company}"
            else:
                subject = f"Application for Opportunities at {company}"
            
            result = self.email_sender.send_email(email, subject, body)
            
            # Log result
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'name': name,
                'email': email,
                'company': company,
                'success': result['success']
            }
            
            if result['success']:
                print(f"  ✅ Email sent successfully (ID: {result['message_id']})")
                log_entry['message_id'] = result['message_id']
            else:
                print(f"  ❌ Failed: {result['error']}")
                log_entry['error'] = result['error']
            
            self.sent_log.append(log_entry)
            
            # Rate limiting
            if i < total:
                print(f"  ⏳ Waiting {self.email_delay} seconds...\n")
                time.sleep(self.email_delay)
        
        self._save_log()
        self._print_summary()
    

    
    def _save_log(self):
        """Save sent emails log"""
        with open('sent_emails.json', 'w') as f:
            json.dump(self.sent_log, f, indent=2)
        print(f"\n📝 Log saved to sent_emails.json")
    
    def _print_summary(self):
        """Print campaign summary"""
        total = len(self.sent_log)
        success = sum(1 for log in self.sent_log if log['success'])
        failed = total - success
        
        print(f"\n{'='*50}")
        print(f"📊 CAMPAIGN SUMMARY")
        print(f"{'='*50}")
        print(f"Total emails: {total}")
        print(f"✅ Successful: {success}")
        print(f"❌ Failed: {failed}")
        print(f"{'='*50}\n")

def main():
    """Main execution"""
    print("🚀 Email Automation System\n")
    
    # Initialize
    automation = EmailAutomation()
    
    # Choose input method
    print("Select input method:")
    print("1. Google Sheets (Public Sheet)")
    print("2. Manual list (edit in code)")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == '1':
        # Get sheet URL as input
        sheet_url = input("\n📊 Enter Google Sheet URL: ").strip()
        
        if not sheet_url:
            print("❌ No URL provided. Using URL from .env if available...")
            sheet_url = os.getenv('SHEET_URL')
        
        if not sheet_url:
            print("❌ No sheet URL found. Exiting.")
            return
        
        print(f"\n📊 Reading from Google Sheets...")
        reader = SheetsReader(sheet_url)
        records = reader.read_public_sheet()
        recipients = reader.validate_records(records)
    else:
        print("\n📝 Using manual recipient list...")
        recipients = automation.get_recipients_manual()
    
    print(f"Found {len(recipients)} recipients")
    
    # Show preview
    print("\n📋 Preview (first 3):")
    for i, r in enumerate(recipients[:3], 1):
        position = f" | Position: {r['job_position']}" if r.get('job_position') else ""
        resume = f" | Resume: {r['resume_link'][:30]}..." if r.get('resume_link') else ""
        print(f"  {i}. {r['name']} ({r['email']}) - {r['company']}{position}{resume}")
    
    # Confirm before sending
    confirm = input("\n⚠️ Ready to send emails? (yes/no): ").strip().lower()
    
    if confirm == 'yes':
        automation.send_bulk_emails(recipients, use_gemini=True)
    else:
        print("❌ Cancelled")

if __name__ == "__main__":
    main()
