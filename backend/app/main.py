from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router
from app.core.database import engine, Base
import app.core.models  # Implicitly loads the models

# Auto-generate DB schema (for simple initialization)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Adaptive Clinical Trial API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {"status": "healthy", "llm": "local_ollama"}