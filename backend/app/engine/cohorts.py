import numpy as np
from typing import Dict

class VirtualTrialEngine:
    """
    Simulates patient cohorts and multi-arm clinical trial outcomes.
    """
    def __init__(self, random_seed: int = 42):
        # Modern NumPy random number generation
        self.rng = np.random.default_rng(random_seed)

    def simulate_cohort(self, sample_size: int, base_mean: float, effect_size: float, std_dev: float = 1.5) -> np.ndarray:
        """
        Simulates a patient cohort's continuous response.
        Ground truth: response ~ N(base_mean + effect_size, std_dev)
        """
        true_mean = base_mean + effect_size
        responses = self.rng.normal(loc=true_mean, scale=std_dev, size=sample_size)
        return responses

    def run_interim_phase(self, patient_allocations: Dict[str, int], true_effects: Dict[str, float]) -> Dict[str, np.ndarray]:
        """
        Simulates a phase of the trial for multiple arms using an adaptive allocation distribution.
        Example true_effects: {"Control": 0.0, "Arm_A_LowDose": 0.5, "Arm_B_HighDose": 1.2}
        """
        results = {}
        for arm_name, effect in true_effects.items():
            sample_size = patient_allocations.get(arm_name, 0)
            if sample_size > 0:
                results[arm_name] = self.simulate_cohort(
                    sample_size=sample_size, 
                    base_mean=10.0, 
                    effect_size=effect
                )
        return results