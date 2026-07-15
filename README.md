# 📧 Email Automation System

**Automated Job Application Email Sender with AI-Generated Content**

✨ **Ye project tumhari personal Gmail se HR ko automatic emails bhejta hai**  
📊 **HR ki sheet ya manual entry ke madhyam se**

---

## 🔀 Teen Tarike — apna chuno

| | **Standalone** | **Local MCP** | **Hosted MCP** |
|---|---|---|---|
| Email kaun likhta hai | Gemini | Claude | Claude |
| Kaun use kar sakta hai | Sirf tum | Sirf tum | **Koi bhi user** |
| User ko install karna padta hai | Haan | Haan | **Kuch nahi** |
| Chalane ka tarika | `python app.py` | Claude Desktop | claude.ai / ChatGPT |
| Google setup | User khud karta hai | User khud karta hai | **Tum ek baar** |
| Guide | Neeche ⬇️ | [MCP_SETUP.md](MCP_SETUP.md) | [remote/README.md](remote/README.md) |

**Setup docs:**
[GOOGLE_SETUP.md](GOOGLE_SETUP.md) — Google Cloud ka pura walkthrough (scopes, audience, client) ·
[NGROK_CHATGPT.md](NGROK_CHATGPT.md) — ngrok se ChatGPT/claude.ai mein test karo ·
[RENDER.md](RENDER.md) — Render pe deploy

**Standalone** mein koi model loop mein nahi hota, isliye Gemini content likhta hai.

**MCP** modes mein Claude khud likhta hai — usse tumhari actual skills aur conversation
ka context pata hota hai, jo ek fixed prompt ke paas kabhi nahi hoga. Isliye MCP mein
Gemini use hi nahi hota.

**Hosted** wala asli product hai: user claude.ai pe connector add karta hai,
"Sign in with Google" karta hai, aur bolta hai *"hiring companies dhundo aur apply karo"* —
Claude research karta hai, likhta hai, server bhejta hai.

---

## 🔒 Ek rule jo kabhi mat todna

Ye app sirf **`gmail.send`** scope maangta hai. `gmail.readonly` add karne ka man kare
to yaad rakhna:

| Scope | Tier | Cost |
|---|---|---|
| `gmail.send` | Sensitive | Free verification |
| `gmail.readonly` / `compose` / `modify` | **Restricted** | **$15k-75k CASA audit, har saal** |

