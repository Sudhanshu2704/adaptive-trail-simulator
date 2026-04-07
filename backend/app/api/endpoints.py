from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.agent.graph import adaptive_trial_app
from app.core.database import get_db
from app.core.models import TrialSession, PhaseLog

# Initialize the router that main.py is looking for
router = APIRouter()

# Define the expected JSON payload from the React frontend
class TrialRequest(BaseModel):
    arms: List[str] = ["Control", "Arm_A", "Arm_B"]
    patients_per_arm: int = 50

@router.post("/simulate-trial")
async def simulate_trial(request: TrialRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Triggers the LangGraph AI agent to run a clinical trial simulation.
    """
    try:
        # 1. Setup the initial state for the state machine
        initial_state = {
            "active_arms": request.arms,
            "patient_count_per_arm": request.patients_per_arm,
            "current_phase": 1,
            "is_completed": False,
            "trial_history": [],
            "messages": []
        }
        
        # 2. Execute the LangGraph workflow
        result = adaptive_trial_app.invoke(initial_state)
        
        # 3. Format the output cleanly for the React frontend
        final_phase = result["current_phase"] - 1
        history = result["trial_history"]
        active_arms_remaining = result["active_arms"]
        
        # 4. Persist the Trial and its Logs to PostgreSQL
        trial_record = TrialSession(
            status="completed" if result["is_completed"] else "stopped_early",
            initial_arms=request.arms,
            final_phase=final_phase
        )
        db.add(trial_record)
        db.commit()
        db.refresh(trial_record)
        
        for phase_event in history:
            phase_log = PhaseLog(
                trial_id=trial_record.id,
                phase_number=phase_event.get("phase"),
                event_type=phase_event.get("type"),
                data_payload=phase_event
            )
            db.add(phase_log)
            
        db.commit()

        return {
            "status": "success",
            "final_phase": final_phase,
            "active_arms_remaining": active_arms_remaining,
            "history": history
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))