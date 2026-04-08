# 🚀 Deploy to Render

Complete guide to deploy the AI Block System on Render.

## Quick Deploy (One-Click)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/yourusername/ai-block-system)

*(Replace with your actual repo URL)*

## Manual Deploy

### Step 1: Create Account
1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Connect your repository

### Step 2: Create Web Service
1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repo
3. Fill in the form:

| Setting | Value |
|---------|-------|
| **Name** | `ai-block-system` |
| **Environment** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Plan** | Free (or paid for production) |

### Step 3: Add Disk (Optional but Recommended)
For persistent storage:
1. Click **"Disks"** in your service
2. **Name**: `data`
3. **Mount Path**: `/app/data`
4. **Size**: 1 GB (or more)

### Step 4: Set Environment Variables
Go to **Environment** tab and add:

```bash
# Required
PYTHON_VERSION=3.11.0
DATA_DIR=/app/data

# Optional - AI Features
OPENAI_API_KEY=sk-your-key
ANTHROPIC_API_KEY=sk-ant-your-key

# Optional - Search
SERPER_API_KEY=your-key

# Optional - Drive Integrations
GOOGLE_CREDENTIALS_PATH=/app/data/credentials.json
ONEDRIVE_ACCESS_TOKEN=your-token
```

### Step 5: Deploy
Click **"Create Web Service"**

Wait for build (~2-3 minutes), then visit your URL!

---

## Post-Deploy Setup

### 1. Verify Deployment
```bash
curl https://your-service.onrender.com/health
```

### 2. Test a Block
```bash
curl -X POST https://your-service.onrender.com/execute \
  -H "Content-Type: application/json" \
  -d '{
    "block": "chat",
    "input": "Hello from Render!",
    "params": {"provider": "mock"}
  }'
```

### 3. API Documentation
Visit: `https://your-service.onrender.com/docs`

---

## Troubleshooting

### Build Fails
```bash
# Check Python version in runtime.txt
python-3.11.0
```

### Port Issues
Render automatically sets `$PORT`. Don't hardcode it!

### Disk Not Persisting
Ensure `DATA_DIR=/app/data` matches your disk mount path.

### Import Errors
```bash
# Check requirements.txt is in root
# Verify app/__init__.py exists
```

---

## Production Checklist

- [ ] Upgrade from Free plan
- [ ] Add custom domain
- [ ] Set up environment variables
- [ ] Add disk for persistence
- [ ] Configure CORS if needed
- [ ] Set up monitoring/health checks
- [ ] Enable auto-deploy on push

---

## Free Tier Limits

| Resource | Limit |
|----------|-------|
| RAM | 512 MB |
| CPU | Shared |
| Disk | 1 GB |
| Sleep | After 15 min idle |
| Bandwidth | 100 GB/month |

Upgrade for production use!
