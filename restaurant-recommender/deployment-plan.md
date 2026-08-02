# AI Eats — Deployment Plan

This document outlines the strategy for deploying the AI Eats application across two distinct platforms:
- **Backend (FastAPI, AI Engine):** Railway
- **Frontend (Vanilla HTML/JS/Tailwind):** Vercel

By decoupling the frontend from the backend, we leverage Vercel's edge CDN for lightning-fast UI delivery while using Railway's containerized environment to handle heavy Python data processing and LLM integration.

---

## 1. Architectural Changes Required

Currently, the FastAPI `main.py` serves both the API endpoints and the `index.html` file. To deploy across two platforms, we must decouple them.

### A. Vercel Configuration (`vercel.json`)
Since the frontend JavaScript currently makes requests to relative paths (e.g., `fetch('/api/v1/locations')`), deploying the frontend to a different domain will break these links.
Instead of hardcoding the backend URL in our JavaScript (which causes CORS issues and exposes the backend domain), we will use Vercel's Rewrite feature.

Create a `vercel.json` file in the root of the repository:
```json
{
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "https://<YOUR_RAILWAY_URL>/api/$1"
    }
  ]
}
```
*This seamlessly proxies all `/api/...` calls from the frontend directly to the Railway backend.*

### B. Railway Configuration (`Procfile` / `railway.json`)
Railway will detect the `requirements.txt` and know it's a Python app. We need to explicitly tell it how to start the FastAPI server.
Create a `Procfile` in the root of the repository:
```text
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

---

## 2. Phase 1: Deploying the Backend on Railway

Railway is ideal for our Python backend because it easily handles the memory requirements for downloading and caching the Hugging Face Zomato dataset in memory.

### Steps:
1. **Push to GitHub**: Ensure all latest backend code (`main.py`, `data/`, `services/`, etc.) is pushed to the `main` branch.
2. **Create Railway Project**: 
   - Go to [Railway.app](https://railway.app/) and sign in with GitHub.
   - Click **New Project** → **Deploy from GitHub repo**.
   - Select the `AI-Eats` repository.
3. **Configure Environment Variables**:
   Before the deployment finishes, go to the **Variables** tab in Railway and add:
   - `GROQ_API_KEY`: Your Groq API Key (required for recommendations)
   - `LLM_PROVIDER`: `groq`
   - `HF_TOKEN`: (Optional but recommended) Your Hugging Face read token, to bypass rate limits when downloading the Zomato dataset on startup.
4. **Generate Public URL**:
   - Go to the **Settings** tab → **Environment** → **Domains**.
   - Click **Generate Domain**.
   - *Save this URL (e.g., `https://ai-eats-production.up.railway.app`), as we need it for Vercel.*
5. **Verify**: Wait for the build to complete. Visit `<RAILWAY_URL>/api/v1/locations` to confirm the backend successfully initialized the dataset and is serving data.

---

## 3. Phase 2: Deploying the Frontend on Vercel

Vercel will serve our `frontend/index.html` statically. 

### Steps:
1. **Configure Root Directory**:
   Since our `index.html` is inside the `frontend/` folder, we need to tell Vercel where to look.
2. **Create Vercel Project**:
   - Go to [Vercel.com](https://vercel.com/) and sign in with GitHub.
   - Click **Add New Project** and select the `AI-Eats` repository.
3. **Configure Build Settings**:
   - **Framework Preset**: `Other`
   - **Root Directory**: `frontend` (Type this in so Vercel knows to serve from the frontend folder).
   - **Build Command**: Leave empty.
   - **Output Directory**: Leave empty.
4. **Environment Variables**:
   Since this is a static Vanilla JS site, we don't need environment variables for the frontend. The `vercel.json` (placed inside the `frontend/` folder) will handle the routing.
5. **Deploy**:
   Click **Deploy**. Vercel will assign a URL like `https://ai-eats.vercel.app`.

---

## 4. Final Integration Checklist

- [ ] Create `Procfile` in project root for Railway.
- [ ] Move `vercel.json` into the `frontend/` folder with the updated Railway destination URL.
- [ ] Push changes to GitHub.
- [ ] Ensure Railway has the `GROQ_API_KEY` configured.
- [ ] Test the Vercel URL. Ensure that location/cuisine dropdowns populate (verifying the Vercel proxy works) and that "Get AI Recommendations" successfully fetches results.
