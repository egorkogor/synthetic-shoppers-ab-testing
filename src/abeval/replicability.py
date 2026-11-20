"""Model-based estimate of verdict replicability (section 5.5, appendix H.5): how likely a replication of a test gives the
same three-way verdict, and how likely two future replications agree in sign, given the test's z-statistic.

The paper applies these functions to the z-statistics recovered from the closed reports (40 tests); the z-values and the
recovery from p-values, intervals or group proportions are closed. Here the procedures are published and tested on
synthetic z (tests/test_replicability.py). Assumptions: z is observed with unit variance and a replication has the same
power.
"""
import numpy as np
from scipy.optimize import minimize_scalar
from scipy.stats import multivariate_normal, norm

ZC = float(norm.ppf(.975))
BOUNDS = {"+": (ZC, np.inf), "-": (-np.inf, -ZC), "0": (-ZC, ZC)}


def same_verdict_flat(z: float, verdict: str) -> float:
    """Flat prior: the true effect given z is N(z, 1), so a replication's z' ~ N(z, 2)."""
    lo, hi = BOUNDS[verdict]
    return float(norm.cdf((hi - z) / np.sqrt(2)) - norm.cdf((lo - z) / np.sqrt(2)))


def two_reruns_flat(z: float) -> float:
    """Flat prior: two future replications (z1, z2) ~ N((z, z), [[2, 1], [1, 2]]); agreement = P(both > 0) + P(both < 0)."""
    cov = [[2., 1.], [1., 2.]]
    return float(multivariate_normal([-z, -z], cov).cdf([0, 0]) + multivariate_normal([z, z], cov).cdf([0, 0]))


def fit_spike(z_values, pi: float) -> float:
    """Spike and slab: the true effect is 0 with probability pi, otherwise N(0, tau^2); tau^2 by maximum likelihood."""
    zz = np.asarray(z_values, float)

    def nll(lt):
        return -np.sum(np.log(pi * norm.pdf(zz) + (1 - pi) * norm.pdf(zz, scale=np.sqrt(1 + np.exp(lt)))))

    with np.errstate(divide="ignore", invalid="ignore"):  # the likelihood underflows at the far end of the bounds
        return float(np.exp(minimize_scalar(nll, bounds=(-5, 8), method="bounded").x))


def _posterior(z: float, pi: float, tau2: float):
    w0, w1 = pi * norm.pdf(z), (1 - pi) * norm.pdf(z, scale=np.sqrt(1 + tau2))
    return w0 / (w0 + w1), z * tau2 / (1 + tau2), tau2 / (1 + tau2)


def same_verdict_spike(z: float, verdict: str, pi: float, tau2: float) -> float:
    p0, m, v = _posterior(z, pi, tau2)
    lo, hi = BOUNDS[verdict]

    def pr(mean, var):
        return norm.cdf((hi - mean) / np.sqrt(var)) - norm.cdf((lo - mean) / np.sqrt(var))

    return float(p0 * pr(0, 1) + (1 - p0) * pr(m, v + 1))


def two_reruns_spike(z: float, pi: float, tau2: float) -> float:
    """theta | non-null ~ N(m, v); replications z_i = theta + e_i, so (z1, z2) ~ N((m, m), [[1 + v, v], [v, 1 + v]])."""
    p0, m, v = _posterior(z, pi, tau2)
    cv = [[1 + v, v], [v, 1 + v]]
    agree = multivariate_normal([-m, -m], cv).cdf([0, 0]) + multivariate_normal([m, m], cv).cdf([0, 0])
    return float(p0 * .5 + (1 - p0) * agree)
