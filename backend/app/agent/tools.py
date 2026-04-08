from langchain_core.tools import tool
from app.engine.cohorts import VirtualTrialEngine
from app.engine.stats import compute_interim_analysis
import numpy as np

# Engine uses random seed per call for realistic trial variance
engine = VirtualTrialEngine()


@tool
def get_interim_analysis(
    patient_allocations: dict,
    active_arms: list[str],
    arm_effects: dict,
) -> dict:
    """
    Simulates a trial phase and returns the Bayesian statistical analysis
    (prob_superior, mean differences, futility flags) comparing each active
    treatment arm against the Control arm.

    Args:
        patient_allocations: {arm_name: n_patients} for this phase
        active_arms: list of currently active arm names
        arm_effects: {arm_name: effect_size} — ground truth effect sizes (hidden from LLM)
    """
    # Filter to only active arms; guarantee Control is always present
    current_effects = {arm: arm_effects.get(arm, 0.0) for arm in active_arms}
    if "Control" not in current_effects:
        current_effects["Control"] = 0.0

    raw_data = engine.run_interim_phase(patient_allocations, current_effects)

    results = {}
    control_info = raw_data.get("Control", {})
    control_data = control_info.get("data", np.array([]))

    for arm in active_arms:
        if arm == "Control":
            continue
        arm_info = raw_data.get(arm, {})
        treatment_data = arm_info.get("data", np.array([]))
        if len(control_data) > 1 and len(treatment_data) > 1:
            stats_result = compute_interim_analysis(control_data, treatment_data)
            # Attach response counts for real Thompson Sampling in graph.py
            stats_result["responders"] = arm_info.get("responders", 0)
            stats_result["n_patients"] = arm_info.get("n", 0)
            results[arm] = stats_result
        else:
            results[arm] = {"error": "Not enough data to calculate."}

    return results