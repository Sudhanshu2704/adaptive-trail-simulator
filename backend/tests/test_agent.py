"""
Agent tests for the LangGraph workflow (graph.py).

Strategy: Mock both the LLM and the interim analysis tool so tests are:
  - Fast     (~milliseconds, no Ollama, no MCMC)
  - Isolated (failures pinpoint graph logic, not dependencies)
  - Deterministic (same result every run)

Run with: poetry run pytest tests/test_agent.py -v
"""
import math
import pytest
from unittest.mock import patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage

from app.agent.schemas import TrialState, TrialAction
from app.agent.graph import data_collection_node, reasoning_node, routing_logic


# ---------------------------------------------------------------------------
# Shared fake stats payloads — mirrors what compute_interim_analysis returns
# ---------------------------------------------------------------------------
STATS_ARM_B_WINNING = {
    "Arm_B": {
        "control_mean": 10.0,
        "treatment_mean": 12.5,
        "mean_difference": 2.5,
        "p_value": 0.001,
        "t_statistic": 0.999,
        "is_significant_05": True,
        "is_significant_01": True,
        "is_failing_futility": False,
    }
}

STATS_ARM_A_FUTILE = {
    "Arm_A": {
        "control_mean": 10.0,
        "treatment_mean": 9.8,
        "mean_difference": -0.2,
        "p_value": 0.91,
        "t_statistic": 0.09,
        "is_significant_05": False,
        "is_significant_01": False,
        "is_failing_futility": True,
    }
}

STATS_ALL_CONTINUE = {
    "Arm_A": {
        "control_mean": 10.0,
        "treatment_mean": 10.6,
        "mean_difference": 0.6,
        "p_value": 0.18,
        "t_statistic": 0.82,
        "is_significant_05": False,
        "is_significant_01": False,
        "is_failing_futility": False,
    }
}


def _base_state(**overrides) -> TrialState:
    """Helper: builds a minimal valid TrialState with sensible defaults."""
    state: TrialState = {
        "messages": [],
        "current_phase": 1,
        "active_arms": ["Control", "Arm_A", "Arm_B"],
        "patient_count_per_arm": 50,
        "trial_history": [],
        "is_completed": False,
    }
    state.update(overrides)
    return state


# ===========================================================================
# 1. data_collection_node tests
# ===========================================================================

class TestDataCollectionNode:
    """Tests for the data collection / adaptive allocation node."""

    @patch("app.agent.graph.get_interim_analysis")
    def test_phase1_allocates_equally(self, mock_tool):
        """Phase 1 must give every arm the same patient count."""
        mock_tool.invoke.return_value = STATS_ALL_CONTINUE
        state = _base_state(current_phase=1)

        result = data_collection_node(state)

        # Pull the allocations dict that was passed to the tool
        call_kwargs = mock_tool.invoke.call_args[0][0]
        allocations = call_kwargs["patient_allocations"]

        assert allocations["Control"] == 50
        assert allocations["Arm_A"]   == 50
        assert allocations["Arm_B"]   == 50

    @patch("app.agent.graph.get_interim_analysis")
    def test_phase2_favours_winning_arm(self, mock_tool):
        """Phase 2 must give a higher allocation to the arm with t_statistic closer to 1."""
        mock_tool.invoke.return_value = STATS_ARM_B_WINNING

        # Provide a history entry so the node can look up prior stats
        prior_stats = {"type": "stats", "phase": 1, "data": STATS_ARM_B_WINNING, "allocations": {}}
        state = _base_state(
            current_phase=2,
            active_arms=["Control", "Arm_B"],
            trial_history=[prior_stats],
        )

        data_collection_node(state)

        call_kwargs = mock_tool.invoke.call_args[0][0]
        allocations = call_kwargs["patient_allocations"]

        # Arm_B has t_statistic=0.999, Control weight=1.0 — Arm_B should get far more
        assert allocations["Arm_B"] > allocations["Control"]

    @patch("app.agent.graph.get_interim_analysis")
    def test_result_adds_to_trial_history(self, mock_tool):
        """The returned dict must include a new 'stats' event for trial_history."""
        mock_tool.invoke.return_value = STATS_ALL_CONTINUE
        state = _base_state()

        result = data_collection_node(state)

        assert len(result["trial_history"]) == 1
        assert result["trial_history"][0]["type"] == "stats"
        assert result["trial_history"][0]["phase"] == 1

    @patch("app.agent.graph.get_interim_analysis")
    def test_result_adds_human_message(self, mock_tool):
        """The data node must append exactly one HumanMessage to messages."""
        mock_tool.invoke.return_value = STATS_ALL_CONTINUE
        state = _base_state()

        result = data_collection_node(state)

        assert len(result["messages"]) == 1
        assert isinstance(result["messages"][0], HumanMessage)


