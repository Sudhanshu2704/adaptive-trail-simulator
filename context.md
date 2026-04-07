# Project: Adaptive Trial Simulator

## What this project does
A locally hosted web application designed for LLM-guided clinical trial simulation. It uses autonomous agents to simulate clinical trials while storing data locally.

## Tech stack
- Language: Python 3.11 (Backend), JavaScript/JSX (Frontend)
- Framework: FastAPI (Backend), React + Vite (Frontend)
- Database: PostgreSQL
- LLM/Agents: LangGraph, Langchain-Ollama (connecting to local Ollama instance)
- Styling: Tailwind CSS
- Data Visualization: Recharts
- Containerization: Docker & Docker Compose

## Folder structure
adaptive-trial-simulator/
├── backend/            # Python backend using FastAPI and LangGraph
│   ├── app/            # Main application logic (api, core, engine, agent)
│   ├── tests/          # Backend testing setup
│   ├── Dockerfile      # Docker setup for backend
│   └── pyproject.toml  # Poetry dependencies
├── frontend/           # React + Vite frontend
│   ├── src/            # React components, styles (App.jsx)
│   ├── Dockerfile      # Docker setup for frontend
│   └── package.json    # Node dependencies
├── docker-compose.yml  # Local services orchestration (db, backend, frontend, ollama)
└── context.md          # This file

## Features built so far
- [x] Basic project scaffolding for FastAPI backend and Vite/React frontend
- [x] Docker compose configuration for running Database, Backend, and Frontend together
- [x] Local LLM integration using Langchain-Ollama with LangGraph
- [x] Implement core simulation engine logic and API integration
- [x] Build interactive trial flow on the frontend (Recharts visualizer and AI Event Timeline)
- [x] Graceful error handling and loading UI states implemented
- [x] Recharts responsive container UI fixed and fully integrated Ollama service into docker-compose
- [x] Implement Bayesian Statistics (replace basic scipy t-test with PyMC/numpyro)
- [x] Adaptive Randomization (dynamic patient allocation ratio based on arm performance)
- [x] Database Persistence (write trial logs, LLM decisions, and phase histories to PostgreSQL)
- [x] Unit Testing (pytest) for deterministic math functions
- [x] Agent Testing (mock tests for LangGraph workflow and Pydantic schemas)
- [ ] GitHub Actions (CI/CD pipeline for automated Docker builds and testing)
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

## Current errors / known issues
- None right now

## How to run this project
Run `docker-compose up --build`
Then open your browser to:
- Frontend: http://localhost:5173
- Backend API Docs: http://localhost:8000/docs