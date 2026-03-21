"""Flask Web Interface for Email Automation"""
from flask import Flask, render_template, request, jsonify
import os
import json
from dotenv import load_dotenv, set_key
from gmail_auth import GmailAuth
from gemini_content import GeminiContentGenerator
from email_sender import EmailSender
import time

load_dotenv()

app = Flask(__name__)

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    return jsonify({
        'resume_link': os.getenv('RESUME_LINK', ''),
        'your_name': os.getenv('YOUR_NAME', ''),
        'your_email': os.getenv('YOUR_EMAIL', ''),
        'email_delay': os.getenv('EMAIL_DELAY', '5'),
        'gemini_configured': bool(os.getenv('GEMINI_API_KEY'))
    })

@app.route('/api/config', methods=['POST'])
def update_config():
    """Update configuration"""
    data = request.json
    
    try:
        if 'resume_link' in data:
            set_key('.env', 'RESUME_LINK', data['resume_link'])
        if 'your_name' in data:
            set_key('.env', 'YOUR_NAME', data['your_name'])
        if 'your_email' in data:
            set_key('.env', 'YOUR_EMAIL', data['your_email'])
        if 'email_delay' in data:
            set_key('.env', 'EMAIL_DELAY', str(data['email_delay']))
        if 'gemini_api_key' in data and data['gemini_api_key']:
            set_key('.env', 'GEMINI_API_KEY', data['gemini_api_key'])
        
        load_dotenv(override=True)
        return jsonify({'success': True, 'message': 'Configuration updated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/preview', methods=['POST'])
def preview_email():
    """Preview email content"""
    data = request.json
    
    try:
        gemini = GeminiContentGenerator()
        job_position = data.get('job_position')
        resume_link = data.get('resume_link') or os.getenv('RESUME_LINK')
        
        body = gemini.generate_email_content(
            data['name'],
            data['company'],
            resume_link,
            os.getenv('YOUR_NAME'),
            job_position
        )
        
        if job_position:
            subject = f"Application for {job_position} at {data['company']}"
        else:
            subject = f"Application for Opportunities at {data['company']}"
        
        return jsonify({
            'success': True,
            'content': body,
            'subject': subject
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sheet/preview', methods=['POST'])
def preview_sheet():
    """Preview data from Google Sheet"""
    data = request.json
    sheet_url = data.get('sheet_url')
    
    if not sheet_url:
        return jsonify({'success': False, 'error': 'Sheet URL not provided'}), 400
    
    try:
        from sheets_reader import SheetsReader
        reader = SheetsReader(sheet_url)
        records = reader.read_public_sheet()
        normalized = reader.validate_records(records)
        
        return jsonify({
            'success': True,
            'count': len(normalized),
            'recipients': normalized
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/send', methods=['POST'])
def send_emails():
    """Send emails to recipients"""
    data = request.json
    recipients = data.get('recipients', [])
    
    if not recipients:
        return jsonify({'success': False, 'error': 'No recipients provided'}), 400
    
    try:
        # Authenticate Gmail
        gmail_auth = GmailAuth()
        gmail_service = gmail_auth.authenticate()
        email_sender = EmailSender(gmail_service, os.getenv('YOUR_EMAIL'))
        
        # Initialize Gemini
        gemini = GeminiContentGenerator()
        
        results = []
        
        for recipient in recipients:
            job_position = recipient.get('job_position')
            resume_link = recipient.get('resume_link') or os.getenv('RESUME_LINK')
            
            # Generate content
            body = gemini.generate_email_content(
                recipient['name'],
                recipient['company'],
                resume_link,
                os.getenv('YOUR_NAME'),
                job_position
            )
            
            # Send email
            if job_position:
                subject = f"Application for {job_position} at {recipient['company']}"
            else:
                subject = f"Application for Opportunities at {recipient['company']}"
            
            result = email_sender.send_email(recipient['email'], subject, body)
            
            results.append({
                'name': recipient['name'],
                'email': recipient['email'],
                'company': recipient['company'],
                'success': result['success'],
                'message_id': result.get('message_id'),
                'error': result.get('error')
            })
            
            # Rate limiting
            time.sleep(int(os.getenv('EMAIL_DELAY', 5)))
        
        # Save log
        with open('sent_emails.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        success_count = sum(1 for r in results if r['success'])
        
        return jsonify({
            'success': True,
            'total': len(results),
            'successful': success_count,
            'failed': len(results) - success_count,
            'results': results
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/test', methods=['POST'])
def test_email():
    """Send a test email to yourself"""
    try:
        your_email = os.getenv('YOUR_EMAIL')
        
        # Authenticate Gmail
        gmail_auth = GmailAuth(os.getenv('GMAIL_CREDENTIALS_PATH'))
        gmail_service = gmail_auth.authenticate()
        email_sender = EmailSender(gmail_service, your_email)
        
        # Generate test content
        gemini = GeminiContentGenerator()
        body = gemini.generate_email_content(
            "Test User",
            "Test Company",
            os.getenv('RESUME_LINK'),
            os.getenv('YOUR_NAME'),
            "Software Engineer"  # Test with job position
        )
        
        # Send to yourself
        result = email_sender.send_email(
            your_email,
            "Test: Email Automation System",
            body
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': f'Test email sent to {your_email}',
                'content': body
            })
        else:
            return jsonify({'success': False, 'error': result['error']}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
