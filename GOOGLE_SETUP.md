# Google Cloud Setup — Complete Walkthrough

Ye doc **hosted server** (`remote/`) ke liye hai. Local wale server (`mcp_server/`)
ke liye setup alag hai — neeche "Do alag client types" dekho.

> **Console ka UI 2025 mein badla tha.** "OAuth consent screen" ab **Google Auth
> Platform** ban gaya hai, aur settings teen jagah bant gayi hain: Branding,
> Audience, Data Access. Purane tutorials wo purana menu dhundhwate hain jo ab
> exist hi nahi karta. Isliye neeche ke saare links direct hain.

---

## Do alag client types — ye confusion #1 hai

| Server | Client type | Redirect URI |
|---|---|---|
| `mcp_server/` (local, tumhare laptop pe) | **Desktop app** | koi nahi |
| `remote/` (hosted, sab users ke liye) | **Web application** | `<BASE_URL>/auth/callback` |

Galat type chuna to redirect URI ka field hi nahi milega. Ye doc **Web application**
ke liye hai.

---

## Step 1 — Project

[console.cloud.google.com/projectcreate](https://console.cloud.google.com/projectcreate)

- Project name: `setu` (ya kuch bhi)
- **Create**

> Upar left ka project selector check karte rehna. Sabse aam galti: Gmail API ek
> project mein enable karna aur client dusre project mein banana. Sab kuch **ek hi
> project** mein hona chahiye.

## Step 2 — Gmail API enable

[console.cloud.google.com/apis/library/gmail.googleapis.com](https://console.cloud.google.com/apis/library/gmail.googleapis.com)

- **ENABLE** dabao
- Button "MANAGE" ban jaaye = ho gaya

> **Ye step skip mat karna.** Google scope picker mein sirf un APIs ke scopes
> dikhata hai jo enable hain. Gmail API off hai to Step 4 mein `gmail.send` list
> mein milega hi nahi, chahe kitna bhi filter karo.

## Step 3 — Branding

[console.cloud.google.com/auth/branding](https://console.cloud.google.com/auth/branding)

- **App name** — user ko consent screen pe yahi dikhega
- **User support email** — apna
- **Developer contact email** — apna
- **Save**

> Naya project hai aur ye page khali/"not configured" dikha? To pehle
> [Overview](https://console.cloud.google.com/auth/overview) pe **GET STARTED**
> wizard poora karo. Uske baad Branding, Audience, Clients, Data Access — sab
> left nav mein aa jaayenge.

## Step 4 — Audience (publishing status)

[console.cloud.google.com/auth/audience](https://console.cloud.google.com/auth/audience)

- User type: **External**
- **PUBLISH APP** → confirm
- Ab "Publishing status: **In production**" dikhna chahiye

### Ye sabse important setting hai

| | **Testing** | **In production** (unverified) | **In production** (verified) |
|---|---|---|---|
| Kaun login kar sakta | Sirf Test users list wale | **Koi bhi** | Koi bhi |
| Test users list | **Manually add karni padegi** | Chahiye hi nahi | Chahiye hi nahi |
| Warning screen | Nahi | "Google hasn't verified this app" | Nahi |
| Total cap | 100 test users | **100 users (total, kabhi bhi)** | Unlimited |
| Refresh token | **7 din mein expire!** | Expire nahi hota | Expire nahi hota |

**Publish karo.** Testing mode mein do problem hain: har user ka email manually add
karna padega (scale nahi karta), aur har user ko **har hafte dobara login** karna
padega — tumhe lagega code toot gaya, par ye Google ka rule hai.

Production-unverified mein user ko warning screen dikhega (Advanced → "Go to app"),
par koi bhi login kar sakta hai.

## Step 5 — Data Access (scopes)

[console.cloud.google.com/auth/scopes](https://console.cloud.google.com/auth/scopes)
→ **ADD OR REMOVE SCOPES** → right panel khulega

Ye teen add karo:

```
openid
https://www.googleapis.com/auth/userinfo.email
https://www.googleapis.com/auth/gmail.send
```

> **`openid` koi URL nahi hai** — bas wahi ek word. Log ise
> `https://www.googleapis.com/auth/openid` bana dete hain, jo exist hi nahi karta.

List mein na mile to panel mein neeche **"Manually add scopes"** box hai:
paste karo → **ADD TO TABLE** ← *ye step log bhool jaate hain* → **UPDATE** → **SAVE**

### Save ke baad aisa dikhna chahiye

| Box | Kya hona chahiye |
|---|---|
| Non-sensitive | `openid`, `userinfo.email` |
| Sensitive | `gmail.send` — ⚠️ "Approval required" ke saath |
| **Restricted** | **KHALI** |

Sensitive box mein ⚠️ dikhna **sahi hai**. Wo bas ye keh raha hai ki 100 users se
aage jaane ke liye verification chahiye hogi — abhi kuch block nahi karta.

### ⚠️ Ye rule kabhi mat todna

| Scope | Tier | Cost |
|---|---|---|
| `gmail.send` | Sensitive | Free verification, ~2-6 hafte |
| `gmail.readonly` / `compose` / `modify` / `insert` | **Restricted** | **CASA audit, $15k-75k, har saal repeat** |

`gmail.readonly` picker mein `gmail.send` ke bilkul paas hota hai. Ek galat tick aur
tumhara free product ek paid annual security audit ban jaata hai. **Restricted box
hamesha khali rehna chahiye.**

## Step 6 — Client banao (yahan credentials milengi)

[console.cloud.google.com/auth/clients](https://console.cloud.google.com/auth/clients)
→ **CREATE CLIENT**

- Application type: **Web application**
- Name: `local-test` (ya kuch bhi)
- Neeche scroll → **Authorized redirect URIs** → **+ ADD URI**:

  | Kab | URI |
  |---|---|
  | Localhost testing | `http://localhost:8000/auth/callback` |
  | ngrok testing | `https://your-name.ngrok-free.app/auth/callback` |
  | Production | `https://your-domain.com/auth/callback` |

- **CREATE**

Popup mein **Client ID** aur **Client secret** dikhengi.

> **Secret sirf ek baar dikhti hai.** Chhut jaye to client pe click → "Add secret"
> → nayi bana lo, purani delete kar do.

Ek client mein multiple redirect URIs add kar sakte ho — localhost, ngrok aur
production teeno ek saath rakh sakte ho.

## Step 7 — `.env`

```env
GOOGLE_CLIENT_ID=1234-abc.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxx
PUBLIC_BASE_URL=http://localhost:8000
```

`.env` gitignored hai — kabhi commit mat karna.

Check karo ki sab load ho raha hai:

```bash
python -c "from remote import config; print(config.missing_settings() or 'ready')"
```

---

## Troubleshooting

**`redirect_uri_mismatch`** — sabse aam error.
URI **bilkul exactly** match karna chahiye: `PUBLIC_BASE_URL` + `/auth/callback`.
Ye sab alag-alag cheezein hain:
- `http://localhost:8000/auth/callback` ✅
- `http://localhost:8000/auth/callback/` ❌ (trailing slash)
- `https://localhost:8000/auth/callback` ❌ (https)
- `http://127.0.0.1:8000/auth/callback` ❌ (localhost nahi hai)

**`gmail.send` scope list mein nahi mil raha** → Step 2 (Gmail API enable) nahi hua,
ya galat project mein hua.

**"Access blocked: app has not completed verification"** → Step 4 mein Publish
nahi kiya, aur tum test users list mein bhi nahi ho.

**"Google hasn't verified this app"** → Ye normal hai. Advanced → "Go to app
(unsafe)" → chalega. Verification ke baad hat jaayega.

**Scope badalne ke baad purana token kaam nahi kar raha** → Normal hai. `~/.fastmcp/`
ka cached token delete karke dobara login karo.

**Sab theek lag raha par kuch kaam nahi kar raha** → Project selector check karo.
90% chance galat project mein baithe ho.

---

## Aage: Verification (jab 100 users ke paas pahuncho)

[Verification Center](https://console.cloud.google.com/auth/verification) se apply karo.

Chahiye:
- **Privacy Policy URL** — live, working
- **Terms of Service URL** — live, working
- **Domain verification** via [Search Console](https://search.google.com/search-console)
- **Demo video** (YouTube, unlisted chalega) — pura flow dikhana: consent se lekar
  email send tak
- **Scope justification** — kyun `gmail.send` chahiye

Time: **~2-6 hafte**, back-and-forth ke saath.

**Aaj hi apply kar do** — code ready hone ka intezaar mat karo. Review parallel
chalta rahega, aur tab tak tum 100 users tak build kar sakte ho.

---

## Sources

- [Gmail API scopes — send is sensitive, readonly is restricted](https://developers.google.com/workspace/gmail/api/auth/scopes)
- [Configure OAuth consent (Google Auth Platform)](https://developers.google.com/workspace/guides/configure-oauth-consent)
- [Manage app audience — Testing vs In production](https://support.google.com/cloud/answer/15549945?hl=en)
- [Unverified apps & the 100-user cap](https://support.google.com/cloud/answer/7454865?hl=en)
- [Sensitive scope verification](https://developers.google.com/identity/protocols/oauth2/production-readiness/sensitive-scope-verification)
- [Restricted scope verification (CASA)](https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification)
- [Refresh token expiry in Testing status](https://developers.google.com/identity/protocols/oauth2)
