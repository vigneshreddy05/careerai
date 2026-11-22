# CareerAI: AI-Powered Job Prediction and Career Recommendation System

[![Python](https://img.shields.io/badge/Python-3.11.9-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6.0+-646CFF.svg)](https://vitejs.dev/)
[![PyTorch](https://img.shields.io/badge/PyTorch-CPU-EE4C2C.svg)](https://pytorch.org/)
[![HuggingFace](https://img.shields.io/badge/Transformers-DistilBERT-yellow.svg)](https://huggingface.co/)
[![Tests](https://img.shields.io/badge/Tests-86%20Passed-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-green.svg)]()

**CareerAI** is a comprehensive, production-ready AI/ML career advancement platform. It extracts candidate technical proficiencies from resumes, classifies candidates across 24 industry categories using a custom fine-tuned **DistilBERT** model, computes dense semantic alignment with target job descriptions using **Sentence-BERT** (`all-MiniLM-L6-v2`), generates actionable 30-day and 60-day personalized learning roadmaps with canonical free learning resources, and provides an instant contextual career guidance chatbot backed by a deterministic Guided Career Advisor with local **Ollama** LLM support.

---

## Architecture Overview

```
                                +-----------------------------------+
                                |     React 19 + Vite Frontend      |
                                | (Tailwind CSS, Lucide, Recharts)  |
                                +-----------------+-----------------+
                                                  | REST (JSON / Bearer JWT)
                                                  v
                                +-----------------------------------+
                                |        FastAPI Backend App        |
                                |  (RateLimiter, SecurityHeaders,   |
                                |   Sanitized Exception Handlers)   |
                                +-----------------+-----------------+
                                                  |
        +-------------------------+---------------+-------------------------+
        |                         |                                         |
        v                         v                                         v
+------------------+     +------------------+                     +------------------+
| Document Parser  |     |  DistilBERT CPU  |                     |  Sentence-BERT   |
| (PyMuPDF / Docx) |     |  24-Class Model  |                     | (all-MiniLM-L6)  |
| Skill Extractor  |     | Category & Conf. |                     | Dense Embedding  |
+------------------+     +------------------+                     +------------------+
        |                         |                                         |
        +-------------------------+---------------+-------------------------+
                                                  |
                                                  v
                                +-----------------------------------+
                                |  Career Decision & Roadmap Engine |
                                |  - 30-Day & 60-Day Milestones     |
                                |  - Resume Readiness Scoring       |
                                |  - Guided AI Assistant / Ollama   |
                                +-----------------+-----------------+
                                                  |
                                                  v
                                +-----------------------------------+
                                |  Data Persistence & Privacy Layer |
                                |  - MongoDB Atlas (M0 Free Tier)   |
                                |  - Embedded SQLite (Fallback)     |
                                |  - Strict Opt-In PII Privacy      |
                                +-----------------------------------+
```

---

## Key Features & Capabilities

### 1. Document Extraction & Skill Mining
- High-fidelity PDF and DOCX parsing using PyMuPDF and python-docx in memory.
- Multilingual skill dictionary matching over 150+ software engineering, data science, devops, and cloud skills.
- Automatic extraction and sanitization of contact info, education levels (including 10th/12th/B.Tech), and projects.

### 2. Multi-Class Job Domain Prediction (DistilBERT)
- Fine-tuned `distilbert-base-uncased` classifier operating on CPU.
- 24 standardized industry categories (e.g., *Information Technology*, *Data Science*, *Software Engineering*, *Cloud & DevOps*, *Database Administration*).
- Outputs top-3 ranked categories with calibrated softmax confidence scores and low-confidence advisories (< 30%).

### 3. Dense Semantic Matching & Gap Analysis (Sentence-BERT)
- Hugging Face `all-MiniLM-L6-v2` embedding pipeline with attention-mask-aware mean pooling and L2 normalization.
- Computes mathematical cosine similarity against live job descriptions without hardcoded strings or paid APIs.
- Identifies matching skills, missing skills, and overall skill coverage percentages.

### 4. Resume Improvement Suggestions & Structural Readiness Score
- Computes a multi-category structural readiness score (0–100) evaluating Skill Breadth, Experience Detail, Education Credentials, Contact Completeness, and Impact Metrics.
- Detects passive bullet points and suggests Google XYZ formula rewrites (`Accomplished [X] as measured by [Y] by doing [Z]`).
- Highlights critical alerts, role-specific missing skills, and actionable advice.

### 5. Explainable Career Recommendations & Personalized Roadmaps
- Classifies recommended roles into **Strong Match** ($\ge 50\%$ overlap, or $\ge 40\%$ within primary domain), **Alternative Career Path** ($15\% \le \text{overlap} < 50\%$), and **Exploratory Track** ($< 15\%$).
- Generates structured **30-day (4-week)** and **60-day (8-week)** roadmaps featuring weekly objectives, target skills, practical exercises, deliverables, and canonical free learning resources (MDN, Python.org, freeCodeCamp, etc.).
- Transparent candidate skill accounting (matched skills + transferable skills).

### 6. Hybrid AI Career Assistant Chatbot
- Context-aware chatbot grounded directly in candidate skills, top prediction domains, skill gaps, and active roadmap targets.
- **Dual Engine Design:**
  - **Deterministic Guided Career Advisor:** Instant CPU fallback responding in < 5 ms with zero external dependencies, network calls, or paid API keys.
  - **Local Ollama Integration:** Asynchronously queries local Qwen 2.5 3B (`127.0.0.1:11434`) when running locally.
- PII-sanitized grounding prompts preventing candidate leaks.

### 7. Persistent User History & Dashboard Analytics
- Secure JWT-based authentication (PBKDF2/bcrypt hashing, HS256 tokens, 60-min expiration).
- Multi-session history storage with 1-click workspace snapshot restoration.
- Dashboard analytics showing top skills frequency, domain distribution, and chronological score progression across multiple uploads.

### 8. Strict Privacy & Security Standards
- **Zero-Storage Privacy Mode:** Candidate resume raw text is discarded immediately upon prediction unless explicit opt-in consent is provided.
- **Security Headers:** Enforces `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection`, and `Referrer-Policy`.
- **API Rate Limiting:** Sliding window token limiter mitigating brute-force and credential-stuffing attacks.
- **Cascading Deletion:** Complete user account and historical data can be permanently erased in a single transaction with immediate token blacklisting.

---

## Directory Structure

```text
AI Job Prediction System/
│
├── backend/
│   ├── app/
│   │   ├── api/            # REST API endpoints (auth, resume, prediction, matching, roadmap, suggestions, assistant, history)
│   │   ├── core/           # Security, JWT, middleware, rate limiting, and dual database (MongoDB/SQLite)
│   │   ├── schemas/        # Strict Pydantic v2 schemas for all payloads and responses
│   │   ├── services/       # Core business & ML engines (PyMuPDF, DistilBERT, Sentence-BERT, Roadmap, Assistant)
│   │   └── main.py         # FastAPI application entrypoint with security middlewares and exception handlers
│   ├── ml/
│   │   └── saved_models/   # Serialized DistilBERT and Sentence-BERT weights, configs, and label maps
│   ├── tests/              # 86 automated Pytest suites covering unit, schema, security, and E2E lifecycles
│   ├── requirements.txt    # Production Python dependencies
│   └── Dockerfile          # Production container configuration for free cloud deployment
│
├── frontend/
│   ├── src/
│   │   ├── components/     # Reusable UI widgets (ErrorBoundary, ScoreCard, RadarCharts, Modal)
│   │   ├── context/        # React context providers (AuthContext, ResumeContext)
│   │   ├── pages/          # Full page views (Dashboard, ResumeAnalysis, JobMatching, Recommendations, Roadmap, Suggestions, Assistant, History, Login, Register)
│   │   ├── services/       # Axios API client with automatic token attachment and 401 interceptors
│   │   └── App.jsx         # Client-side routing, protected routes, and layout wrappers
│   ├── package.json        # Frontend dependencies and scripts
│   └── vercel.json         # Vercel SPA routing rewrite rules
│
├── .env.example            # Environment variable template
├── .gitignore              # Strict ignore rules excluding .db, .env, .venv, node_modules, and model binaries
├── DEPLOYMENT.md           # Free cloud hosting evaluation and setup guide (Vercel + Hugging Face / Render)
└── README.md               # Complete project documentation
```

---

## Quickstart Guide

### Prerequisites
- **Python 3.11+** installed
- **Node.js 18+** and **npm** installed
- *(Optional)* [Ollama](https://ollama.ai) installed locally if running local LLM chat

### Step 1: Clone Repository
```bash
git clone https://github.com/<your-username>/careerai.git
cd careerai
```

### Step 2: Backend Setup
1. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .\.venv\Scripts\Activate.ps1
   # macOS / Linux:
   source .venv/bin/activate
   ```
2. Install Python dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Create your local environment file:
   ```bash
   cp .env.example .env
   ```
4. Start the FastAPI backend server:
   ```bash
   uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   *The backend will automatically start with the embedded SQLite database (`backend/data/careerai.db`) if no MongoDB URI is set.*

### Step 3: Frontend Setup
1. Open a new terminal and navigate to `frontend/`:
   ```bash
   cd frontend
   npm install
   ```
2. Start the Vite development server:
   ```bash
   npm run dev
   ```
3. Open your browser and visit: **`http://localhost:5173`**

---

## Automated Test Suite

CareerAI features 86 automated backend test cases covering all services, input edge cases, schema validations, security headers, rate limiting, and an end-to-end user lifecycle test.

Run the complete test suite:
```bash
python -m pytest backend/tests/ -v
```

### Test Breakdown
| Test Module | Tests | Description |
| :--- | :---: | :--- |
| `test_auth.py` | 11 | Registration, bcrypt verification, login, profile, logout, account deletion |
| `test_resume.py` | 13 | PyMuPDF PDF parsing, docx parsing, skill extraction, corrupted file rejection |
| `test_prediction.py` | 11 | DistilBERT model loading, top-3 ranks, confidence thresholds, edge-case texts |
| `test_matching.py` | 10 | Sentence-BERT vector similarity, chunking, skill gaps, cosine bounds |
| `test_roadmap.py` | 10 | Available roles, 30/60-day roadmaps, verified canonical free links, disclaimers |
| `test_suggestions.py` | 5 | Structural readiness scores (0-100), critical alerts, XYZ bullet rewrite examples |
| `test_assistant.py` | 7 | Deterministic Guided Advisor intents, fallback routing, zero-PII prompt checks |
| `test_history.py` | 10 | Analysis persistence, privacy enforcement, multi-user isolation, analytics |
| `test_security.py` | 6 | Security headers, tamper rejection, rate limiting bursts, sanitized errors |
| `test_e2e_workflow.py` | 1 | Complete 11-step end-to-end candidate lifecycle validation |
| `test_health.py` | 2 | Root and health check ping |
| **Total** | **86** | **All 86 Passing** |

---

## API Reference Summary

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `GET` | `/api/health` | System health and model availability status | No |
| `POST` | `/api/auth/register` | Register new user account | No |
| `POST` | `/api/auth/login` | Authenticate and obtain JWT access token | No |
| `GET` | `/api/auth/me` | Retrieve authenticated user profile | Bearer JWT |
| `DELETE` | `/api/auth/account` | Permanently delete account and all history | Bearer JWT |
| `POST` | `/api/resume/analyze` | Upload and parse PDF/DOCX resume | Optional |
| `POST` | `/api/predictions/job-role` | Predict top-3 job categories via DistilBERT | Optional |
| `POST` | `/api/match/job-description` | Compute semantic match via Sentence-BERT | Optional |
| `POST` | `/api/suggestions/analyze` | Generate resume improvement suggestions & score | Optional |
| `POST` | `/api/roadmap/recommendations` | Get explainable career path matches | Optional |
| `POST` | `/api/roadmap/generate` | Generate 30-day or 60-day milestone roadmap | Optional |
| `POST` | `/api/assistant/chat` | Query AI career chatbot (Guided Advisor / Ollama) | Optional |
| `POST` | `/api/history/save` | Save or update analysis session snapshot | Bearer JWT |
| `GET` | `/api/history` | List candidate past analysis records | Bearer JWT |
| `GET` | `/api/history/{record_id}` | Retrieve full historical snapshot for restore | Bearer JWT |
| `GET` | `/api/history/analytics` | Retrieve aggregated analytics and skill trends | Bearer JWT |

---

## Ethical AI & Hiring Disclaimers

> **IMPORTANT NOTICE:**  
> CareerAI is designed solely as an educational career guidance and skill development tool.
>
> 1. **Not a Hiring Guarantee:** Match percentages and DistilBERT category confidences reflect semantic document similarity and text token overlap—**not** the probability of receiving an interview, job offer, or employment outcome.
> 2. **Holistic Hiring:** Human hiring decisions evaluate team culture fit, soft skills, communication, problem-solving, and professional references that automated document parsers cannot evaluate.
> 3. **Non-Discriminatory Design:** The platform does not use demographic attributes (age, gender, ethnicity, location) in model inference or career recommendations.
> 4. **Verified Free Resources:** All learning materials recommended in learning roadmaps are canonical, open-access, and strictly 100% free of charge.

---

## Deployment

Refer to [DEPLOYMENT.md](file:///c:/Users/boyap/Desktop/AI%20Job%20Prediction%20System/DEPLOYMENT.md) for full instructions on deploying CareerAI with **zero cloud costs**:
- **Frontend:** Vercel Hobby Free Tier (Global CDN, automated Git deployments).
- **Backend ML:** Hugging Face Spaces Docker (Free 2 vCPU, 16 GB RAM) eliminating OOM risks on ML inference.
- **Database:** MongoDB Atlas M0 Shared Free Tier (512 MB permanent storage).

---

## License

This project is licensed under the MIT License — see the LICENSE file for details.
