import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router
from app.api.history_endpoints import history_router
from app.core.database import engine, Base
import app.core.models  # Loads ORM models so Base.metadata is populated

# Auto-generate DB schema on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Adaptive Clinical Trial API",
    description="LangGraph-powered Bayesian adaptive clinical trial simulator",
    version="1.0.0",
)

# Dynamic CORS — read from env so localhost dev and GitHub Pages both work
raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
allowed_origins = [origin.strip() for origin in raw_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")
app.include_router(history_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    llm_provider = os.getenv("LLM_PROVIDER", "ollama")
    return {"status": "healthy", "llm_provider": llm_provider}