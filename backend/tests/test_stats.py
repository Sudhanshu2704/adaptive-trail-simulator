"""
Unit tests for the Bayesian statistical analysis module (stats.py).
These are SLOW (~3-5s each) due to MCMC sampling.
Run alongside fast tests with:  poetry run pytest
Run only fast tests with:        poetry run pytest -m "not slow"
"""
import numpy as np
import pytest
from app.engine.stats import compute_interim_analysis

# All test data is deterministically generated with a fixed seed
_RNG = np.random.default_rng(seed=7)
CONTROL_CLEARLY_INFERIOR  = _RNG.normal(loc=10.0, scale=1.0, size=150)  # baseline
TREATMENT_CLEARLY_SUPERIOR = _RNG.normal(loc=13.5, scale=1.0, size=150) # +3.5 effect
TREATMENT_SAME_AS_CONTROL  = _RNG.normal(loc=10.0, scale=1.0, size=150) # no effect


class TestOutputSchema:
    """Verify the returned dict always has the exact keys the LangGraph agent expects."""

    @pytest.mark.slow
    def test_all_required_keys_present(self):
        result = compute_interim_analysis(CONTROL_CLEARLY_INFERIOR, TREATMENT_CLEARLY_SUPERIOR)
        expected_keys = {
            "control_mean", "treatment_mean", "mean_difference",
            "p_value", "t_statistic",
            "is_significant_05", "is_significant_01",
            "is_failing_futility"
        }
        assert expected_keys == set(result.keys())

    @pytest.mark.slow
    def test_output_types_are_correct(self):
        result = compute_interim_analysis(CONTROL_CLEARLY_INFERIOR, TREATMENT_CLEARLY_SUPERIOR)
        assert isinstance(result["control_mean"],       float)
        assert isinstance(result["treatment_mean"],     float)
        assert isinstance(result["mean_difference"],    float)
        assert isinstance(result["p_value"],            float)
        assert isinstance(result["t_statistic"],        float)
        assert isinstance(result["is_significant_05"],  bool)
        assert isinstance(result["is_significant_01"],  bool)
        assert isinstance(result["is_failing_futility"],bool)


class TestComputedValues:
    """Verify the computed metrics are mathematically correct."""

    @pytest.mark.slow
    def test_means_are_calculated_from_input_data(self):
        result = compute_interim_analysis(CONTROL_CLEARLY_INFERIOR, TREATMENT_CLEARLY_SUPERIOR)
        # These are computed directly from raw data (not MCMC), so they are deterministic
        assert result["control_mean"]   == round(float(np.mean(CONTROL_CLEARLY_INFERIOR)), 3)
        assert result["treatment_mean"] == round(float(np.mean(TREATMENT_CLEARLY_SUPERIOR)), 3)

    @pytest.mark.slow
    def test_mean_difference_equals_treatment_minus_control(self):
        result = compute_interim_analysis(CONTROL_CLEARLY_INFERIOR, TREATMENT_CLEARLY_SUPERIOR)
        expected_diff = round(float(np.mean(TREATMENT_CLEARLY_SUPERIOR) - np.mean(CONTROL_CLEARLY_INFERIOR)), 3)
        assert result["mean_difference"] == expected_diff

    @pytest.mark.slow
    def test_p_value_is_between_0_and_1(self):
        result = compute_interim_analysis(CONTROL_CLEARLY_INFERIOR, TREATMENT_CLEARLY_SUPERIOR)
        assert 0.0 <= result["p_value"] <= 1.0

    @pytest.mark.slow
    def test_t_statistic_is_probability_between_0_and_1(self):
        """t_statistic has been repurposed to hold P(treatment > control)."""
        result = compute_interim_analysis(CONTROL_CLEARLY_INFERIOR, TREATMENT_CLEARLY_SUPERIOR)
        assert 0.0 <= result["t_statistic"] <= 1.0


class TestBayesianDecisions:
    """Verify the boolean decision flags are correct for clear-cut scenarios."""

    @pytest.mark.slow
    def test_clearly_superior_treatment_is_significant(self):
        """With a +3.5 effect on 150 patients, the Bayesian model must flag significance."""
        result = compute_interim_analysis(CONTROL_CLEARLY_INFERIOR, TREATMENT_CLEARLY_SUPERIOR)
        assert result["is_significant_05"] is True

    @pytest.mark.slow
    def test_clearly_superior_treatment_is_not_failing_futility(self):
        result = compute_interim_analysis(CONTROL_CLEARLY_INFERIOR, TREATMENT_CLEARLY_SUPERIOR)
        assert result["is_failing_futility"] is False

    @pytest.mark.slow
    def test_no_effect_treatment_is_not_significant(self):
        """With no real difference, the model should NOT flag statistical significance."""
        result = compute_interim_analysis(CONTROL_CLEARLY_INFERIOR, TREATMENT_SAME_AS_CONTROL)
        assert result["is_significant_05"] is False

    @pytest.mark.slow
    def test_no_effect_treatment_fails_futility(self):
        """With no real benefit, the trial should be flagged as failing futility."""
        result = compute_interim_analysis(CONTROL_CLEARLY_INFERIOR, TREATMENT_SAME_AS_CONTROL)
        assert result["is_failing_futility"] is True
