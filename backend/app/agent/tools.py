from langchain_core.tools import tool
from app.engine.cohorts import VirtualTrialEngine
from app.engine.stats import compute_interim_analysis
import numpy as np

# Initialize the deterministic engine
engine = VirtualTrialEngine(random_seed=42)

@tool
def get_interim_analysis(patient_allocations: dict, active_arms: list[str]) -> dict:
    """
    Simulates a trial phase and returns the statistical analysis (p-values, mean differences)
    comparing the active treatment arms against the Control arm.
    """
    # Ground truth effects (hidden from the LLM, but used by the engine)
    true_effects = {"Control": 0.0, "Arm_A": 0.1, "Arm_B": 1.2}
    
    # Filter only the arms still active in the trial
    current_effects = {arm: true_effects[arm] for arm in active_arms if arm in true_effects}
    if "Control" not in current_effects:
         current_effects["Control"] = 0.0
         
    raw_data = engine.run_interim_phase(patient_allocations, current_effects)
    
    results = {}
    control_data = raw_data.get("Control", np.array([]))
    
    for arm in active_arms:
        if arm == "Control":
            continue
        treatment_data = raw_data.get(arm, np.array([]))
        if len(control_data) > 1 and len(treatment_data) > 1:
            stats_result = compute_interim_analysis(control_data, treatment_data)
            results[arm] = stats_result
        else:
            results[arm] = {"error": "Not enough data mapped to calculate."}
        
    return results