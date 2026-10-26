"""The replicability model of section 5.5 against Monte Carlo simulation on synthetic z (no data of the paper)."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from abeval import replicability as R  # noqa: E402

RNG = np.random.default_rng(11)
N = 400_000


@pytest.mark.parametrize("z,verdict", [(0.5, "0"), (2.5, "+"), (-3.0, "-"), (1.9, "0")])
def test_flat_same_verdict_matches_simulation(z, verdict):
    theta = z + RNG.normal(size=N)
    rep = theta + RNG.normal(size=N)
    lo, hi = R.BOUNDS[verdict]
    assert R.same_verdict_flat(z, verdict) == pytest.approx(np.mean((rep > lo) & (rep < hi)), abs=0.004)


@pytest.mark.parametrize("z", [0.0, 1.0, -2.5])
def test_flat_two_reruns_matches_simulation(z):
    theta = z + RNG.normal(size=N)
    z1, z2 = theta + RNG.normal(size=N), theta + RNG.normal(size=N)
    assert R.two_reruns_flat(z) == pytest.approx(np.mean(np.sign(z1) == np.sign(z2)), abs=0.004)


def test_spike_fit_recovers_the_slab_variance():
    pi, tau = 0.6, 2.5
    null = RNG.random(20_000) < pi
    z = np.where(null, 0, RNG.normal(0, tau, 20_000)) + RNG.normal(size=20_000)
    assert R.fit_spike(z, pi) == pytest.approx(tau ** 2, rel=0.1)


@pytest.mark.parametrize("z,verdict", [(0.3, "0"), (2.2, "+"), (-2.8, "-")])
def test_spike_predictions_match_simulation(z, verdict):
    pi, tau2 = 0.5, 4.0
    p0, m, v = R._posterior(z, pi, tau2)
    null = RNG.random(N) < p0
    theta = np.where(null, 0.0, m + np.sqrt(v) * RNG.normal(size=N))
    rep, rep2 = theta + RNG.normal(size=N), theta + RNG.normal(size=N)
    lo, hi = R.BOUNDS[verdict]
    assert R.same_verdict_spike(z, verdict, pi, tau2) == pytest.approx(np.mean((rep > lo) & (rep < hi)), abs=0.004)
    assert R.two_reruns_spike(z, pi, tau2) == pytest.approx(np.mean(np.sign(rep) == np.sign(rep2)), abs=0.004)
