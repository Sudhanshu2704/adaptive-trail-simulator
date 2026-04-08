import numpy as np
from typing import Dict


class VirtualTrialEngine:
    """
    Simulates patient cohorts and multi-arm clinical trial outcomes.
    """
    def __init__(self, random_seed: int = None):
        # Use a random seed each trial run for realistic variance;
        # pass a fixed seed only in tests for determinism.
        self.rng = np.random.default_rng(random_seed)

    def simulate_cohort(self, sample_size: int, base_mean: float, effect_size: float, std_dev: float = 1.5) -> np.ndarray:
        """
        Simulates a patient cohort's continuous response.
        Ground truth: response ~ N(base_mean + effect_size, std_dev)
        """
        true_mean = base_mean + effect_size
        responses = self.rng.normal(loc=true_mean, scale=std_dev, size=sample_size)
        return responses

    def run_interim_phase(
        self,
        patient_allocations: Dict[str, int],
        true_effects: Dict[str, float]
    ) -> Dict[str, dict]:
        """
        Simulates a phase of the trial for multiple arms using an adaptive allocation.
        Returns both the raw data array AND discrete response counts for Thompson Sampling.

        Returns per arm:
          - data: np.ndarray of continuous responses
          - responders: int count of patients above response threshold (mean of arm)
          - n: int total patients in this arm
        """
        results = {}
        for arm_name, effect in true_effects.items():
            sample_size = patient_allocations.get(arm_name, 0)
            if sample_size > 0:
                arm_data = self.simulate_cohort(
                    sample_size=sample_size,
                    base_mean=10.0,
                    effect_size=effect,
                )
                # Discretize for Thompson Sampling: count patients above cohort mean as "responders"
                response_threshold = 10.0  # baseline mean (effect_size=0 arm)
                responders = int(np.sum(arm_data > response_threshold))
                results[arm_name] = {
                    "data": arm_data,
                    "responders": responders,
                    "n": sample_size,
                }
        return results