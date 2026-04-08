from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.core.database import get_db
from app.core.models import TrialSession, PhaseLog

history_router = APIRouter()


@history_router.get("/trials", response_model=List[Dict[str, Any]])
def list_trials(db: Session = Depends(get_db)):
    """Returns a summary list of all past trial runs, newest first."""
    trials = db.query(TrialSession).order_by(TrialSession.id.desc()).limit(50).all()
    return [
        {
            "id": t.id,
            "status": t.status,
            "initial_arms": t.initial_arms,
            "final_phase": t.final_phase,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in trials
    ]


@history_router.get("/trials/{trial_id}", response_model=Dict[str, Any])
def get_trial(trial_id: int, db: Session = Depends(get_db)):
    """Returns the full phase-by-phase event log for a specific trial."""
    trial = db.query(TrialSession).filter(TrialSession.id == trial_id).first()
    if not trial:
        raise HTTPException(status_code=404, detail=f"Trial {trial_id} not found.")

    logs = (
        db.query(PhaseLog)
        .filter(PhaseLog.trial_id == trial_id)
        .order_by(PhaseLog.id.asc())
        .all()
    )

    return {
        "id": trial.id,
        "status": trial.status,
        "initial_arms": trial.initial_arms,
        "final_phase": trial.final_phase,
        "created_at": trial.created_at.isoformat() if trial.created_at else None,
        "history": [log.data_payload for log in logs],
    }
