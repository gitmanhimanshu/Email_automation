# ngrok se test karo — ChatGPT / claude.ai ke saath

Localhost pe server chal raha hai, par **ChatGPT aur claude.ai tumhare laptop tak
nahi pahunch sakte** — wo cloud pe hain. ngrok tumhare localhost ko ek public HTTPS
URL de deta hai, bina deploy kiye.

> ChatGPT **sirf remote HTTPS servers** support karta hai — local stdio wale nahi.
> Isliye ngrok yahan optional nahi, zaroori hai.

---

## Pehle jaan lo: ChatGPT ki requirements

| | |
|---|---|
| Plan | **Plus / Pro / Team / Enterprise** — Free pe custom connectors nahi chalte |
| Developer mode | **On karna padega** (default off hai) |
| Server | Remote HTTPS only |

Claude ke liye ye limits nahi hain — Claude Code to localhost pe bhi direct connect
kar leta hai, bina ngrok ke.

---

## 1. ngrok install

Download: **[ngrok.com/download](https://ngrok.com/download)**

**Windows:**
```bash
winget install ngrok
```
Ya zip download karke `ngrok.exe` kahin rakh do.

**Sign up karo** (free): [dashboard.ngrok.com/signup](https://dashboard.ngrok.com/signup)

**Authtoken lagao** — [dashboard.ngrok.com/get-started/your-authtoken](https://dashboard.ngrok.com/get-started/your-authtoken) se copy karke:

```bash
ngrok config add-authtoken <tumhara_token>
```

## 2. Static domain lo — ye step skip mat karna

ngrok free plan mein **ek static domain** milta hai. Ye bahut zaroori hai:

- **Bina static domain:** URL har restart pe badalta hai → har baar Google Console
  mein redirect URI update karo → har baar `.env` badlo → har baar server restart karo
- **Static domain ke saath:** URL kabhi nahi badalta → Console mein ek baar set karo → khatam

[dashboard.ngrok.com/domains](https://dashboard.ngrok.com/domains) → **Create Domain**
→ kuch aisa milega: `setu-himanshu.ngrok-free.app`

## 3. Google Console mein redirect URI add karo

[console.cloud.google.com/auth/clients](https://console.cloud.google.com/auth/clients)
→ apne client pe click → **Authorized redirect URIs** → **+ ADD URI**:

```
https://your-name.ngrok-free.app/auth/callback
```

`https` hai (ngrok hamesha HTTPS deta hai), `http` nahi.

> Purana `http://localhost:8000/auth/callback` **delete mat karo** — dono saath
> rakh sakte ho. Localhost testing bhi chalti rahegi.

**SAVE** dabao.

## 4. `.env` update karo

```env
PUBLIC_BASE_URL=https://your-name.ngrok-free.app
```

> Trailing slash mat lagana. Server isme `/auth/callback` jodta hai, aur Console
> wali URI se **exactly** match hona chahiye.

## 5. Chalao — do terminal

```bash
# Terminal 1 — server
python -m remote.server

# Terminal 2 — tunnel
ngrok http --url=your-name.ngrok-free.app 8000
```

ngrok ye dikhayega:
```
Forwarding    https://your-name.ngrok-free.app -> http://localhost:8000
```

**Check karo ki tunnel zinda hai:**
```bash
curl https://your-name.ngrok-free.app/.well-known/oauth-protected-resource/mcp
```

JSON aana chahiye jisme `authorization_servers` ho. Nahi aaya to aage mat badho —
ChatGPT ko bhi wahi error milega.

## 6. ChatGPT mein connect karo

**a. Developer mode on karo**
Settings → **Connectors** → **Advanced** → **Developer mode** → ON

*(Kuch versions mein: Settings → Security and login → Developer mode)*

**b. Connector add karo**
Settings → Connectors → **Create** / **+**

- Name: `Setu`
- MCP Server URL:
  ```
  https://your-name.ngrok-free.app/mcp
  ```
  ← `/mcp` lagana **zaroori** hai. Sirf domain daaloge to connect nahi hoga.
- Authentication: **OAuth**
- **Create**

**c. Login karo**
- Google consent khulega
- "Google hasn't verified this app" → **Advanced** → **Go to app (unsafe)**
- **"Send email on your behalf"** → **Allow**

Ho gaya. ChatGPT ab 6 tools dekh sakta hai.

## 7. Test karo

ChatGPT mein bolo:

```
Mera profile check karo
```

`get_my_profile` call hona chahiye aur tumhara Gmail address wapas aana chahiye.

Phir:

```
Mujhe apne aap ko ek test job application bhejni hai.
Resume link: <tumhara drive link>
```

Dekhna ki ye sab hota hai ya nahi:
1. Resume link save hua
2. Bina resume ke send **block** hua (agar resume pehle na diya ho)
3. Fake email address **reject** hua
4. Asli mail tumhare inbox mein aaya

---

## claude.ai ke liye bhi wahi

Settings → Connectors → **Add custom connector** → wahi URL:
```
https://your-name.ngrok-free.app/mcp
```

**Claude Code ko ngrok ki zaroorat hi nahi** — localhost pe direct:
```bash
claude mcp add --transport http setu http://localhost:8000/mcp
```

---

## Troubleshooting

**`redirect_uri_mismatch`** → Console ki URI aur `PUBLIC_BASE_URL` + `/auth/callback`
match nahi kar rahe. Dono dekho: `https` hai? trailing slash to nahi? ngrok URL sahi
copy hua?

**ChatGPT mein "Could not connect"** → URL ke end mein `/mcp` laga hai? ngrok terminal
zinda hai? `curl` se check karo pehle.

**ngrok "ERR_NGROK_108" / agent limit** → free plan pe ek waqt mein ek hi tunnel.
Purana ngrok band karo.

**ngrok URL badal gaya** → Static domain nahi liya (Step 2). Le lo, ye dukh khatam
ho jaayega.

**"App not verified" warning** → Normal hai, Advanced → Go to app. Verification ke
baad hat jaayega. [GOOGLE_SETUP.md](GOOGLE_SETUP.md) dekho.

**ngrok ka browser warning page** → Free plan pe pehli visit pe interstitial aata
hai. OAuth pe asar nahi karta, par chaho to:
```bash
ngrok http --url=your-name.ngrok-free.app --request-header-add "ngrok-skip-browser-warning:true" 8000
```

**Server restart kiya par purana URL use ho raha** → `.env` badalne ke baad server
restart karna padta hai. Config sirf startup pe padhi jaati hai.

---

## Dhyan rakhna

ngrok tunnel chalu hai matlab **tumhara laptop internet pe live hai**. Jab tak URL
kisi ko na do, koi aayega nahi — par kaam khatam ho to `Ctrl+C` se band kar dena.

Ye sirf testing ke liye hai. Asli users ke liye proper deploy karo —
[remote/README.md](remote/README.md) dekho.
