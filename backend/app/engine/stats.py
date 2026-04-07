from typing import Dict, Any
import numpy as np
import numpyro
import numpyro.distributions as dist
from numpyro.infer import MCMC, NUTS
import jax.random as random

def compute_interim_analysis(control_data: np.ndarray, treatment_data: np.ndarray) -> Dict[str, Any]:
    """
    Performs a Bayesian estimation superseding the t-test (BEST) using NumPyro.
    Outputs metrics similar to the traditional test to maintain agent compatibility,
    but replaces frequentist p-values with Bayesian posterior probabilities.
    """
    control_mean = np.mean(control_data)
    treatment_mean = np.mean(treatment_data)
    mean_difference = treatment_mean - control_mean
    
    # Simple Bayesian model for the difference of two means
    def model(control, treatment):
        # Priors for means
        mu_c = numpyro.sample("mu_c", dist.Normal(0, 10))
        mu_t = numpyro.sample("mu_t", dist.Normal(0, 10))
        
        # Priors for std deviations
        sigma_c = numpyro.sample("sigma_c", dist.HalfNormal(10))
        sigma_t = numpyro.sample("sigma_t", dist.HalfNormal(10))
        
        # Likelihoods
        numpyro.sample("obs_c", dist.Normal(mu_c, sigma_c), obs=control)
        numpyro.sample("obs_t", dist.Normal(mu_t, sigma_t), obs=treatment)
        
        # Deterministic difference
        numpyro.deterministic("diff_means", mu_t - mu_c)
    
    # Run MCMC — tuned for speed in real-time simulation (200 warmup + 500 samples)
    # Accuracy is preserved because the effect sizes in clinical trials are large enough
    # that 500 posterior samples give stable probability estimates.
    rng_key = random.PRNGKey(42)
    kernel = NUTS(model)
    mcmc = MCMC(kernel, num_warmup=200, num_samples=500, progress_bar=False)
    mcmc.run(rng_key, control=control_data, treatment=treatment_data)
    
    # Get posterior samples
    samples = mcmc.get_samples()
    diff_means_samples = samples["diff_means"]
    
    # Bayesian equivalent metrics
    # Probability that treatment is better than control (difference > 0)
    prob_superior = np.mean(diff_means_samples > 0)
    
    # The pseudo p-value in a typical setting is the probability of the null (<=0) assuming effect is positive
    pseudo_p_value = 1.0 - float(prob_superior)
    
    is_significant_05 = bool(prob_superior > 0.95)
    is_significant_01 = bool(prob_superior > 0.99)
    
    return {
        "control_mean": round(float(control_mean), 3),
        "treatment_mean": round(float(treatment_mean), 3),
        "mean_difference": round(float(mean_difference), 3),
        "p_value": round(float(pseudo_p_value), 5), # pseudo p-value to keep the LLM schema intact
        "t_statistic": round(float(prob_superior), 3), # repurposed to show probability of superiority
        "is_significant_05": is_significant_05,
        "is_significant_01": is_significant_01,
        # Expected value of difference threshold for futility
        "is_failing_futility": bool(np.mean(diff_means_samples) <= 0.1) 
    }