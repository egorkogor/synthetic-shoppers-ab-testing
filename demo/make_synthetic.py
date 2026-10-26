"""A fully synthetic bank of A/B tests for the demo. SYNTHETIC: generated from the model below, not from any real
experiment, company or customer; the parameters are arbitrary round numbers, not fitted to the closed bank of the paper.

Model, per synthetic test syn01..syn40:
  true standardized effect   theta = 0 with probability P_NULL, otherwise N(0, TAU^2)
  "human" verdict            z = theta + N(0, 1); '+' if z > 1.96, '-' if z < -1.96, '0' otherwise
  simulator                  150 paired scenarios; target action in A with probability pA ~ U(0.1, 0.6), in B with
                             pA + TRANSFER * theta + bias, bias ~ N(0, BIAS_SD) (simulator error unrelated to people);
                             A and B of one scenario share a uniform draw, so the pair differs only where the arms differ
  direct forecast            three answers from a latent score OPTIMISM + FORECAST_SIGNAL * theta + N(0, 1):
                             '+' above +0.8, '-' below -0.8, '0' between; confidence 1-10 from the score's magnitude

    python demo/make_synthetic.py      -> demo/data/synthetic_tests.csv, synthetic_scenarios.csv, synthetic_direct.csv
"""
import csv
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent / "data"
SEED = 7
N_TESTS, N_SCENARIOS = 40, 150
P_NULL, TAU = 0.5, 3.0
TRANSFER, BIAS_SD = 0.01, 0.02
OPTIMISM, FORECAST_SIGNAL = 0.3, 0.4


def generate(seed: int = SEED, n_tests: int = N_TESTS, n_scenarios: int = N_SCENARIOS):
    rng = np.random.default_rng(seed)
    tests, scenarios, direct = [], [], []
    for k in range(n_tests):
        tid = f"syn{k + 1:02d}"
        theta = 0.0 if rng.random() < P_NULL else float(rng.normal(0, TAU))
        z = theta + float(rng.normal())
        truth = "+" if z > 1.96 else "-" if z < -1.96 else "0"
        tests.append(dict(test=tid, theta=round(theta, 4), z=round(z, 4), truth=truth))
        pa = float(rng.uniform(.1, .6))
        pb = float(np.clip(pa + TRANSFER * theta + rng.normal(0, BIAS_SD), .01, .99))
        u = rng.random(n_scenarios)
        for s in range(n_scenarios):
            scenarios.append(dict(test=tid, scenario=s, outcome_a=int(u[s] < pa), outcome_b=int(u[s] < pb)))
        for a in range(3):
            score = OPTIMISM + FORECAST_SIGNAL * theta + float(rng.normal())
            sign = "+" if score > .8 else "-" if score < -.8 else "0"
            direct.append(dict(test=tid, k=a, sign=sign, confidence=int(np.clip(round(abs(score) * 4) + 3, 1, 10))))
    return tests, scenarios, direct


def write(rows, path: Path):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main():
    OUT.mkdir(exist_ok=True)
    tests, scenarios, direct = generate()
    write(tests, OUT / "synthetic_tests.csv")
    write(scenarios, OUT / "synthetic_scenarios.csv")
    write(direct, OUT / "synthetic_direct.csv")
    print(f"synthetic: {len(tests)} tests, {len(scenarios)} scenario pairs, {len(direct)} direct answers -> {OUT}")


if __name__ == "__main__":
    main()
