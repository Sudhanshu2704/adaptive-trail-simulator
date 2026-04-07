# AI Adaptive Trial Simulator

A fully functional, locally hosted web application that simulates clinical trials using LLM-driven autonomous agents.

## 🚀 The Core Concept: LangGraph State Machine

This project leverages **LangGraph** to model an adaptive clinical trial as a cyclic State Machine workflow:

1. **Collect Data Node:** In each simulated phase of the trial, virtual cohorts are evaluated. Statistical data (like p-values and mean differences) are calculated against a Control arm.
2. **Reasoning Node:** A local LLM (running via Ollama) evaluates this statistical output. As the "Principal Investigator", the LLM looks at the data to decide the future of the trial:
   - Should it continue? (`CONTINUE`)
   - Can an underperforming arm be dropped? (`STOP_ARM_FUTILITY`)
   - Did a drug succeed early? (`STOP_TRIAL_SUCCESS`)
3. **Engine Evaluation:** The LangGraph state holds onto active arms, history, and phase counters. The trial dynamically updates parameters and routes back to data collection based on the LLM's decision until completion.

## 🏗 Architecture

- **Backend Context:** 
  - Written in **Python 3.11** using **FastAPI** for robust, high-performance routing.
  - LLM logic is managed by **LangChain** and **LangGraph**.
  - PostgreSQL is used for underlying data management and relations.
- **Frontend Context:**
  - Designed as a React Single Page Application created with **Vite**.
  - Advanced data visualizations power the dashboard using **Recharts**.
  - Modern, responsive styling implemented using **Tailwind CSS**.
- **Containerization:** The entire environment (Database, Backend, Frontend) is glued together using **Docker Compose** for a seamless developer experience without dependency headaches.

## 🔧 Getting Started

### Prerequisites

Ensure you have the following installed on your machine:
- [Docker](https://www.docker.com/) & Docker Compose
- [Ollama](https://ollama.com/) (Must be installed and running *locally* on your host machine to serve the LLM)

### 1. Model Configuration

First, make sure your local Ollama instance has pulled the required model used by the AI Agent (e.g., `llama3` or `mistral`, based on your LangChain configuration).
```bash
ollama pull llama3
```

### 2. Startup

To run the application, navigate to the project's root folder and simply trigger docker-compose:

```bash
docker-compose up --build
```

### 3. Usage

Once Docker containerizes and spins up the environments, you can access the application at:
- **Frontend Dashboard:** [http://localhost:5173](http://localhost:5173)
- **Backend API Docs (Swagger Profile):** [http://localhost:8000/docs](http://localhost:8000/docs)

Click "Start Trial" on the Frontend UI to trigger a fresh multi-arm trial simulation through LangGraph!
