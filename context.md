# Project: Adaptive Trial Simulator

## What this project does
A locally hosted web application designed for LLM-guided clinical trial simulation. It uses autonomous agents to simulate clinical trials, applying Bayesian statistics and adaptive patient allocation, while persisting all results to a PostgreSQL database.

## Tech stack
- Language: Python 3.11 (Backend), JavaScript/JSX (Frontend)
- Framework: FastAPI (Backend), React + Vite (Frontend)
- Database: PostgreSQL
- LLM/Agents: LangGraph, Langchain-Ollama (connecting to local Ollama instance)
- Bayesian Statistics: NumPyro + JAX (NUTS/MCMC sampler)
- Styling: Tailwind CSS
- Data Visualization: Recharts
- Containerization: Docker & Docker Compose
- Testing: pytest (unit + agent mock tests)
- CI/CD: GitHub Actions

## Folder structure
adaptive-trial-simulator/
├── .github/
│   └── workflows/
│       ├── ci.yml          # Runs pytest on every push to master/main/dev
│       └── deploy.yml      # Deploys frontend to GitHub Pages on push to main
├── backend/                # Python backend using FastAPI and LangGraph
│   ├── app/
│   │   ├── agent/          # LangGraph graph, schemas, tools, LLM config
│   │   ├── api/            # FastAPI route endpoints
│   │   ├── core/           # SQLAlchemy database config and ORM models
│   │   └── engine/         # Trial simulation engine (cohorts.py, stats.py)
│   ├── tests/              # pytest suite (test_engine, test_agent, test_stats)
│   ├── Dockerfile          # Docker setup for backend
│   └── pyproject.toml      # Poetry dependencies (includes numpyro, pytest)
├── frontend/               # React + Vite frontend
│   ├── src/                # React components, styles (App.jsx)
│   ├── Dockerfile          # Docker setup for frontend
│   ├── vite.config.js      # Vite config with GitHub Pages base path set
│   └── package.json        # Node dependencies
├── docker-compose.yml      # Local services orchestration (db, backend, frontend, ollama)
└── context.md              # This file

## Features built so far
- [x] Basic project scaffolding for FastAPI backend and Vite/React frontend
- [x] Docker compose configuration for running Database, Backend, and Frontend together
- [x] Local LLM integration using Langchain-Ollama with LangGraph
- [x] Implement core simulation engine logic and API integration
- [x] Build interactive trial flow on the frontend (Recharts visualizer and AI Event Timeline)
- [x] Graceful error handling and loading UI states implemented
- [x] Recharts responsive container UI fixed and fully integrated Ollama service into docker-compose
- [x] Implement Bayesian Statistics (replaced scipy t-test with NumPyro NUTS/MCMC — outputs prob_superior, pseudo p-value, Bayesian boolean flags)
- [x] Adaptive Randomization (Thompson Sampling — exponential weighting shifts patients toward better-performing arms each phase)
- [x] Database Persistence (SQLAlchemy ORM — TrialSession and PhaseLog tables write all trial events to PostgreSQL on every simulation)
- [x] Timezone fix (TZ=Asia/Kolkata set in docker-compose so all logs and DB timestamps reflect local time)
- [x] MCMC speed optimization (reduced from 500 warmup/1000 samples to 200/500 — ~3x faster per arm)
- [x] Unit Testing — 11 deterministic pytest tests for VirtualTrialEngine (cohort sizes, seeding, arm dropout, mean accuracy)
- [x] Agent Testing — 13 mock pytest tests for LangGraph nodes (adaptive allocation, LLM decisions, routing logic, state mutations)
- [x] GitHub Actions CI — live and passing on master branch; auto-runs all 24 fast tests on every push
- [ ] Container Registry integration (push images to Docker Hub/AWS ECR)
- [ ] Hook system up to a Managed Cloud Database (AWS RDS or Supabase)
- [ ] Cloud Hosting (deploy backend to Render/Railway, frontend to GitHub Pages)
- [ ] API Toggle (switch between local Ollama and hosted Groq/OpenAI APIs for cloud deployment)

## Key decisions made
- Using PostgreSQL instead of SQLite for more robust relational data handling, containerized via Docker.
- Employing FastAPI for a high-performance Python backend API.
- Connecting to a local Ollama instance for free, secure, and private LLM inferences.
- Using React with Vite and TailwindCSS for a fast and modern frontend developer experience.
- Structuring with LangGraph to handle agent-based workflows.
- Implemented Recharts for robust data visualization to transform raw JSON output into a dynamic analytical dashboard.
- Utilized a containerized Ollama instance mapped via docker-compose network (http://ollama:11434) to avoid missing host dependencies and standardize the environment.
- Replaced frequentist t-test with Bayesian Estimation (BEST) using NumPyro — outputs probability of superiority instead of p-values, making LLM decision-making more principled.
- Adaptive randomization uses exponential Thompson Sampling weights derived from Bayesian t_statistic (prob_superior) to dynamically reallocate patients each phase.
- Pytest suite split into fast (no MCMC, <4s for 24 tests) and slow (full Bayesian, marked `@pytest.mark.slow`) layers for CI efficiency.
- GitHub Actions CI configured to skip slow MCMC tests (`-m "not slow"`) to keep pipeline under 40 seconds.
- Frontend vite.config.js has `base: '/adaptive-trail-simulator/'` set for correct GitHub Pages asset routing.

## Current errors / known issues
- Simulation wall-clock time is still slow (~1-2 min) due to local CPU-only Ollama LLM inference (~30-60s per phase). Planned fix: API Toggle to Groq for cloud deployment.
- GitHub Pages deployment workflow (`deploy.yml`) currently disabled — requires public repo or GitHub Pro plan to activate.

## How to run this project
Run `docker-compose up --build`
Then open your browser to:
- Frontend: http://localhost:5173
- Backend API Docs: http://localhost:8000/docs

## How to run tests
```
cd backend
poetry run pytest -m "not slow" -v     # Fast suite (24 tests, ~4s)
poetry run pytest -v                    # Full suite including Bayesian MCMC tests
```