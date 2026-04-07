from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from app.agent.schemas import TrialState, TrialAction
from app.agent.tools import get_interim_analysis
from app.agent.llm_config import local_llm 

# Bind the tool and the expected JSON output format to the local LLM
llm_with_tools = local_llm.bind_tools([get_interim_analysis])
llm_with_structured_output = local_llm.with_structured_output(TrialAction)

import math

def data_collection_node(state: TrialState) -> dict:
    """Node 1: Gathers the statistical data for the current phase with Adaptive Randomization."""
    print(f"--- Running Phase {state['current_phase']} ---")
    
    active_arms = state["active_arms"]
    
    # Adaptive Randomization (Thompson Sampling Concept)
    # Total patients for this phase relies on the baseline
    total_patients = state["patient_count_per_arm"] * len(active_arms)
    patient_allocations = {}
    
    # If phase 1, allocate equally
    if state["current_phase"] == 1:
        for arm in active_arms:
            patient_allocations[arm] = state["patient_count_per_arm"]
    else:
        # Phase 2+, calculate allocation weights from previous phase Bayesian outputs
        last_stats = None
        for step in reversed(state["trial_history"]):
            if step["type"] == "stats":
                last_stats = step["data"]
                break
        
        weights = {}
        # Control always gets a fixed baseline weight to maintain statistical validity
        weights["Control"] = 1.0 
        
        for arm in active_arms:
            if arm == "Control":
                continue
            # Fetch the probability of superiority from Bayesian output
            prob_superior = last_stats.get(arm, {}).get("t_statistic", 0.5) if last_stats else 0.5
            # We use an exponential weight so beneficial arms get exponentially more patients
            weights[arm] = math.exp(prob_superior * 2)
            
        total_weight = sum(weights[arm] for arm in active_arms)
        
        # Distribute patients deterministically via rounding
        distributed = 0
        for i, arm in enumerate(active_arms):
            if i == len(active_arms) - 1:
                patient_allocations[arm] = total_patients - distributed
            else:
                allocated = int(total_patients * (weights[arm] / total_weight))
                patient_allocations[arm] = allocated
                distributed += allocated

    print(f"Adaptive Patient Allocation: {patient_allocations}")

    stats_data = get_interim_analysis.invoke({
        "patient_allocations": patient_allocations,
        "active_arms": active_arms
    })
    
    data_msg = HumanMessage(content=f"Interim Phase {state['current_phase']} Results: {stats_data}. Allocations: {patient_allocations}")
    
    return {
        "messages": [data_msg], 
        "trial_history": [{"type": "stats", "phase": state["current_phase"], "data": stats_data, "allocations": patient_allocations}]
    }

def reasoning_node(state: TrialState) -> dict:
    """Node 2: The LLM analyzes the data and makes a protocol decision."""
    
    # UPDATED PROMPT: The AI is now instructed to read the Python-generated boolean flags
    sys_prompt = SystemMessage(content="""
    You are the Principal Investigator of an adaptive clinical trial.
    Review the latest statistical results provided by the interim analysis tool. 
    - If a treatment arm shows 'is_significant_05': true, it is successful. 
    - If a treatment arm shows 'is_failing_futility': true, drop it for futility.
    Ensure your statistical reasoning cites the specific boolean flags and mean differences provided.
    Do not perform your own numerical comparisons.
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
        
    ai_memory = AIMessage(content=f"Action taken in Phase {state['current_phase']}: {decision.decision} on {decision.target_arm}.")
        
    return {
        "messages": [ai_memory], 
        "active_arms": next_active_arms,
        "current_phase": state["current_phase"] + 1,
        "is_completed": is_completed,
        "trial_history": [{"type": "action", "phase": state["current_phase"], "decision": decision.decision, "target": decision.target_arm, "reasoning": decision.statistical_reasoning}]
    }

def routing_logic(state: TrialState) -> str:
    """Determines if the trial should loop or end."""
    if state["is_completed"] or state["current_phase"] > 3:
        return END
    return "collect_data"

workflow = StateGraph(TrialState)

workflow.add_node("collect_data", data_collection_node)
workflow.add_node("reason", reasoning_node)

workflow.set_entry_point("collect_data")
workflow.add_edge("collect_data", "reason")
workflow.add_conditional_edges("reason", routing_logic)

adaptive_trial_app = workflow.compile()