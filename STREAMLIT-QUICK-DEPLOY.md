# 🚀 Deploy to Streamlit Cloud - Quick Start

## The 3-Step Process

### Step 1️⃣: Push to GitHub (2 minutes)

```powershell
# From project root
cd "D:\Triage Agent Final\finance-support-triage-agent-final-streamlit-1"

# Check git status
git status

# Stage all changes
git add .

# Commit
git commit -m "Finance Triage Agent - Ready for Cloud"

# First time only - add remote
git remote add origin https://github.com/YOUR_USERNAME/finance-triage-agent.git
git branch -M main

# Push to GitHub
git push -u origin main
```

**Create GitHub repo first:** https://github.com/new

---

### Step 2️⃣: Deploy on Streamlit Cloud (1 minute)

1. Go to **https://share.streamlit.io**
2. Click **"New app"**
3. Select:
   - Repo: `YOUR_USERNAME/finance-triage-agent`
   - Branch: `main`
   - Main file: `streamlit_app.py`
4. Click **"Deploy"** → ☕ Wait 2-3 minutes

**Your live URL:** `https://YOUR_USERNAME-finance-triage-agent.streamlit.app`

---

### Step 3️⃣: Add Secrets (5 minutes)

In Streamlit Cloud dashboard:
1. Click your app name
2. Go to **Settings** → **Secrets**
3. Copy-paste this template (get values below):

```toml
# Required: Database
DATABASE_URL="postgresql://user:password@host:5432/database"

# Required: Gmail
EMAIL_USER="your_email@gmail.com"
EMAIL_PASSWORD="your_16_char_app_password"

# Required: LLM
GROQ_API_KEY="your_groq_api_key"

# Optional
ENABLE_EMAIL_POLLING="true"
EMAIL_POLL_INTERVAL="300"
EMAIL_INCLUDE_READ="true"
EMAIL_LOOKBACK_DAYS="30"
LOG_LEVEL="INFO"
```

4. Click **Save** → App restarts automatically

---

## 🔑 Get Your Secrets

### Database URL
**Free Option - Neon PostgreSQL:**
1. Go to https://neon.tech (sign up free)
2. Create new project
3. Copy connection string: `postgresql://...`
4. Paste as `DATABASE_URL`

**Alternative - Supabase:**
1. Go to https://supabase.com
2. Create project
3. Copy PostgreSQL URL
4. Use as `DATABASE_URL`

### Gmail App Password
1. Open https://myaccount.google.com/security
2. Enable **2-Step Verification** (if not done)
3. Click **App passwords**
4. Select: **Mail** + **Windows Computer**
5. Copy 16-char password → use as `GMAIL_PASSWORD`

### Groq API Key
1. Go to https://console.groq.com
2. Sign up / login
3. Click **"API Keys"**
4. Create new key
5. Copy → use as `GROQ_API_KEY`

---

## 📝 File Checklist

Before pushing, ensure you have:
- ✅ `streamlit_app.py` (main entry point)
- ✅ `requirements.txt` (all dependencies)
- ✅ `frontend/templates.py` (UI templates)
- ✅ `backend/models.py` (database models)
- ✅ `.streamlit/config.toml` (theme config)
- ⚠️ DO NOT push: `.env`, `secrets.toml`, `.venv/`

Check `.gitignore`:
```
.env
.streamlit/secrets.toml
.venv/
*.db
__pycache__/
```

---

## ✨ After Deployment

### Your app is now live!
- **URL:** https://YOUR_USERNAME-finance-triage-agent.streamlit.app
- **Updates:** Push to `main` branch → auto-deploys in 10-30 seconds
- **Logs:** Dashboard → **Manage app** → **Logs**

### Keep It Running
- Streamlit Cloud may sleep after inactivity (free tier)
- Auto-refresh and polling only run while the app is open
- For always-on fetch, add an external keep-alive ping or run a VM worker

### Update Your Code
```powershell
git add .
git commit -m "Your changes"
git push origin main
```
Streamlit Cloud re-deploys automatically!

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| `DATABASE_URL not set` | Check Secrets panel, restart app |
| `Gmail login failed` | Use **App Password**, not regular password |
| `Module not found` | Add to `requirements.txt`, redeploy |
| `Port already in use` | Streamlit Cloud handles ports automatically |
| `Timeout errors` | Check database connection URL |

---

## 💡 Pro Tips

1. **Monitor Real-Time Logs**
   - Dashboard → Manage app → Logs
   - See errors as they happen

2. **Test Before Pushing**
   ```powershell
   streamlit run streamlit_app.py
   ```

3. **Keep Secrets Secure**
   - Never commit `.env` or `secrets.toml`
   - Always use Streamlit Cloud Secrets panel
   - Regenerate API keys after deployment

4. **Rollback if Needed**
   - Go to Dashboard → Revert to previous version

---

## 📚 Full Documentation
- Read [STREAMLIT-CLOUD-DEPLOY.md](STREAMLIT-CLOUD-DEPLOY.md) for details
- Streamlit Docs: https://docs.streamlit.io/deploy
- Community Help: https://discuss.streamlit.io

---

**Ready?** Start with **Step 1** above! 🎉
