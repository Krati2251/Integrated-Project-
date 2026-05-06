# Deploy to Streamlit Cloud

## Prerequisites
1. **GitHub Account** - Required (Streamlit Cloud deploys from GitHub repos)
2. **Streamlit Account** - Sign up at https://streamlit.io/
3. **Secrets** - Database URL, API keys, Gmail credentials

---

## Step 1: Push to GitHub

```powershell
# 1. Initialize git (if not already done)
cd "D:\Triage Agent Final\finance-support-triage-agent-final-streamlit-1"
git init

# 2. Add all files
git add .

# 3. Commit
git commit -m "Finance Triage Agent - Ready for Streamlit Cloud"

# 4. Create a new repo on GitHub (https://github.com/new)
# Then push:
git remote add origin https://github.com/YOUR_USERNAME/finance-triage-agent.git
git branch -M main
git push -u origin main
```

---

## Step 2: Deploy on Streamlit Cloud

### 2A: Create Streamlit Cloud App
1. Go to **https://share.streamlit.io**
2. Click **"New app"** button
3. Select:
   - **Repository**: `YOUR_USERNAME/finance-triage-agent`
   - **Branch**: `main`
   - **Main file path**: `streamlit_app.py`
4. Click **"Deploy"**

### 2B: Set Secrets (Critical!)
After deployment, go to **App → Settings → Secrets** and paste:

```toml
# Database
DATABASE_URL="postgresql://username:password@host:5432/finance_db"

# Gmail
EMAIL_USER="your_email@gmail.com"
EMAIL_PASSWORD="your_app_password"

# LLM
GROQ_API_KEY="your_groq_api_key"
ANTHROPIC_API_KEY="your_anthropic_key"  # if using Claude

# App Config
LOG_LEVEL="INFO"
ENABLE_EMAIL_POLLING="true"
EMAIL_POLL_INTERVAL="300"
EMAIL_INCLUDE_READ="true"
EMAIL_LOOKBACK_DAYS="30"
```

---

## Step 3: Configure Database

### Option A: Use Cloud Database (Recommended)
1. **Neon PostgreSQL** (Free tier available)
   - Go to https://neon.tech
   - Create PostgreSQL instance
   - Get `DATABASE_URL`
   - Paste in Streamlit Secrets

2. **Supabase** (Alternative)
   - Go to https://supabase.com
   - Create PostgreSQL project
   - Copy connection string
   - Paste in Streamlit Secrets

### Option B: Use Existing Database
- If you have RDS/local DB accessible from internet, update `DATABASE_URL` in secrets

---

## Step 4: Get Required API Keys

### Gmail App Password
```
1. Go to https://myaccount.google.com/security
2. Enable "2-Step Verification"
3. Go to "App passwords"
4. Select: Mail + Windows Computer
5. Copy 16-char password
6. Use in GMAIL_PASSWORD secret
```

### Groq API Key
```
1. Go to https://console.groq.com
2. Create API key
3. Copy and paste in GROQ_API_KEY secret
```

---

## Step 5: Deploy & Monitor

```
Your app will be live at:
https://YOUR_USERNAME-finance-triage-agent.streamlit.app
```

### Monitor Logs
- Click **"Manage app"** → **"Logs"** to view real-time logs
- Check for errors during initial startup
- Database connection issues will show here

---

## Troubleshooting

### Error: `DATABASE_URL not set`
- Check Streamlit Cloud → Settings → Secrets
- Ensure you restart the app after adding secrets

### Error: `Gmail authentication failed`
- Use **App Password**, NOT your Google password
- Enable 2-Step Verification first

### Error: `Port already in use`
- Streamlit Cloud automatically assigns ports (ignore local port settings)

### Error: `ModuleNotFoundError`
- Check `requirements.txt` has all dependencies
- Redeploy after updating requirements

---

## Key Differences: Streamlit Cloud vs Docker

| Feature | Streamlit Cloud | Docker (Local) |
|---------|----------------|---|
| Backend | Python process (no FastAPI) | FastAPI + Uvicorn |
| Database | Must be cloud-hosted | Local PostgreSQL |
| Files | Git-based deployment | Container-based |
| Scaling | Automatic | Manual |
| Cost | Free tier available | Self-hosted |

---

## File Structure Expected by Streamlit Cloud
```
your-repo/
├── streamlit_app.py          ← Main entry point
├── requirements.txt           ← Python dependencies
├── .streamlit/
│   └── config.toml           ← Streamlit config (optional)
├── frontend/
│   ├── templates.py
│   ├── static/
│   └── ...
├── backend/
│   ├── models.py
│   ├── database.py
│   └── ...
└── .env                       ← NOT deployed (use Secrets instead)
```

---

## After Deployment

### Keep App Alive
Streamlit Community Cloud may sleep apps after inactivity. Auto-refresh and polling
only run while a user has the app open. For always-on fetching, use one of:

1) External keep-alive ping (recommended)
   - Create a GitHub Actions workflow to `curl` your app URL every 10 minutes.
   - Store the URL in a repo secret named `STREAMLIT_APP_URL`.

2) Always-on backend worker
   - Run `backend/main.py` (FastAPI) and `backend/email_ingestion.py` on a VM.
   - Point both to the same `DATABASE_URL` as the Streamlit app.

### Update Code
```powershell
git add .
git commit -m "Your update message"
git push origin main
```
Streamlit Cloud auto-deploys within seconds!

---

## Quick Reference Commands

```powershell
# First time setup
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/finance-triage-agent.git
git push -u origin main

# Update deployment
git add .
git commit -m "Update message"
git push origin main

# View app
https://YOUR_USERNAME-finance-triage-agent.streamlit.app
```

---

**Need Help?** → https://docs.streamlit.io/deploy/streamlit-community-cloud