Ek line ka farak, lakhon rupaye ka. ([Google docs](https://developers.google.com/workspace/gmail/api/auth/scopes))

---

## 🔄 How It Works (Simple Flow)

### 📝 Imagine Karo:

```
👤 You (Job Seeker)
    ↓
📊 HR Contacts ki List (Google Sheet ya Manual)
    ↓
🤖 AI (Gemini) - Har HR ke liye personalized email likhta hai
    ↓
📧 Your Gmail - Automatically emails bhejta hai
    ↓
✅ HR ko email milta hai (professional & personalized)
```

---

## 🎬 Real-Life Example

### Scenario: Tumhe 50 companies mein apply karna hai

**Without This Tool:**
- ❌ Har email manually likhna padega (2-3 min per email)
- ❌ 50 emails = 2-3 hours ka kaam
- ❌ Copy-paste se generic lagega
- ❌ Mistakes ho sakte hain

**With This Tool:**
- ✅ Ek baar setup karo (5 minutes)
- ✅ HR list paste karo (Google Sheet ya manual)
- ✅ Click "Send" - bas!
- ✅ 50 personalized emails = 5 minutes
- ✅ Har email unique aur professional

---

## 🎯 Step-by-Step Journey

### 1️⃣ **Setup (One Time - 5 minutes)**

```
Install → Configure → Authenticate
   ↓         ↓            ↓
  pip     .env file    Gmail login
```

**Kya karna hai:**
- Dependencies install karo
- Apni details bharo (.env file)
- Gmail se connect karo (browser mein login)

**Result:** System ready! ✅

---

### 2️⃣ **Add HR Contacts (Every Time)**

**Option A: Google Sheet** 📊
```
Create Sheet → Make Public → Copy URL → Paste in App
```

**Option B: Manual Entry** ✍️
```
Open App → Add Recipient → Fill Details → Save
```

**Data Format:**
- Name: Rahul Kumar
- Email: hr@company.com
- Company: ABC Corp
- Position: Software Engineer (optional)
- Resume: Your custom link (optional)

---

### 3️⃣ **AI Magic Happens** 🤖

```
Your Data → Gemini AI → Personalized Email
```

**Example:**

**Input:**
- Name: Priya
- Company: XYZ Tech
- Position: Full Stack Developer

**AI Output:**
```
Hi Priya,

I am writing to express my interest in the Full Stack Developer 
position at XYZ Tech. With my experience in React, Node.js, and 
cloud technologies, I believe I would be a great fit for your team.

Please find my resume here: [your-link]

Looking forward to discussing this opportunity.

Best regards,
Himanshu Yadav
```

---

### 4️⃣ **Send Emails** 📤

```
Review → Click Send → Sit Back & Relax
```

**What Happens:**
- Email 1 → Send → Wait 5 seconds
- Email 2 → Send → Wait 5 seconds
- Email 3 → Send → Wait 5 seconds
- ...and so on

**Why Wait?** Gmail ko lagta hai tum human ho, bot nahi! 😊

---

### 5️⃣ **Track Results** 📊

```
sent_emails.json
    ↓
✅ Rahul (ABC Corp) - Sent successfully
✅ Priya (XYZ Tech) - Sent successfully
❌ Amit (Tech Inc) - Failed (invalid email)
```

**You Get:**
- Total emails sent
- Success count
- Failed count (with reasons)
- Message IDs for tracking

---

## 💡 Real Use Cases

### Use Case 1: Mass Job Applications
```
50 companies ki list → 1 click → 50 personalized emails
Time saved: 2-3 hours → 5 minutes
```

### Use Case 2: Different Positions
```
10 companies - Software Engineer
15 companies - Full Stack Developer
20 companies - Backend Developer

Each gets position-specific email! 🎯
```

### Use Case 3: Custom Resumes
```
Startup companies → Startup-focused resume
Corporate companies → Corporate resume
Each recipient gets relevant resume link!
```

---

## 🎨 Visual Workflow

```
┌─────────────────────────────────────────────────────────┐
│  YOU                                                    │
│  ├─ Open browser: http://localhost:5000                │
│  ├─ Fill your details (name, email, resume)            │
│  └─ Save configuration                                 │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  ADD HR CONTACTS                                        │
│  ├─ Option 1: Paste Google Sheet URL                   │
│  │   └─ Click "Load" → Auto-fills all recipients       │
│  │                                                      │
│  └─ Option 2: Manual Entry                             │
│      └─ Click "Add" → Fill form → Repeat               │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  PREVIEW (Optional)                                     │
│  └─ Test with sample name/company                      │
│      └─ See how email will look                        │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  SEND EMAILS                                            │
│  ├─ Click "Send All Emails"                            │
│  ├─ Confirm (yes/no)                                   │
│  └─ Watch progress in real-time                        │
│      ├─ [1/50] Sending to Rahul... ✅                  │
│      ├─ [2/50] Sending to Priya... ✅                  │
│      └─ [3/50] Sending to Amit... ✅                   │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  RESULTS                                                │
│  ├─ Browser: Success/Failure summary                   │
│  └─ File: sent_emails.json (complete log)              │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 Features

- ✅ **Web Interface** - No terminal commands needed
- ✅ **Google Sheets Support** - Public sheet se automatic data load
- ✅ **Manual Entry** - Browser mein directly recipients add karo
- ✅ **AI-Generated Content** - Gemini se personalized emails (model `.env` mein badal sakte ho)
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

`.env.example` ko `.env` naam se copy karke bharo:

```env
YOUR_NAME=Your Full Name
YOUR_EMAIL=your.email@gmail.com
RESUME_LINK=https://your-resume-link.com
EMAIL_DELAY=5

GOOGLE_CLIENT_ID=xxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxxx

GEMINI_API_KEY=your_api_key_here
```

**Google client ID/secret:** [Cloud Console](https://console.cloud.google.com/apis/credentials)
→ Gmail API enable karo → Create OAuth client ID → type **Desktop app**.
(Ya JSON download karke `cred.json` naam se project folder mein rakh do.)

**Gemini API Key:** https://aistudio.google.com/app/apikey

### Step 3: Gmail Login (ek baar)

```bash
python authorize.py
```

Browser khulega. Jis Gmail se bhejna hai usse login karo → Allow.

### Step 4: Start Web Interface

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
- Scope sirf `gmail.send` hai — ye app tumhara **inbox padh hi nahi sakta**
- `.env` aur `cred.json` `.gitignore` mein hain
- Token `~/.email_automation/token.json` mein, project folder se bahar

### Gemini Fallback:
- If API fails, uses professional template
- Same data (name, company, position, resume)
- Emails continue sending
- No manual intervention needed

### First Time Gmail Authentication:
- `python authorize.py` chalao
- Browser khulega, login karo, "Allow" click karo
- Token save ho jaayega — next time automatic
- Teeno modes (CLI, web, MCP) yahi ek login share karte hain

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
├── .env                    # Your configuration (never commit)
├── core/                   # Shared by all three entry points
│   ├── config.py           #   Settings + file locations
│   ├── gmail_auth.py       #   OAuth (send-only scope)
│   ├── email_sender.py     #   Gmail send
│   ├── sheets_reader.py    #   Public sheet reader
│   ├── gemini_content.py   #   AI content (standalone mode only)
│   └── sent_log.py         #   Send history + dedupe
├── app.py                  # Standalone: Flask web server
├── main.py                 # Standalone: CLI
├── test_email.py           # Send yourself one test email
├── authorize.py            # One-time Gmail login
├── mcp_server/
│   └── server.py           # MCP server for Claude
├── requirements.txt
└── templates/
    └── index.html          # Web interface
```

Ye files project folder mein **nahi** banti — `~/.email_automation/` mein banti hain,
taaki teeno modes ek hi login share karein aur kuch secret galti se commit na ho:

```
~/.email_automation/
├── token.json          # Gmail login
└── sent_emails.json    # Har bheji hui email ka record
```

---

## 🆘 Troubleshooting

**"No Google OAuth credentials found"**
→ `.env` mein `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` bharo, ya `cred.json` rakho

**"Gmail is not authorized"**
→ `python authorize.py` chalao

**"Google did not recognize the OAuth client"**
→ Client ID/secret galat hai ya Cloud Console se delete ho gaya
→ Theek karke `python authorize.py` dobara chalao

**"GEMINI_API_KEY not found"**
→ Add to `.env` file from https://aistudio.google.com/app/apikey
→ (MCP mode mein iski zaroorat nahi — Claude khud likhta hai)

**"The sheet is not public"**
→ Sheet → Share → "Anyone with the link" → Viewer

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

- **Send-only scope.** Ye app `gmail.send` maangta hai aur bas. Inbox padhna
  technically possible hi nahi hai — token leak bhi ho jaye to koi tumhari
  mails nahi dekh sakta.
- Har user apni khud ki Google client ID/secret use karta hai — koi shared credential nahi
- `.env` aur `cred.json` `.gitignore` mein hain
- Token project folder se bahar (`~/.email_automation/token.json`), file permissions `600`
- Code mein koi credential hardcoded nahi

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
