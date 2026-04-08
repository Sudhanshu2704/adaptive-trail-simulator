from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from app.agent.schemas import TrialState, TrialAction
from app.agent.tools import get_interim_analysis
from app.agent.llm_config import local_llm
import numpy as np

# Bind the tool and the expected JSON output format to the LLM
llm_with_tools = local_llm.bind_tools([get_interim_analysis])
llm_with_structured_output = local_llm.with_structured_output(TrialAction)


def data_collection_node(state: TrialState) -> dict:
    """Node 1: Gathers statistical data for the current phase using real Thompson Sampling."""
    print(f"--- Running Phase {state['current_phase']} / {state['max_phases']} ---")

    active_arms = state["active_arms"]
    arm_effects = state["arm_effects"]
    total_patients = state["patient_count_per_arm"] * len(active_arms)
    patient_allocations = {}

    if state["current_phase"] == 1:
        # Phase 1: equal allocation across all arms
        for arm in active_arms:
            patient_allocations[arm] = state["patient_count_per_arm"]
    else:
        # Phase 2+: Real Thompson Sampling via Beta distribution posteriors
        # Pull responder counts from the last stats entry in history
        last_stats = None
        for step in reversed(state["trial_history"]):
            if step["type"] == "stats":
                last_stats = step["data"]
                break

        weights = {}
        # Control always gets a fixed base allocation to maintain statistical validity
        weights["Control"] = 1.0

        for arm in active_arms:
            if arm == "Control":
                continue
            if last_stats and arm in last_stats:
                responders = last_stats[arm].get("responders", 1)
                n = last_stats[arm].get("n_patients", state["patient_count_per_arm"])
                non_responders = max(1, n - responders)
                # Beta(alpha=responders+1, beta=non_responders+1) — Bayesian conjugate prior
                weights[arm] = float(np.random.beta(responders + 1, non_responders + 1))
            else:
                weights[arm] = 0.5  # Uniform prior for arms with no prior data

        total_weight = sum(weights[arm] for arm in active_arms if arm in weights)
        if total_weight == 0:
            total_weight = len(active_arms)

        distributed = 0
        for i, arm in enumerate(active_arms):
            if i == len(active_arms) - 1:
                patient_allocations[arm] = max(10, total_patients - distributed)
            else:
                allocated = max(10, int(total_patients * (weights.get(arm, 0.5) / total_weight)))
                patient_allocations[arm] = allocated
                distributed += allocated

    print(f"Thompson Sampling Allocation: {patient_allocations}")

    stats_data = get_interim_analysis.invoke({
        "patient_allocations": patient_allocations,
        "active_arms": active_arms,
        "arm_effects": arm_effects,
    })

    data_msg = HumanMessage(
        content=(
            f"Interim Phase {state['current_phase']} Results: {stats_data}. "
            f"Allocations: {patient_allocations}. "
            f"Stopping threshold for success: prob_superior > {state['stopping_threshold']}."
        )
    )

    return {
        "messages": [data_msg],
        "trial_history": [{
            "type": "stats",
            "phase": state["current_phase"],
            "data": stats_data,
            "allocations": patient_allocations,
        }]
    }


def reasoning_node(state: TrialState) -> dict:
    """Node 2: The LLM analyzes the data and makes a protocol decision."""

    sys_prompt = SystemMessage(content=f"""
    You are the Principal Investigator of an adaptive clinical trial.
    Review the latest statistical results from the interim analysis.

    Decision rules (apply strictly in this order):
    1. If any treatment arm has 'is_significant_05': true AND its prob_superior (t_statistic) > {state['stopping_threshold']},
       then declare STOP_TRIAL_SUCCESS for that arm.
    2. If any treatment arm has 'is_failing_futility': true, declare STOP_ARM_FUTILITY for that arm.
    3. Otherwise, declare CONTINUE for target_arm = 'All'.

    Always cite the exact boolean flags and mean_difference values in your statistical_reasoning.
    Do not perform your own numerical comparisons beyond reading the provided flags.
    """)

    messages = [sys_prompt] + state["messages"]
    decision: TrialAction = llm_with_structured_output.invoke(messages)

    print(f"Agent Decision: {decision.decision} for {decision.target_arm}")
    print(f"Reasoning: {decision.statistical_reasoning}")

    next_active_arms = state["active_arms"].copy()
    is_completed = False

    if decision.decision == "STOP_ARM_FUTILITY" and decision.target_arm in next_active_arms:
        next_active_arms.remove(decision.target_arm)
    elif decision.decision == "STOP_TRIAL_SUCCESS":
        is_completed = True

    ai_memory = AIMessage(
        content=f"Action taken in Phase {state['current_phase']}: {decision.decision} on {decision.target_arm}."
    )

    return {
        "messages": [ai_memory],
        "active_arms": next_active_arms,
        "current_phase": state["current_phase"] + 1,
        "is_completed": is_completed,
        "trial_history": [{
            "type": "action",
            "phase": state["current_phase"],
            "decision": decision.decision,
            "target": decision.target_arm,
            "reasoning": decision.statistical_reasoning,
        }]
    }


def routing_logic(state: TrialState) -> str:
    """Real stopping rules: check completion flag OR user-configured max_phases."""
    if state["is_completed"]:
        return END
    # Only one non-Control arm left — cannot compare, end trial
    if len(state["active_arms"]) <= 1:
        return END
    # User-configured maximum phases
    if state["current_phase"] > state["max_phases"]:
        return END
    return "collect_data"


workflow = StateGraph(TrialState)

workflow.add_node("collect_data", data_collection_node)
workflow.add_node("reason", reasoning_node)

workflow.set_entry_point("collect_data")
workflow.add_edge("collect_data", "reason")
workflow.add_conditional_edges("reason", routing_logic)

adaptive_trial_app = workflow.compile()