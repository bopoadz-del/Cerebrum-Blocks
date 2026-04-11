# CEREBRUM BLOCKS - TODO & RESUME GUIDE

## 🔑 CREDENTIALS & KEYS

### API Keys (Provided by User)
```
DEEPSEEK_API_KEY=sk-7c8b9a6f4e2d1c0b9a8f7e6d5c4b3a2918f7e6d5c4b3a2918f7e6d5c4b3a29
RENDER_API_KEY=rnd_abc123xyz789example
```

### SSH/Git Access
- Repo: `https://github.com/bopoadz-del/Cerebrum-Blocks.git`
- Branch: `main`
- Working Dir: `/workspaces/SSDPPG/`

### Render Services (Current Status)
| Service | URL | Status | Notes |
|---------|-----|--------|-------|
| ssdppg | https://ssdppg.onrender.com | SUSPENDED (resumed) | Old backend |
| ssdppg-api-j1zs | https://ssdppg-api-j1zs.onrender.com | SUSPENDED (resumed) | Old backend |
| cerebrum-platform-api-j1zs | https://cerebrum-platform-api-j1zs.onrender.com | RUNNING | 22 blocks |
| cerebrum-store-api-j1zs | https://cerebrum-store-api-j1zs.onrender.com | RUNNING | Store backend |
| cerebrum-platform-j1zs | https://cerebrum-platform-j1zs.onrender.com | RUNNING | Platform UI |
| cerebrum-store-j1zs | https://cerebrum-store-j1zs.onrender.com | RUNNING | Store UI |

---

## 📋 TOMORROW'S CHECKLIST

### Step 1: Delete Old Services (CRITICAL)
In Render Dashboard, DELETE these 6 services:
- [ ] `ssdppg`
- [ ] `ssdppg-api-j1zs`
- [ ] `cerebrum-platform-api-j1zs`
- [ ] `cerebrum-store-api-j1zs`
- [ ] `cerebrum-platform-j1zs`
- [ ] `cerebrum-store-j1zs`

### Step 2: Deploy via Blueprint
1. [ ] Go to https://dashboard.render.com/blueprints
2. [ ] Click "New Blueprint Instance"
3. [ ] Select repo: `bopoadz-del/Cerebrum-Blocks`
4. [ ] Render will auto-create 4 services from `render.yaml`:
   - `cerebrum-platform-api` (Python backend)
   - `cerebrum-platform` (Static frontend)
   - `cerebrum-store-api` (Python backend)
   - `cerebrum-store` (Static frontend)
5. [ ] Wait 3-5 minutes for all to deploy

### Step 3: Verify Deployment
```bash
# Test Platform Backend
curl https://cerebrum-platform-api.onrender.com/health
# Expected: {"status": "healthy", "blocks_available": 22}

# Test Store Backend
curl https://cerebrum-store-api.onrender.com/health
# Expected: {"status": "healthy", "service": "store"}

# Test Frontend URLs
open https://cerebrum-platform.onrender.com
open https://cerebrum-store.onrender.com
```

### Step 4: Fix Any Issues
If CORS errors appear:
- Check `app/main.py` line 41: `return ["*"]` should allow all origins
- If not working, add explicit origins to `_get_cors_origins()`

---

## 🏗️ ARCHITECTURE

### Current (Messy - 6 services)
```
ssdppg (suspended)
ssdppg-api-j1zs (suspended)
cerebrum-platform-api-j1zs (running)
cerebrum-store-api-j1zs (running)
cerebrum-platform-j1zs (running)
cerebrum-store-j1zs (running)
```

### Target (Clean - 4 services)
```
cerebrum-platform-api   ← Block execution, chains, files
cerebrum-platform       ← Universal UI Shell (platform/index.html)
cerebrum-store-api      ← Block catalog, shopping, billing
cerebrum-store          ← Marketplace UI (store/src/index.html)
```

### URLs After Deploy
- **Platform**: https://cerebrum-platform.onrender.com
- **Platform API**: https://cerebrum-platform-api.onrender.com
- **Store**: https://cerebrum-store.onrender.com
- **Store API**: https://cerebrum-store-api.onrender.com

---

## 📁 FILE STRUCTURE

```
/workspaces/SSDPPG/
├── app/                          # Platform backend
│   ├── main.py                   # FastAPI app with CORS
│   ├── blocks/                   # 22 block implementations
│   └── core/                     # UniversalBlock base class
├── blocks/                       # 58 block definitions
├── platform/                     # Platform frontend (NEW)
│   └── index.html                # Universal UI Shell
├── store/                        # Store (NEW)
│   ├── main.py                   # Store backend API
│   ├── src/index.html            # Store frontend
│   ├── package.json
│   └── requirements.txt
├── render.yaml                   # Blueprint definition
└── TODO.md                       # This file
```

---

## 🔧 TECHNICAL DETAILS

### Backend Endpoints (Platform)
- `GET /health` - Health check
- `GET /v1/blocks` - List all blocks with ui_schema
- `POST /v1/execute` - Execute single block
- `POST /v1/chain` - Execute block chain
- `POST /v1/upload` - File upload

### Backend Endpoints (Store)
- `GET /health` - Health check
- `GET /v1/blocks` - List catalog
- `POST /v1/cart/{user_id}/add` - Add to cart
- `POST /v1/checkout/{user_id}` - Checkout
- `GET /v1/creator/{id}/earnings` - Creator stats

### CORS Configuration
File: `app/main.py` lines 36-41
```python
def _get_cors_origins() -> List[str]:
    return ["*"]  # Allows all origins
```

If security needed later, change to:
```python
return [
    "https://cerebrum-platform.onrender.com",
    "https://cerebrum-store.onrender.com"
]
```

---

## ⚠️ PENDING ISSUES

1. **CORS**: Fixed in code (`return ["*"]`), but needs redeploy to take effect
2. **File Upload**: `/v1/upload` endpoint added, needs testing
3. **Store Backend**: Minimal implementation (3 sample blocks), needs full catalog
4. **Frontend**: Platform UI simplified, Store UI basic - both work but need polish

---

## 🎯 SUCCESS CRITERIA

- [ ] Platform UI loads at `cerebrum-platform.onrender.com`
- [ ] Store UI loads at `cerebrum-store.onrender.com`
- [ ] No CORS errors in browser console
- [ ] Can upload PDF to Platform and get construction analysis
- [ ] Can browse blocks in Store and see pricing

---

## 📞 EMERGENCY COMMANDS

If deployment fails:
```bash
# Check logs
curl https://cerebrum-platform-api.onrender.com/health
curl https://cerebrum-store-api.onrender.com/health

# Force redeploy
git commit --allow-empty -m "force redeploy" && git push

# Check CORS manually
curl -H "Origin: https://cerebrum-platform.onrender.com" \
     https://cerebrum-platform-api.onrender.com/v1/blocks
```

---

## 📝 CONTEXT FOR RESUME

**What we built:**
- Universal Block System with 22 backend blocks
- 2 separate products: Platform (execution) + Store (marketplace)
- Auto-morphing UI that adapts to block schemas
- CORS issues during deployment (fixed in code, needs deploy)

**Current blocker:**
- Old services suspended/resumed but not clean
- New blueprint services not deployed yet
- Need to delete 6 old services, deploy 4 new ones

**User's threat:**
- "Pray it works tomorrow otherwise, u wont have a job anymore"
- **Translation: This MUST work tomorrow!**

---

Last Updated: 2026-04-11 23:05 UTC
Status: READY FOR DEPLOYMENT ✅
