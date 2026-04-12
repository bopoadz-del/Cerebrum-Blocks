# DEPLOY FIX - Two Options

## OPTION 1: Fix Existing Services (Fastest - 2 minutes)

Go to Render Dashboard and fix each service manually:

### 1. Fix `cerebrum-platform-j1zs` (Frontend)
1. https://dashboard.render.com/web/cerebrum-platform-j1zs/settings
2. Change **Environment** from `Node` to `Static Site`
3. Change **Build Command** to: `echo "No build needed"`
4. Change **Publish Directory** to: `./platform`
5. Click **Save Changes**
6. Click **Manual Deploy** → **Deploy Latest Commit**

### 2. Fix `cerebrum-platform-api-j1zs` (API)
1. https://dashboard.render.com/web/cerebrum-platform-api-j1zs/settings
2. Verify **Start Command** is: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Click **Manual Deploy** → **Deploy Latest Commit**

---

## OPTION 2: Fresh Deploy (Cleanest - 5 minutes)

Delete old services and deploy fresh:

### Step 1: Delete Old Services
Go to https://dashboard.render.com/ and delete:
- `cerebrum-platform-j1zs`
- `cerebrum-platform-api-j1zs`
- `cerebrum-store-j1zs`
- `cerebrum-store-api-j1zs`

### Step 2: Deploy from Blueprint
1. Go to https://dashboard.render.com/blueprints
2. Click **"New Blueprint Instance"**
3. Select repo: `bopoadz-del/Cerebrum-Blocks`
4. Render will auto-create 4 new services from `render.yaml`
5. Wait 3-5 minutes for deploy

---

## VERIFY AFTER FIX

Test these URLs:
```bash
# API Health
curl https://cerebrum-platform-api-j1zs.onrender.com/health

# Frontend
curl https://cerebrum-platform-j1zs.onrender.com/

# CORS Test
curl -H "Origin: https://cerebrum-platform-j1zs.onrender.com" \
     https://cerebrum-platform-api-j1zs.onrender.com/v1/blocks
```

All should return HTTP 200 with proper JSON.
