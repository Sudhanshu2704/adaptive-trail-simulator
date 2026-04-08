from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.agent.graph import adaptive_trial_app
from app.core.database import get_db
from app.core.models import TrialSession, PhaseLog

router = APIRouter()


class ArmConfig(BaseModel):
    name: str = Field(..., description="Arm name, e.g. 'Arm_A'")
    effect_size: float = Field(..., ge=0.0, le=5.0, description="Hypothesized effect size relative to control")


class TrialRequest(BaseModel):
    arms: List[ArmConfig] = Field(
        default=[
            ArmConfig(name="Control", effect_size=0.0),
            ArmConfig(name="Arm_A", effect_size=0.5),
            ArmConfig(name="Arm_B", effect_size=1.2),
        ],
        description="List of trial arms with their hypothesized effect sizes",
    )
    patients_per_arm: int = Field(default=50, ge=20, le=200)
    max_phases: int = Field(default=5, ge=2, le=10)
    stopping_threshold: float = Field(
        default=0.95,
        ge=0.80,
        le=0.999,
        description="Bayesian posterior probability threshold to declare trial success",
    )


@router.post("/simulate-trial")
async def simulate_trial(request: TrialRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Triggers the LangGraph AI agent to run a fully configurable clinical trial simulation.
    """
    try:
        arm_names = [a.name for a in request.arms]
        arm_effects = {a.name: a.effect_size for a in request.arms}

        # Ensure Control arm is always present
        if "Control" not in arm_effects:
            arm_effects["Control"] = 0.0
            arm_names.insert(0, "Control")

        initial_state = {
            "active_arms": arm_names,
            "patient_count_per_arm": request.patients_per_arm,
            "current_phase": 1,
            "is_completed": False,
            "trial_history": [],
            "messages": [],
            "max_phases": request.max_phases,
            "stopping_threshold": request.stopping_threshold,
            "arm_effects": arm_effects,
        }

        result = adaptive_trial_app.invoke(initial_state)

        final_phase = result["current_phase"] - 1
        history = result["trial_history"]
        active_arms_remaining = result["active_arms"]

        # Persist to PostgreSQL
        trial_record = TrialSession(
            status="completed" if result["is_completed"] else "stopped_early",
            initial_arms=arm_names,
            final_phase=final_phase,
        )
        db.add(trial_record)
        db.commit()
        db.refresh(trial_record)

        for phase_event in history:
            phase_log = PhaseLog(
                trial_id=trial_record.id,
                phase_number=phase_event.get("phase"),
                event_type=phase_event.get("type"),
                data_payload=phase_event,
            )
            db.add(phase_log)

        db.commit()

        return {
            "status": "success",
            "trial_id": trial_record.id,
            "final_phase": final_phase,
            "active_arms_remaining": active_arms_remaining,
            "history": history,
            "config": {
                "arms": arm_names,
                "arm_effects": arm_effects,
                "patients_per_arm": request.patients_per_arm,
                "max_phases": request.max_phases,
                "stopping_threshold": request.stopping_threshold,
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))