# 📧 Email Automation System

**Automated Job Application Email Sender with AI-Generated Content**

Google Sheets/Manual Input → Gemini AI → Gmail API → Personalized Emails

✨ **Ye project tumhari personal Gmail se HR ko automatic emails bhejta hai**  
📊 **HR ki sheet ya manual entry ke madhyam se**

---

## 🔄 How It Works

### Step-by-Step Flow:

```
1. INPUT
   ├─ Google Sheets (Public URL) 
   │  └─ Columns: email, name, company, job_position, resume_link
   │
   └─ Manual Entry (Web Form)
      └─ Browser mein directly add karo

2. DATA EXTRACTION
   ├─ Sheet se CSV format mein data fetch
   ├─ Flexible column matching (email/mail, name/full name, etc.)
   └─ Normalize karo: name, email, company, position, resume

3. AUTHENTICATION
   ├─ Gmail API (cred.json se)
   │  └─ First time: Browser login → token.pickle save
   │  └─ Next time: Automatic authentication
   │
   └─ Gemini API (.env se)

4. CONTENT GENERATION
   ├─ Gemini AI se personalized email
   │  ├─ Job position ke according customized
   │  ├─ Company-specific content
   │  └─ Professional tone
   │
   └─ Fallback Template (if Gemini fails)
      └─ Same data use karke professional email

5. EMAIL SENDING
   ├─ Gmail API se send (your personal Gmail)
   ├─ Custom subject line (position-based)
   ├─ Rate limiting (5-10 sec delay)
   └─ Real-time progress tracking

6. LOGGING
   ├─ sent_emails.json mein save
   ├─ Timestamp, recipient details
   ├─ Success/failure status
   └─ Message IDs
```

### Example Flow:

```
HR Sheet URL Input
    ↓
Extract: Rahul | hr@abc.com | ABC Corp | Software Engineer | resume.com
    ↓
Gemini AI: "Hi Rahul, I'm interested in Software Engineer at ABC Corp..."
    ↓
Gmail API: Send from himanshuyada70@gmail.com
    ↓
Log: ✅ Sent successfully (Message ID: xyz123)
```

---

## 🎯 Features

- ✅ **Web Interface** - No terminal commands needed
- ✅ **Google Sheets Support** - Public sheet se automatic data load
- ✅ **Manual Entry** - Browser mein directly recipients add karo
- ✅ **AI-Generated Content** - Gemini Flash 2.5 se personalized emails
- ✅ **Job Position Based** - Har position ke liye customized email
- ✅ **Custom Resume Links** - Har recipient ka alag resume link
- ✅ **Automatic Fallback** - Gemini fail hone par template use hoga
- ✅ **Rate Limiting** - Spam avoid karne ke liye automatic delay
- ✅ **Complete Logging** - Har email ka record `sent_emails.json` mein
- ✅ **Secure** - Credentials safely managed

---

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Configure .env File

`.env` file edit karke ye 4 values bharo:

```env
GEMINI_API_KEY=your_api_key_here
RESUME_LINK=https://your-resume-link.com
YOUR_NAME=Your Full Name
YOUR_EMAIL=your.email@gmail.com
```

**Gemini API Key:** https://aistudio.google.com/app/apikey

### Step 3: Start Web Interface

```bash
python app.py
```

Browser mein kholo: **http://localhost:5000**

---

## 🎨 Web Interface Usage

### 1️⃣ Configuration Tab (⚙️)

Sabse pehle configuration save karo:
- Your Name
- Your Email
- Resume Link (default)
- Gemini API Key
- Email Delay (5 seconds recommended)

Click: **"Save Configuration"**

### 2️⃣ Recipients Tab (👥)

**Option A: Manual Entry**
- "Add Recipient" button click karo
- Fill: Name, Email, Company
- Optional: Job Position, Custom Resume Link
- Multiple recipients add kar sakte ho

**Option B: Google Sheets**
- "Google Sheets" tab click karo
- Public sheet URL paste karo
- Click: **"Load Recipients from Sheet"**
- Automatically manual tab mein load ho jayega

### 3️⃣ Preview Tab (👁️)

Email preview dekhne ke liye:
- Name aur Company enter karo
- Click: **"Generate Preview"**
- AI-generated email content dikhega

### 4️⃣ Send Tab (🚀)

Ready ho to:
- Click: **"Send All Emails"**
- Confirmation dialog aayega
- Progress real-time dikhega
- Results automatically save honge

---

## 📊 Google Sheet Format

**Sheet ko public karo:**
File → Share → Anyone with link can view

**Required Column:** `email`

