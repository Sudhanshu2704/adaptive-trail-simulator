# Project: Adaptive Trial Simulator

## What this project does
A web application for LLM-guided clinical trial simulation. Users configure multi-arm trial parameters, run Bayesian-adaptive simulations driven by a LangGraph agent, and review results and trial history persisted to PostgreSQL. Designed to be deployable entirely on free-tier infrastructure.

## Tech stack
- Language: Python 3.11 (Backend), JavaScript/JSX (Frontend)
- Framework: FastAPI (Backend), React + Vite (Frontend)
- Database: PostgreSQL (local via Docker; production via Supabase free tier)
- LLM/Agents: LangGraph, LangChain — supports Ollama (local) and Groq API (cloud) via `LLM_PROVIDER` env toggle
- Bayesian Statistics: NumPyro + JAX (NUTS/MCMC sampler — Bayesian Estimation Superseding the T-test)
- Styling: Tailwind CSS
- Data Visualization: Recharts
- Containerization: Docker & Docker Compose (local), `docker-compose.prod.yml` (production override)
- Testing: pytest (unit + agent mock tests)
- CI/CD: GitHub Actions (CI tests + frontend deploy to GitHub Pages + backend image push to ghcr.io)
- Deployment (free): GitHub Pages (frontend), Render.com (backend), Supabase (database), Groq (LLM)

## Folder structure
```
adaptive-trial-simulator/
├── .env.example                 # Documents required env vars (GROQ_API_KEY, DATABASE_URL, etc.)
├── .github/
│   └── workflows/
│       ├── ci.yml               # Runs pytest + frontend build on every push
│       ├── deploy-frontend.yml  # Builds Vite + deploys to GitHub Pages on push to main
│       └── deploy-backend.yml   # Builds Docker image, pushes to ghcr.io, triggers Render deploy
├── backend/                     # Python backend using FastAPI and LangGraph
│   ├── app/
│   │   ├── agent/               # LangGraph graph, schemas, tools, LLM config (Ollama/Groq toggle)
│   │   ├── api/                 # FastAPI route endpoints (simulate + history)
│   │   ├── core/                # SQLAlchemy database config and ORM models
│   │   └── engine/              # Trial simulation engine (cohorts.py, stats.py)
│   ├── tests/                   # pytest suite (test_engine, test_agent, test_stats)
│   ├── Dockerfile               # Docker setup for backend
│   └── pyproject.toml           # Poetry dependencies (numpyro, langgraph, langchain-groq, pytest)
├── frontend/                    # React + Vite frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── TrialConfigForm.jsx  # Trial configuration form (arms, effects, phases, threshold)
│   │   │   └── TrialHistory.jsx     # History table + detail view from DB
│   │   └── App.jsx              # Main app with tab navigation (Run Trial | History)
│   ├── Dockerfile               # Docker setup for frontend
│   ├── vite.config.js           # Vite config with GitHub Pages base path
│   └── package.json             # Node dependencies
├── docker-compose.yml           # Local dev: db + backend + frontend + ollama
├── docker-compose.prod.yml      # Production override: no ollama, uses Supabase + Groq
└── context.md                   # This file
```

## Features: Completed
- [x] Project scaffolding — FastAPI backend, Vite/React frontend
- [x] Docker Compose — Database, Backend, Frontend, Ollama containerized together
- [x] Local LLM integration — LangChain + LangGraph connected to local Ollama instance
- [x] Core simulation engine — VirtualTrialEngine (cohorts.py) + Bayesian stats (stats.py)
- [x] Frontend — Recharts line chart + AI Event Timeline on simulation result
- [x] Error handling + loading UI states
- [x] Bayesian Statistics — NumPyro NUTS/MCMC; outputs prob_superior, pseudo p-value, Bayesian boolean flags
- [x] Adaptive Randomization (exponential Thompson-weight proxy) — shifts patients toward better arms each phase
- [x] Database Persistence — SQLAlchemy ORM writes TrialSession + PhaseLog to PostgreSQL on every run
- [x] Timezone — TZ=Asia/Kolkata in docker-compose for correct local timestamps
- [x] MCMC speed optimization — 200 warmup / 500 samples (~3x faster vs original)
- [x] Unit Tests — 11 deterministic pytest tests for VirtualTrialEngine
- [x] Agent Tests — 13 mock pytest tests for LangGraph nodes
- [x] GitHub Actions CI — passes on master; runs fast suite (24 tests) on every push

## Features: In Progress (v1.0 Roadmap)

