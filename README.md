# 📧 Email Automation System

Google Sheets/Manual → Gemini AI → Gmail API से automated emails भेजने का complete system.

## 🎯 Features

- ✅ Google Sheets या manual list से recipients
- ✅ Gemini Flash 2.5 से AI-generated personalized content
- ✅ Gmail API से direct send (आपकी personal Gmail से)
- ✅ Automatic fallback अगर Gemini fail हो
- ✅ Rate limiting (spam avoid करने के लिए)
- ✅ Complete logging और tracking
- ✅ Environment variables से secure configuration

## 🔧 Setup Instructions

### Step 1: Google Cloud Console Setup

1. **Project बनाओ**
   - https://console.cloud.google.com पर जाओ
   - New Project बनाओ

2. **Gmail API Enable करो**
   - APIs & Services → Library
   - "Gmail API" search करो
   - Enable करो

3. **OAuth Consent Screen**
   - APIs & Services → OAuth consent screen
   - External select करो
   - App name, email डालो
   - Save करो

4. **Credentials बनाओ**
   - APIs & Services → Credentials
   - Create Credentials → OAuth Client ID
   - Application type: Desktop App
   - Download JSON
   - File को `credentials.json` नाम से save करो (इस folder में)

### Step 2: Google Sheets Setup (Optional)

अगर Google Sheets use करना है:

1. **Service Account बनाओ**
   - APIs & Services → Credentials
   - Create Credentials → Service Account
   - Download JSON key
   - File को `sheets_creds.json` नाम से save करो

2. **Sheet Setup**
   - Google Sheets में नया sheet बनाओ
   - Columns: `name`, `email`, `company`
   - Service account email को sheet में Editor access दो

### Step 3: Gemini API Key

1. https://aistudio.google.com/app/apikey पर जाओ
2. API key generate करो
3. Copy करो (`.env` में use करेंगे)

### Step 4: Python Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env file और अपनी details डालो
```

### Step 5: Configure .env File

`.env` file edit करो:

```env
GMAIL_CREDENTIALS_PATH=credentials.json
GEMINI_API_KEY=your_actual_gemini_key
RESUME_LINK=https://your-resume-link.com
YOUR_NAME=Your Full Name
YOUR_EMAIL=your.email@gmail.com
EMAIL_DELAY=5

# If using sheets:
SHEETS_CREDENTIALS_PATH=sheets_creds.json
SHEET_NAME=HR Emails
```

## 🚀 Usage

### Run the script:

```bash
python main.py
```

### Script आपसे पूछेगा:
1. Input method (Sheets या Manual)
2. Confirmation before sending

### Manual list edit करने के लिए:

`main.py` में `get_recipients_manual()` function edit करो:

```python
def get_recipients_manual(self):
    return [
        {"name": "Name1", "email": "email1@example.com", "company": "Company1"},
        {"name": "Name2", "email": "email2@example.com", "company": "Company2"},
    ]
```

## 📊 Output

- Console में real-time progress
- `sent_emails.json` में complete log
- Success/failure tracking

## ⚠️ Important Notes

### Rate Limits:
- Personal Gmail: ~100-300 emails/day safe limit
- `EMAIL_DELAY` को 5-10 seconds रखो

### Security:
- `credentials.json` और `sheets_creds.json` को NEVER commit करो
- `.gitignore` already configured है

### Gemini Fallback:
- अगर Gemini API fail हो, automatic fallback template use होगा
- Emails भेजना continue रहेगा

## 🔍 Testing

पहले test email भेजो:

```python
# main.py में temporary change:
recipients = [{"name": "Test", "email": "your-test@email.com", "company": "Test Co"}]
```

## 📝 Logs

`sent_emails.json` में देखो:
- Timestamp
- Recipient details
- Success/failure status
- Message IDs

## 🛠️ Troubleshooting

**"credentials.json not found"**
→ Google Cloud Console से download करो

**"GEMINI_API_KEY not found"**
→ `.env` file check करो

**"Permission denied" (Gmail)**
→ First run पर browser में login करो

**"Sheet not found"**
→ Service account को sheet में access दो

## 📚 File Structure

```
.
├── main.py                 # Main script
├── gmail_auth.py          # Gmail authentication
├── gemini_content.py      # AI content generation
├── email_sender.py        # Email sending logic
├── sheets_reader.py       # Google Sheets reader
├── requirements.txt       # Dependencies
├── .env                   # Configuration (create from .env.example)
├── .env.example          # Example configuration
└── README.md             # This file
```
