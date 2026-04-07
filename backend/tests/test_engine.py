"""
Unit tests for the deterministic VirtualTrialEngine (cohorts.py).
These tests are fast (<0.1s each) — no LLM, no MCMC.
"""
import numpy as np
import pytest
from app.engine.cohorts import VirtualTrialEngine


class TestSimulateCohort:
    """Tests for the core patient cohort simulation."""

    def test_output_length_matches_sample_size(self):
        engine = VirtualTrialEngine(random_seed=42)
        responses = engine.simulate_cohort(sample_size=500, base_mean=10.0, effect_size=0.0)
        assert len(responses) == 500

    def test_mean_is_close_to_expected(self):
        """With 2000 patients and std_dev=1.0. mean should be within 0.1 of (base + effect)."""
        engine = VirtualTrialEngine(random_seed=42)
        expected_mean = 10.0 + 2.5
        responses = engine.simulate_cohort(sample_size=2000, base_mean=10.0, effect_size=2.5, std_dev=1.0)
        assert abs(np.mean(responses) - expected_mean) < 0.15

    def test_zero_effect_size_centers_on_base_mean(self):
        engine = VirtualTrialEngine(random_seed=42)
        responses = engine.simulate_cohort(sample_size=2000, base_mean=10.0, effect_size=0.0, std_dev=1.0)
        assert abs(np.mean(responses) - 10.0) < 0.15

    def test_different_seeds_produce_different_data(self):
        engine_a = VirtualTrialEngine(random_seed=1)
        engine_b = VirtualTrialEngine(random_seed=2)
        a = engine_a.simulate_cohort(100, 10.0, 0.0)
        b = engine_b.simulate_cohort(100, 10.0, 0.0)
        assert not np.array_equal(a, b)

    def test_same_seed_produces_identical_data(self):
        """Determinism: same seed must always yield bitwise identical results."""
        engine_a = VirtualTrialEngine(random_seed=42)
        engine_b = VirtualTrialEngine(random_seed=42)
        a = engine_a.simulate_cohort(100, 10.0, 0.0)
        b = engine_b.simulate_cohort(100, 10.0, 0.0)
        assert np.array_equal(a, b)

    def test_returns_numpy_array(self):
        engine = VirtualTrialEngine(random_seed=42)
        result = engine.simulate_cohort(50, 10.0, 1.0)
        assert isinstance(result, np.ndarray)


class TestRunInterimPhase:
    """Tests for the multi-arm adaptive phase simulation."""

    def test_returns_all_active_arms(self):
        engine = VirtualTrialEngine(random_seed=42)
        allocations   = {"Control": 50, "Arm_A": 50, "Arm_B": 50}
        true_effects  = {"Control": 0.0, "Arm_A": 0.5, "Arm_B": 1.2}
        result = engine.run_interim_phase(allocations, true_effects)
        assert set(result.keys()) == {"Control", "Arm_A", "Arm_B"}

    def test_arm_with_zero_allocation_is_excluded(self):
        """Arms with 0 allocation should not appear in output — mirrors futility dropout."""
        engine = VirtualTrialEngine(random_seed=42)
        allocations  = {"Control": 50, "Arm_A": 0, "Arm_B": 60}
        true_effects = {"Control": 0.0, "Arm_A": 0.5, "Arm_B": 1.2}
        result = engine.run_interim_phase(allocations, true_effects)
        assert "Arm_A" not in result
        assert "Control" in result and "Arm_B" in result

    def test_cohort_sizes_match_allocations(self):
        engine = VirtualTrialEngine(random_seed=42)
        allocations  = {"Control": 30, "Arm_B": 80}
        true_effects = {"Control": 0.0, "Arm_B": 1.2}
        result = engine.run_interim_phase(allocations, true_effects)
        assert len(result["Control"]) == 30
        assert len(result["Arm_B"]) == 80

    def test_higher_effect_arm_has_higher_mean(self):
        """Arm_B (effect=1.2) should have a noticeably higher mean than Control (effect=0)."""
        engine = VirtualTrialEngine(random_seed=42)
        allocations  = {"Control": 1000, "Arm_B": 1000}
        true_effects = {"Control": 0.0, "Arm_B": 1.2}
        result = engine.run_interim_phase(allocations, true_effects)
        assert np.mean(result["Arm_B"]) > np.mean(result["Control"])

    def test_missing_arm_in_effects_is_safely_skipped(self):
        """If an arm exists in effects but not allocations, it should be silently skipped."""
        engine = VirtualTrialEngine(random_seed=42)
        allocations  = {"Control": 50}           # Arm_A not in allocations
        true_effects = {"Control": 0.0, "Arm_A": 0.5}
        result = engine.run_interim_phase(allocations, true_effects)
        assert "Arm_A" not in result
        assert "Control" in result