# ===========================================================================
# 2. reasoning_node tests
# ===========================================================================

class TestReasoningNode:
    """Tests for the LLM decision-making node — LLM is fully mocked."""

    def _make_mock_llm_decision(self, decision, target_arm, reasoning="mocked reasoning"):
        """Returns a mock LLM that always produces the specified TrialAction."""
        action = TrialAction(
            decision=decision,
            target_arm=target_arm,
            statistical_reasoning=reasoning,
        )
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value.invoke.return_value = action
        return mock_llm

    def _run_reasoning(self, llm_mock, state: TrialState) -> dict:
        with patch("app.agent.graph.llm_with_structured_output", llm_mock.with_structured_output()):
            return reasoning_node(state)

    @patch("app.agent.graph.llm_with_structured_output")
    def test_stop_arm_futility_removes_arm(self, mock_llm):
        """STOP_ARM_FUTILITY must remove the target arm from active_arms."""
        mock_llm.invoke.return_value = TrialAction(
            decision="STOP_ARM_FUTILITY",
            target_arm="Arm_A",
            statistical_reasoning="failing futility",
        )
        state = _base_state(
            messages=[HumanMessage(content="Phase 1 results: ...")],
            active_arms=["Control", "Arm_A", "Arm_B"],
        )

        result = reasoning_node(state)

        assert "Arm_A" not in result["active_arms"]
        assert "Control" in result["active_arms"]
        assert "Arm_B"   in result["active_arms"]

    @patch("app.agent.graph.llm_with_structured_output")
    def test_stop_trial_success_sets_completed(self, mock_llm):
        """STOP_TRIAL_SUCCESS must flip is_completed to True."""
        mock_llm.invoke.return_value = TrialAction(
            decision="STOP_TRIAL_SUCCESS",
            target_arm="Arm_B",
            statistical_reasoning="arm is significant",
        )
        state = _base_state(messages=[HumanMessage(content="Phase 2 results: ...")])

        result = reasoning_node(state)

        assert result["is_completed"] is True

    @patch("app.agent.graph.llm_with_structured_output")
    def test_continue_keeps_all_arms(self, mock_llm):
        """CONTINUE must leave active_arms unchanged."""
        mock_llm.invoke.return_value = TrialAction(
            decision="CONTINUE",
            target_arm="All",
            statistical_reasoning="not yet significant",
        )
        state = _base_state(
            messages=[HumanMessage(content="Phase 1 results: ...")],
            active_arms=["Control", "Arm_A", "Arm_B"],
        )

        result = reasoning_node(state)

        assert set(result["active_arms"]) == {"Control", "Arm_A", "Arm_B"}
        assert result["is_completed"] is False

    @patch("app.agent.graph.llm_with_structured_output")
    def test_phase_increments_by_one(self, mock_llm):
        """The phase counter must always advance by exactly 1 per reasoning call."""
        mock_llm.invoke.return_value = TrialAction(
            decision="CONTINUE", target_arm="All", statistical_reasoning="ok"
        )
        state = _base_state(
            messages=[HumanMessage(content="...")],
            current_phase=2,
        )

        result = reasoning_node(state)

        assert result["current_phase"] == 3

    @patch("app.agent.graph.llm_with_structured_output")
    def test_reasoning_appended_to_history(self, mock_llm):
        """An 'action' event must be written to trial_history on each call."""
        mock_llm.invoke.return_value = TrialAction(
            decision="STOP_ARM_FUTILITY", target_arm="Arm_A", statistical_reasoning="futile"
        )
        state = _base_state(messages=[HumanMessage(content="...")])

        result = reasoning_node(state)

        assert len(result["trial_history"]) == 1
        event = result["trial_history"][0]
        assert event["type"]     == "action"
        assert event["decision"] == "STOP_ARM_FUTILITY"
        assert event["target"]   == "Arm_A"


# ===========================================================================
# 3. routing_logic tests
# ===========================================================================

class TestRoutingLogic:
    """Tests for the conditional edge that decides whether the trial loops or ends."""

    def test_routes_to_collect_data_when_active(self):
        state = _base_state(current_phase=2, is_completed=False)
        assert routing_logic(state) == "collect_data"

    def test_ends_when_is_completed_true(self):
        from langgraph.graph import END
        state = _base_state(current_phase=2, is_completed=True)
        assert routing_logic(state) == END

    def test_ends_when_phase_exceeds_max(self):
        from langgraph.graph import END
        # Phase 4 > 3, should terminate even if is_completed is False
        state = _base_state(current_phase=4, is_completed=False)
        assert routing_logic(state) == END

    def test_phase_3_still_continues(self):
        """Phase 3 is the last allowed phase — it should still loop (not > 3)."""
        state = _base_state(current_phase=3, is_completed=False)
        assert routing_logic(state) == "collect_data"