**Optional Columns (flexible naming):**
- `name` / `Name` / `Full Name`
- `company` / `Company Name` / `Organization`
- `job_position` / `Position` / `Role` / `Job Title`
- `resume_link` / `Resume` / `CV Link`

**Example Sheet:**

| name  | email           | company  | job_position       | resume_link                |
|-------|-----------------|----------|-------------------|----------------------------|
| Rahul | hr1@example.com | ABC Corp | Software Engineer | https://resume1.com        |
| Priya | hr2@example.com | XYZ Ltd  | Full Stack Dev    |                            |
| Amit  | hr3@example.com | Tech Inc |                   | https://resume2.com        |

---

## 🔄 How It Works

### Input:
- **Manual:** Browser mein form fill karo
- **Sheet:** Public Google Sheet URL paste karo

### Processing:
1. Data extract (email, name, company, position, resume)
2. Gemini AI se personalized content generate
3. Fallback template (agar Gemini fail ho)
4. Gmail API se send

### Output:
- Real-time progress browser mein
- Complete log: `sent_emails.json`
- Success/failure tracking

---

## 📧 Email Customization

### With Job Position:
```
Subject: Application for Software Engineer at ABC Corp

Hi Rahul,

I am interested in the Software Engineer position at ABC Corp...
[AI-generated personalized content based on role]

Resume: https://your-resume.com
```

### Without Job Position:
```
Subject: Application for Opportunities at ABC Corp

Hi Rahul,

I am interested in exploring opportunities at ABC Corp...
[AI-generated general professional content]

Resume: https://your-resume.com
```

---

## ⚠️ Important Notes

### Rate Limiting:
- Default: 5 seconds between emails
- Recommended: 5-10 seconds
- Daily limit: ~100-300 emails (personal Gmail)

### Security:
- `cred.json` already in `.gitignore`
- Never commit credentials
- `token.pickle` auto-generated (also ignored)

### Gemini Fallback:
- If API fails, uses professional template
- Same data (name, company, position, resume)
- Emails continue sending
- No manual intervention needed

### First Time Gmail Authentication:
- Browser automatically khulega
- Login karo (same email as cred.json)
- "Allow" click karo
- `token.pickle` file ban jayegi
- Next time automatic hoga

---

## 🧪 Testing

**Test single email to yourself:**
```bash
python test_email.py
```

Ya web interface mein **"Send Test Email"** button use karo.

---

## 📁 File Structure

```
.
├── cred.json              # Gmail credentials (from Google Cloud)
├── .env                   # Your configuration
├── app.py                 # Flask web server
├── gmail_auth.py          # Gmail authentication
├── gemini_content.py      # AI content generation
├── email_sender.py        # Email sending logic
├── sheets_reader.py       # Public sheet reader
├── main.py                # CLI interface (optional)
├── test_email.py          # Test script
├── requirements.txt       # Dependencies
└── templates/
    └── index.html         # Web interface
```

---

## 🆘 Troubleshooting

**"cred.json not found"**
→ Download from Google Cloud Console (OAuth Client ID)

**"GEMINI_API_KEY not found"**
→ Add to `.env` file from https://aistudio.google.com/app/apikey

**"Sheet not accessible"**
→ Make sheet public: File → Share → Anyone with link can view

**"Gmail authentication failed"**
→ Use same email as in cred.json
→ Allow access in browser popup

**"Gemini API fails"**
→ System automatically uses fallback template
→ Emails will still send with professional content

**"Port 5000 already in use"**
→ Change port in `app.py`: `app.run(port=5001)`

---

## 💡 Pro Tips

1. **Test First:** Always send test email before bulk sending
2. **Preview:** Check email preview for each type of recipient
3. **Sheet URL:** Copy URL directly from browser address bar
4. **Job Position:** Agar position specify karo to email zyada targeted hoga
5. **Custom Resume:** Different positions ke liye different resume links use kar sakte ho
6. **Rate Limit:** Agar zyada emails bhejne hain to delay 8-10 seconds rakho

---

## 📈 Best Practices

- Start with 5-10 test emails
- Check spam folder initially
- Use professional email content
- Don't send more than 100 emails/day
- Keep delay between 5-10 seconds
- Monitor `sent_emails.json` for tracking

---

## 🔐 Security

- All credentials in `.gitignore`
- Never commit `cred.json` or `.env`
- `token.pickle` auto-generated and ignored
- API keys stored in environment variables
- No credentials in code

---

## 📞 Support

For issues or questions:
1. Check `.env` configuration
2. Verify `cred.json` exists
3. Test with single email first
4. Check `sent_emails.json` for logs
5. Review browser console for errors

---

## 🎉 Ready to Use!

```bash
python app.py
```

Open: **http://localhost:5000**

Happy emailing! 🚀
