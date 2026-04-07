import numpy as np
import pytest

# Fixed-seed data arrays used across all tests — guarantees identical results on every run.
RNG = np.random.default_rng(seed=99)

@pytest.fixture
def clearly_superior_data():
    """Treatment mean ~14.0, Control mean ~10.0. Treatment is obviously better."""
    control   = RNG.normal(loc=10.0, scale=1.0, size=200)
    treatment = RNG.normal(loc=14.0, scale=1.0, size=200)
    return control, treatment

@pytest.fixture
def clearly_inferior_data():
    """Treatment mean ~10.0, Control mean ~10.0. Indistinguishable — futility case."""
    control   = RNG.normal(loc=10.0, scale=1.0, size=200)
    treatment = RNG.normal(loc=10.0, scale=1.0, size=200)
    return control, treatment
