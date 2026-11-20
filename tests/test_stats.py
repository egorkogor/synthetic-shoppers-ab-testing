"""The statistical procedures of the paper on synthetic inputs with known answers (no data of the paper are used)."""
import sys
from math import comb
from pathlib import Path

import numpy as np
import pytest
from scipy.stats import norm, spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from abeval import stats as S  # noqa: E402


def test_wilson_closed_form():
    lo, hi = S.wilson(0, 10)
    assert lo == pytest.approx(0, abs=1e-12) and hi == pytest.approx(0.2775, abs=1e-4)
    lo, hi = S.wilson(5, 10)
    assert (lo, hi) == pytest.approx((0.2366, 0.7634), abs=1e-4)
    assert S.wilson(17, 27)[0] < 17 / 27 < S.wilson(17, 27)[1]


@pytest.mark.parametrize("a,b", [(0, 0), (6, 2), (4, 9), (0, 6), (11, 9)])
def test_mcnemar_is_exact_binomial(a, b):
    n = a + b
    if n == 0:
        assert S.mcnemar(a, b) == 1.0
        return
    k = min(a, b)
    tail = sum(comb(n, i) for i in range(k + 1)) / 2 ** n
    assert S.mcnemar(a, b) == pytest.approx(min(1.0, 2 * tail), abs=1e-12)


def _tango_by_grid(b10, b01, n, z=norm.ppf(.975)):
    """Independent inversion of Tango's score statistic on a fine grid (slow, test only)."""
    d = (b10 - b01) / n
    m = (b10 + b01) / n
    keep = []
    for delta in np.linspace(-0.999, 0.999, 199_801):
        v = m + d * delta
        q = (v + np.sqrt(max(0.0, v * v - 4 * (d * delta - (1 - m) * delta * delta)))) / 2
        q = min(1.0, max(abs(delta), q))
        stat = n * (d - delta) ** 2 / max(q - delta * delta, 1e-15)
        if stat <= z * z:
            keep.append(delta)
    return min(keep), max(keep)


@pytest.mark.parametrize("b10,b01,n", [(8, 4, 27), (5, 5, 27), (0, 6, 15), (6, 2, 27)])
def test_tango_matches_grid_inversion(b10, b01, n):
    lo, hi = S.tango_ci(b10, b01, n)
    glo, ghi = _tango_by_grid(b10, b01, n)
    assert lo == pytest.approx(glo, abs=2e-4) and hi == pytest.approx(ghi, abs=2e-4)
    assert lo <= (b10 - b01) / n <= hi


def test_cp_bonferroni_is_wider_than_tango():
    for b10, b01, n in [(8, 4, 27), (5, 5, 27), (2, 6, 15)]:
        t, c = S.tango_ci(b10, b01, n), S.cp_bonferroni(b10, b01, n)
        assert c[0] <= t[0] and c[1] >= t[1]


def test_kappa_textbook_example():
    # 2x2 table [[20, 5], [10, 15]]: po = 0.7, pe = 0.5, kappa = 0.4
    pred = ["a"] * 20 + ["b"] * 5 + ["a"] * 10 + ["b"] * 15
    truth = ["a"] * 25 + ["b"] * 25
    assert S.kappa(pred, truth) == pytest.approx(0.4)
    assert S.kappa(truth, truth) == pytest.approx(1.0)


def test_always_zero_baselines():
    truth = ["+"] * 5 + ["0"] * 7 + ["-"] * 3
    m = S.confusion_metrics(["0"] * len(truth), truth)
    assert m["outcome_group_acc"] == pytest.approx(0.5)
    assert m["balanced_acc"] == pytest.approx(1 / 3)
    assert m["kappa"] == pytest.approx(0.0)
    assert m["correct"] == 7 and m["zero_answers"] == 15 and m["opposite_sign"] == 0


def test_confusion_metrics_counts():
    truth = ["+", "+", "0", "0", "-", "-"]
    pred = ["+", "-", "0", "+", "-", "0"]
    m = S.confusion_metrics(pred, truth)
    assert (m["correct"], m["opposite_sign"], m["false_plus_on_null"], m["missed_effect"]) == (3, 1, 1, 1)
    assert (m["effect_correct"], m["effect_n"], m["null_correct"], m["null_n"]) == (2, 4, 1, 2)


def test_spearman_matches_scipy():
    rng = np.random.default_rng(1)
    x, y = rng.normal(size=30), rng.normal(size=30)
    assert S.spearman(x, y) == pytest.approx(spearmanr(x, y).statistic)


def test_ranking_permutation_p():
    ids = [f"s{i}" for i in range(12)]
    eff = {t: i for i, t in enumerate(ids)}
    up = {t: 2.0 * i for i, t in enumerate(ids)}
    down = {t: -1.0 * i for i, t in enumerate(ids)}
    r = S.ranking(up, eff, down, ids)
    assert r["twin_rho"] == pytest.approx(1.0) and r["opus_rho"] == pytest.approx(-1.0)
    assert r["twin_p"] < 0.001 and r["opus_p"] > 0.999
    lo, hi = r["opus_minus_twin_ci"]
    assert lo <= hi <= 0


def test_permutation_p_counts_ties_like_full_enumeration():
    """With tied ranks a permutation can reproduce the observed rho exactly; such permutations count (>= convention)."""
    from itertools import permutations
    x, y = [0, 0, 1, 1, 2, 2], [1, 3, 2, 5, 4, 6]
    ids = list("abcdef")
    r = S.ranking(dict(zip(ids, x)), dict(zip(ids, y)), dict(zip(ids, x)), ids)
    rx, ry = np.array(x, float), np.array(y, float)
    obs = S.spearman(rx, ry)
    exact = np.mean([S.spearman(rx, ry[list(p)]) >= obs - 1e-12 for p in permutations(range(6))])
    assert exact == pytest.approx(64 / 720)
    assert r["twin_p"] == pytest.approx(exact, abs=0.01)


def test_paired_sign_rule():
    assert S.paired_sign([1] * 40 + [0] * 110)[0] == "+"
    assert S.paired_sign([-1] * 40 + [0] * 110)[0] == "-"
    assert S.paired_sign([1, -1] * 75)[0] == "0"
    sign, mean, lo, hi = S.paired_sign([1, 0, 0, -1] * 30, seed=3)
    assert sign == "0" and lo <= mean <= hi


def test_power_numbers_of_section_5_3():
    assert [S.power_pairs(.10, q) for q in (.2, .3, .5)] == [155, 234, 391]


def test_group_accuracy_bootstrap_is_seeded():
    truth = {f"s{i}": "+0-"[i % 3] for i in range(30)}
    pred = {t: ("0" if i % 2 else truth[t]) for i, t in enumerate(sorted(truth))}
    a, b = S.group_accuracy_boot(pred, truth, b=500), S.group_accuracy_boot(pred, truth, b=500)
    assert a == b
    assert a["kappa_ci"][0] <= S.group_accuracy(pred, truth)["kappa"] <= a["kappa_ci"][1]