### Phase 1 — Make It Actually Functional
- [ ] **Configurable Trial Form** — Let user set arm count, arm names, effect sizes, patients/arm, max phases, stopping threshold. Currently everything is hardcoded.
- [ ] **Trial History Page** — Read TrialSession + PhaseLog back from DB. Add `GET /api/v1/trials` and `GET /api/v1/trials/{id}` endpoints. Frontend History tab shows all past runs.
- [ ] **Real Stopping Rules** — Replace hardcoded `phase > 3 → END` with user-configured `max_phases` and Bayesian posterior threshold (e.g., stop arm if `prob_superior > 0.95`). Pass these through `TrialState`.
- [ ] **Real Thompson Sampling** — Replace `math.exp()` weight proxy with Beta distribution posterior sampling (`np.random.beta(alpha, beta)`). Requires cohort engine to return response counts.
- [ ] **CSV Export** — "Download CSV" button after simulation: exports phase-by-phase arm stats.

### Phase 2 — Deploy It (Free)
- [ ] **LLM Provider Toggle** — `LLM_PROVIDER=groq|ollama` env var in `llm_config.py`. Groq API key stored as GitHub Secret + Render env var. Eliminates 60s/phase Ollama inference time.
- [ ] **`docker-compose.prod.yml`** — Production override: no Ollama service, uses Supabase DATABASE_URL, sets LLM_PROVIDER=groq.
- [ ] **`.env.example`** — Document all required env vars: `GROQ_API_KEY`, `DATABASE_URL`, `LLM_PROVIDER`, `ALLOWED_ORIGINS`.
- [ ] **Dynamic CORS** — `main.py` reads `ALLOWED_ORIGINS` from env; defaults to localhost for local dev.
- [ ] **`deploy-frontend.yml`** — GitHub Action: build Vite → deploy `dist/` to GitHub Pages on push to main.
- [ ] **`deploy-backend.yml`** — GitHub Action: build Docker image → push to `ghcr.io` → trigger Render deploy hook.
- [ ] **Supabase** — Create free project, store `DATABASE_URL` as GitHub Secret `SUPABASE_DATABASE_URL`.
- [ ] **Render** — Deploy backend from `ghcr.io` image. Set env vars via Render dashboard.
- [ ] **Extend `ci.yml`** — Add `npm run build` step to catch frontend breakage on every push.

### Phase 3 — Future
- [ ] Sample size calculator widget
- [ ] PDF report export (WeasyPrint / ReportLab)
- [ ] Multi-user trial profiles (Supabase Auth)
- [ ] Published arm comparison across historical trials

## Key decisions made
- PostgreSQL over SQLite — more robust, needed for multi-run history queries.
- FastAPI — async, typed, auto-generates Swagger docs at `/docs`.
- LangGraph — handles the cyclic collect→reason→route agent loop cleanly.
- NumPyro NUTS/MCMC (BEST method) — outputs P(treatment > control) directly, more interpretable for LLM prompt than frequentist p-values.
- Recharts — flexible, React-native chart library; works well with dynamic arm keys.
- Thompson Sampling weights — exponential weight proxy worked as initial placeholder; will be replaced with real Beta posterior sampling.
- pytest split into fast/slow — CI runs only fast suite (<4s, 24 tests); `@pytest.mark.slow` guards MCMC tests from pipeline.
- `vite.config.js` already has `base: '/adaptive-trail-simulator/'` for correct GitHub Pages routing.
- Deployment stack chosen entirely on free-tier availability: Render (backend), GitHub Pages (frontend), Supabase (DB), Groq (LLM).
- No AWS, Azure, or GCP — cost and complexity are unnecessary for this project scope.

## Current known issues
- Simulation wall-clock time is slow (~1-2 min) on local Ollama CPU inference per phase. Fix: LLM_PROVIDER=groq toggle (Phase 2).
- `tools.py` has hardcoded `true_effects = {"Control": 0.0, "Arm_A": 0.1, "Arm_B": 1.2}` — dynamic arm names from the form will break this. Must be fixed in Phase 1.
- DB is write-only — no read endpoints exist yet. History tab depends on this.
- Stopping logic caps at 3 phases unconditionally. Must be replaced with real configurable rules.
- CORS allows only `localhost:5173` — must be env-configurable before Render deployment.

## How to run locally
```bash
docker-compose up --build
```
Then open:
- Frontend: http://localhost:5173
- Backend API Docs: http://localhost:8000/docs

## How to run tests
```bash
cd backend
poetry run pytest -m "not slow" -v     # Fast suite (24 tests, ~4s)
poetry run pytest -v                    # Full suite including Bayesian MCMC tests
```

## Environment variables reference
| Variable | Where Used | Example |
|---|---|---|
| `DATABASE_URL` | Backend | `postgresql://admin:pass@db:5432/clinical_trials` |
| `LLM_PROVIDER` | Backend | `ollama` or `groq` |
| `GROQ_API_KEY` | Backend (Groq mode) | `gsk_...` |
| `OLLAMA_BASE_URL` | Backend (Ollama mode) | `http://ollama:11434` |
| `ALLOWED_ORIGINS` | Backend | `https://user.github.io,http://localhost:5173` |
| `VITE_API_URL` | Frontend build | `https://your-app.onrender.com` |