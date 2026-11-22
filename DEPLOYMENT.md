# CareerAI - Free Deployment & Cloud Launch Guide (2026)

This guide documents the architecture, free hosting evaluation, and step-by-step deployment procedure for running **CareerAI** in production with zero recurring cloud expenses.

---

## 1. Cloud Architecture Overview

```
                 +------------------------------------------+
                 |          Client Web Browser              |
                 +--------------------+---------------------+
                                      |
                         HTTPS (Port 443)
                                      |
         +----------------------------v-----------------------------+
         |            Frontend SPA (Vercel Free Tier)               |
         |      React 19 + Vite + Tailwind CSS + Lucide Icons       |
         +----------------------------+-----------------------------+
                                      |
                         HTTPS API Calls (JSON/REST)
                                      |
         +----------------------------v-----------------------------+
         |      Backend ML API (Hugging Face Spaces / Render)       |
         |   FastAPI + PyTorch CPU + DistilBERT + Sentence-BERT     |
         |         + Built-in Guided Career Advisor Fallback        |
         +-------------+------------------------------+-------------+
                       |                              |
            Local SQLite (Fallback)         MongoDB Atlas M0 Free
          (backend/data/careerai.db)         (Persistent Cloud DB)
```

---

## 2. Free Tier Cloud Provider Evaluation

| Component | Recommended Provider | Free Tier Specifications | Why Selected / Evaluation Notes |
| :--- | :--- | :--- | :--- |
| **Frontend** | **Vercel** | Unlimited deployments, 100 GB bandwidth/month, Global Edge CDN, SSL included | Vite React SPA builds into pure static assets (`dist/`). Ultra-fast CDN delivery worldwide with automatic branch previews and seamless custom domain mapping. |
| **Backend ML Engine** | **Hugging Face Spaces (Docker)** | **2 vCPU, 16 GB RAM, 50 GB storage**, permanent uptime, HTTPS URL | **Top Pick for ML Backends.** PyTorch CPU + DistilBERT (268 MB) + Sentence-BERT (91 MB) consume ~1.2 GB of RAM during startup and concurrent inference. Hugging Face's 16 GB RAM allocation completely eliminates Out-Of-Memory (OOM) risks. |
| **Alternative Backend** | **Render Free Web Service** | 0.5 CPU, 512 MB RAM, spins down after 15 mins inactivity | **Warning: 512 MB RAM limit.** PyTorch CPU and transformer models peak at ~650 MB to 1.1 GB during inference. On Render's 512 MB tier, PyTorch will occasionally trigger an Out-Of-Memory termination (`exit code 137`) unless ONNX quantization is used. |
| **Database** | **MongoDB Atlas (M0)** | 512 MB permanent storage, replica set across 3 nodes, TLS 1.3 encryption | Ample storage for thousands of candidate accounts and snapshot histories. When `save_resume_text=false`, each analysis record averages only 4 KB. |
| **AI Career Assistant** | **Built-in Guided Advisor** | 0 MB additional RAM, 0 ms cold start, 100% deterministic & offline | Runs directly within the backend FastAPI process. If local Ollama is offline or unavailable on the cloud host, queries are answered instantly using candidate skills, gap matrices, and roadmap milestones. |

---

## 3. Step-by-Step Deployment Instructions

### Phase A: MongoDB Atlas Database Setup (Free M0)
1. Navigate to [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas) and create a free account.
2. Select **Create a Deployment** → choose **M0 Free (Shared)**.
3. Choose a cloud region closest to your backend (e.g., AWS `us-east-1` or `eu-central-1`).
4. In **Database Access**, create a user (e.g., `careerai_app`) with a secure password.
5. In **Network Access**, add IP address `0.0.0.0/0` (Allow Access from Anywhere) to permit cloud backend connections.
6. Under **Clusters** → **Connect** → **Drivers (Python 3.11+)**, copy the connection URI:
   ```
   mongodb+srv://careerai_app:<password>@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority
   ```

---

### Phase B: Backend Deployment on Hugging Face Spaces (Recommended)
1. Log in to [huggingface.co](https://huggingface.co) and click **New Space**.
2. Space settings:
   - **Space Name:** `careerai-api`
   - **License:** MIT or Apache 2.0
   - **SDK:** **Docker** (Blank)
   - **Space Hardware:** **CPU Basic (2 vCPU · 16 GB RAM - Free)**
3. In Space Settings → **Variables and secrets**, add:
   - `JWT_SECRET_KEY`: `<Generate 32+ char random hex string>`
   - `ENVIRONMENT`: `production`
   - `MONGODB_URI`: `<Your MongoDB Atlas connection URI>`
   - `DATABASE_NAME`: `ai_job_prediction`
   - `CORS_ORIGINS`: `https://your-frontend.vercel.app` (or `*` during initial testing)
4. Push the repository to the Hugging Face Space Git remote:
   ```bash
   git remote add space https://huggingface.co/spaces/<your-username>/careerai-api
   git push space main
   ```
5. Hugging Face will automatically build using `backend/Dockerfile` and deploy. Once built, note your Space public URL (e.g., `https://<username>-careerai-api.hf.space`).

---

### Phase C: Frontend Deployment on Vercel
1. Log in to [vercel.com](https://vercel.com) with GitHub.
2. Click **Add New Project** → Import your GitHub repository.
3. Configure Project Settings:
   - **Framework Preset:** Vite
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
4. Add Environment Variable:
   - `VITE_API_BASE_URL`: `https://<username>-careerai-api.hf.space` (or your backend URL)
5. Click **Deploy**. Vercel will install dependencies, compile the production bundle, and issue an automatic HTTPS domain (e.g., `https://careerai.vercel.app`).
6. The included [frontend/vercel.json](file:///c:/Users/boyap/Desktop/AI%20Job%20Prediction%20System/frontend/vercel.json) rewrite rule handles client-side React Router navigation without 404 errors.

---

## 4. Production Smoke Test Verification Checklist

Once deployed, verify the complete candidate workflow in production:

- [ ] **Health Check:** `curl https://<backend-url>/api/health` returns `{"status": "healthy"}`.
- [ ] **Security Headers:** Response headers include `X-Content-Type-Options: nosniff` and `X-Frame-Options: DENY`.
- [ ] **User Auth:** Register a test account at `/register`, verify JWT token creation, and test `/api/auth/me`.
- [ ] **Resume Parsing:** Upload a test PDF resume and verify skill extraction and PII parsing.
- [ ] **DistilBERT Inference:** Verify top-3 job role predictions with confidence scores.
- [ ] **Sentence-BERT Matcher:** Test semantic comparison against a job description.
- [ ] **Roadmap Generation:** Generate 30-day and 60-day roadmaps with 4 and 8 milestones.
- [ ] **AI Assistant:** Query the chatbot to confirm instant responses from the Guided Career Advisor.
- [ ] **History & Privacy:** Verify saved record creation; check that resume raw text is absent when privacy mode is enabled.
- [ ] **Account Deletion:** Verify cascading account deletion and token revocation.
