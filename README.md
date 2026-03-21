# 📧 Email Automation System

**Automated Job Application Email Sender with AI-Generated Content**

Google Sheets/Manual Input → Gemini AI → Gmail API → Personalized Emails

---

## 🎯 What This Does

Ye system automatically job application emails bhejta hai with:
- ✅ AI-generated personalized content (Gemini Flash 2.5)
- ✅ Google Sheets ya manual input support
- ✅ Job position-specific emails
- ✅ Custom resume links per recipient
- ✅ Automatic rate limiting (spam avoid)
- ✅ Complete web interface (no terminal needed)
- ✅ Fallback templates (if AI fails)
- ✅ Full logging and tracking

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment

`.env` file edit karke ye 4 values bharo:

```env
GEMINI_API_KEY=your_api_key_here
RESUME_LINK=https://your-resume-link.com
YOUR_NAME=Your Full Name
YOUR_EMAIL=your.email@gmail.com
```

**Gemini API Key kahan se:** https://aistudio.google.com/app/apikey

### Step 3: Start Application

```bash
python app.py
```

Browser mein kholo: **http://localhost:5000**

---

## 🔐 Complete Google Setup Guide

### Part 1: Google Cloud Console Setup (Gmail API)

#### 1.1 Create Project

1. **Google Cloud Console** kholo: https://console.cloud.google.com
2. Top bar mein **"Select a project"** click karo
3. **"New Project"** click karo
4. Project name do (e.g., "Email Automation")
5. **"Create"** click karo
6. Project select karo (top bar se)

#### 1.2 Enable Gmail API

1. Left sidebar → **"APIs & Services"** → **"Library"**
2. Search bar mein type karo: **"Gmail API"**
3. **Gmail API** click karo
4. **"Enable"** button click karo
5. Wait for activation (few seconds)

#### 1.3 Configure OAuth Consent Screen

1. Left sidebar → **"APIs & Services"** → **"OAuth consent screen"**
2. User Type: **"External"** select karo
3. **"Create"** click karo
4. Fill basic info:
   - **App name:** Email Automation (ya koi bhi naam)
   - **User support email:** Your email select karo
   - **Developer contact:** Your email enter karo
5. **"Save and Continue"** click karo
6. **Scopes page:** Skip karo (Save and Continue)
7. **Test users page:** Skip karo (Save and Continue)
8. **Summary:** Review karke **"Back to Dashboard"**

#### 1.4 Create Credentials (Most Important!)

1. Left sidebar → **"APIs & Services"** → **"Credentials"**
2. Top bar mein **"+ Create Credentials"**

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
