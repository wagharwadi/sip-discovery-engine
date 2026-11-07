# Step 1: Setup Guide (Windows, all free)

Tick each box as you go. Total time: ~45–60 min.
Order: **send recruitment first** (people need time to reply), then set up accounts.

---

## A. Recruitment (15 min), do this first
- [ ] Create the Google Form from `recruitment_kit.md` §4
- [ ] Send the WhatsApp message to 5+ groups and DM people you know
- [ ] Post the LinkedIn / Instagram version

---

## B. Accounts and API keys
Copy each key into `.env` (section C) as you get it. **Never paste keys into chats, docs or GitHub.**

### 1. GitHub
- [ ] Sign up at https://github.com (skip if you already have an account)
- [ ] Create a new **public** repo called `groww-sip-discovery` (keys will never go in it, so public is fine and easier for Streamlit)

### 2. Gemini API key (main AI model)
- [ ] Go to https://aistudio.google.com → sign in with Google
- [ ] Click **Get API key** → **Create API key**
- [ ] Copy it into `.env` as `GEMINI_API_KEY`

### 3. Groq API key (backup AI model)
- [ ] Go to https://console.groq.com → sign up
- [ ] **API Keys** → **Create API Key** → copy it into `.env` as `GROQ_API_KEY`

### 4. YouTube Data API key
- [ ] Go to https://console.cloud.google.com → top bar **Select project** → **New project** (name: `sip-discovery`) → Create
- [ ] Left menu **APIs & Services → Library** → search **YouTube Data API v3** → **Enable**
- [ ] **APIs & Services → Credentials → + Create credentials → API key** → copy it into `.env` as `YOUTUBE_API_KEY`
- (The free quota of 10,000 units/day is plenty: reading 100 comments costs ~1 unit.)

### 5. Reddit app (for the Reddit scraper)
- [ ] Log in to Reddit → go to https://www.reddit.com/prefs/apps
- [ ] Scroll down → **create another app…**
  - name: `sip-research` · type: **script** · redirect uri: `http://localhost:8080`
- [ ] Copy the string under the app name (the **client id**) and the **secret** into `.env`
- ⚠️ Reddit sometimes asks new API apps to request approval. **If it blocks you, skip this.** We have a fallback, and you can note it as a limitation.

### 6. Streamlit Community Cloud
- [ ] Go to https://share.streamlit.io → **Continue with GitHub** → authorise
- (Nothing to deploy yet. This just links the account.)

---

## C. Install Python and the project files

### 1. Python
- [ ] Open PowerShell and type `py --version`. If it shows 3.10 or higher, skip ahead.
- [ ] Otherwise install from https://www.python.org/downloads/ and **tick "Add python.exe to PATH"** on the first screen.
- [ ] Install VS Code (https://code.visualstudio.com) if you don't have it.

### 2. Set up the project (in PowerShell)
```powershell
cd "C:\Users\adity\OneDrive\Desktop\4-1\2_attempt_nextleap"
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
If `activate` fails with a "running scripts is disabled" error, run this once and try again:
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 3. Create your `.env`
- [ ] Copy `.env.example` → rename the copy to `.env`
- [ ] Paste in your keys (no quotes, no spaces around `=`)

### 4. Test every key
```powershell
python test_keys.py
```
You want ✅ next to each line. Send me any ❌ message and I'll fix it.

---

## D. Evidence Log
- [ ] Create a Google Doc called **"AI Evidence Log: Groww SIP Continuation"**
- [ ] Paste in the structure from `evidence_log_template.md`
- [ ] **Share → General access → Anyone with the link → Viewer**
- [ ] Add first entry under *Decision log*: "6 Nov: chose Groww because…"

---

## ✅ Step 1 is done when
- Recruitment sent + form live
- `python test_keys.py` shows ✅ for Gemini, Groq, YouTube, Google Play (Reddit optional)
- Evidence Log doc exists and is shared

Then tell me, and we move to **Step 2 (metric decomposition)** and I'll write the scrapers for Step 3.
