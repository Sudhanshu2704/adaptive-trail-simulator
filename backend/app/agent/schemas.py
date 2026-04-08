from typing import TypedDict, Annotated, List, Dict, Any, Literal, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
import operator


# 1. The Graph State — now fully configurable, no hardcoded values
class TrialState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    current_phase: int
    active_arms: List[str]
    patient_count_per_arm: int
    trial_history: Annotated[List[Dict[str, Any]], operator.add]
    is_completed: bool
    # New configurable fields
    max_phases: int                    # Was hardcoded to 3 — now user-controlled
    stopping_threshold: float          # Bayesian prob_superior threshold to declare success (e.g. 0.95)
    arm_effects: Dict[str, float]      # True effect sizes per arm — was hardcoded in tools.py


# 2. The Structured LLM Output
class TrialAction(BaseModel):
    decision: Literal["CONTINUE", "STOP_ARM_FUTILITY", "STOP_TRIAL_SUCCESS", "INCREASE_SAMPLE_SIZE"] = Field(
        ..., description="The definitive action to take for the next phase."
    )
    target_arm: str = Field(
        ..., description="The specific arm this decision applies to (e.g., 'Arm_A', 'All')."
    )
    statistical_reasoning: str = Field(
        ..., description="Cite the specific p-value or mean difference justifying this action."
    )