"""Statistics used in the paper. Everything is computed after the experiments on saved outputs; no model calls."""
from collections import Counter
from math import sqrt

import numpy as np
from scipy.optimize import brentq
from scipy.stats import beta, binomtest, norm, rankdata

SEED = 20261018  # ranking: permutation p and the bootstrap of 'Opus minus forecast' (table 4)
SEED_METRICS = 20261020  # bootstraps of accuracy by groups, kappa and rank combinations (added 20.10)


def wilson(k: int, n: int) -> tuple[float, float]:
    z = norm.ppf(.975)
    c = (k / n + z * z / (2 * n)) / (1 + z * z / n)
    h = z * (k / n * (1 - k / n) / n + z * z / (4 * n * n)) ** .5 / (1 + z * z / n)
    return float(c - h), float(c + h)


def mcnemar(only_a: int, only_b: int) -> float:
    """Exact two-sided McNemar = binomial test on the discordant pairs."""
    return float(binomtest(only_a, only_a + only_b).pvalue) if only_a + only_b else 1.0


def tango_ci(b10: int, b01: int, n: int, alpha: float = .05) -> tuple[float, float]:
    """Tango (1998) score interval for a paired difference of proportions, no continuity correction."""
    m, d, z2 = (b10 + b01) / n, (b10 - b01) / n, norm.ppf(1 - alpha / 2) ** 2
    if b10 + b01 == 0:
        return -z2 / (n + z2), z2 / (n + z2)

    def q_mle(delta):
        v = m + d * delta
        root = sqrt(max(0., v * v - 4 * (d * delta - (1 - m) * delta * delta)))
        return min(1., max(abs(delta), (v + root) / 2))

    def equation(delta):
        return n * (d - delta) ** 2 - z2 * (q_mle(delta) - delta * delta)

    lo = -1. if d == -1 else brentq(equation, -1., d, xtol=1e-13)
    hi = 1. if d == 1 else brentq(equation, d, 1., xtol=1e-13)
    return lo, hi


def _cp(k: int, n: int, alpha: float) -> tuple[float, float]:
    return (0. if k == 0 else float(beta.ppf(alpha / 2, k, n - k + 1)),
            1. if k == n else float(beta.ppf(1 - alpha / 2, k + 1, n - k)))


def cp_bonferroni(b10: int, b01: int, n: int) -> tuple[float, float]:
    """Conservative check: 97.5% Clopper-Pearson for p10 and p01, opposite bounds subtracted."""
    a, b = _cp(b10, n, .025), _cp(b01, n, .025)
    return max(-1., a[0] - b[1]), min(1., a[1] - b[0])


def kappa(pred: list, truth: list) -> float:
    n = len(truth)
    po = sum(p == t for p, t in zip(pred, truth)) / n
    cp, ct = Counter(pred), Counter(truth)
    pe = sum(cp[lab] * ct[lab] for lab in set(pred) | set(truth)) / n ** 2
    return float("nan") if pe == 1 else (po - pe) / (1 - pe)


def group_accuracy(pred: dict, truth: dict) -> dict:
    """Accuracy by outcome groups = mean of the accuracy on effect tests and on null tests ('always zero' = 0.5);
    standard balanced accuracy = mean recall over the classes present; Cohen's kappa ('?' is its own label)."""
    ids = sorted(truth)
    eff = [t for t in ids if truth[t] != "0"]
    nul = [t for t in ids if truth[t] == "0"]
    ok = lambda ts: sum(pred[t] == truth[t] for t in ts)  # noqa: E731
    by_groups = (ok(eff) / len(eff) + ok(nul) / len(nul)) / 2 if eff and nul else None
    tv = [truth[t] for t in ids]
    standard = sum(sum(pred[t] == c for t in ids if truth[t] == c) / tv.count(c) for c in sorted(set(tv))) / len(set(tv))
    return dict(n=len(ids), correct=ok(ids), effect=(ok(eff), len(eff)), null=(ok(nul), len(nul)), by_groups=by_groups,
                standard=standard, kappa=kappa([pred[t] for t in ids], tv),
                reversed=sum({pred[t], truth[t]} == {"+", "-"} for t in ids))


def group_accuracy_boot(pred: dict, truth: dict, b: int = 20000) -> dict:
    ids = sorted(truth)
    rng = np.random.default_rng(SEED_METRICS)
    ks, bs = [], []
    for _ in range(b):
        smp = [ids[i] for i in rng.integers(0, len(ids), len(ids))]
        pr, tr = [pred[t] for t in smp], [truth[t] for t in smp]
        eff = [i for i, t in enumerate(tr) if t != "0"]
        nul = [i for i, t in enumerate(tr) if t == "0"]
        if eff and nul:
            bs.append((sum(pr[i] == tr[i] for i in eff) / len(eff) + sum(pr[i] == tr[i] for i in nul) / len(nul)) / 2)
        k = kappa(pr, tr)
        if not np.isnan(k):
            ks.append(k)
    return dict(kappa_ci=np.quantile(ks, [.025, .975]).tolist(), by_groups_ci=np.quantile(bs, [.025, .975]).tolist())


def spearman(x, y) -> float:
    return float(np.corrcoef(rankdata(x), rankdata(y))[0, 1])


def norm_ranks(v: np.ndarray) -> np.ndarray:
    r = rankdata(v, axis=-1)
    r = r - r.mean(axis=-1, keepdims=True)
    d = np.sqrt((r * r).sum(axis=-1, keepdims=True))
    return np.divide(r, d, out=np.full_like(r, np.nan), where=d != 0)


def ranking(twin: dict, effect: dict, opus: dict, ids: list) -> dict:
    """Spearman rho of a forecast with the historical effect (only its ranks are needed), one-sided permutation p
    (10 000 permutations, >= convention) and a paired percentile bootstrap (20 000) of 'Opus minus forecast'."""
    x, y, o = (np.array([s[t] for t in ids], float) for s in (twin, effect, opus))
    ry = rankdata(y) - np.mean(rankdata(y))
    rng = np.random.default_rng(SEED)
    perms = np.array([rng.permutation(ry) for _ in range(10000)])
    ps = []
    for v in (x, o):
        rv = rankdata(v) - np.mean(rankdata(v))
        den = np.sqrt(np.dot(ry, ry) * np.dot(rv, rv))
        # the observed statistic by the same formula as the permuted ones, and ties counted: with tied ranks a permutation
        # can give exactly the observed rho, which a comparison against np.corrcoef dropped by rounding (fixed 26.10)
        observed = np.dot(ry, rv) / den
        ps.append(float(np.mean(perms @ rv / den >= observed - 1e-12)))
    ix = np.random.default_rng(SEED).integers(0, len(ids), (20000, len(ids)))
    by = norm_ranks(y[ix])
    tx, ox = (norm_ranks(x[ix]) * by).sum(axis=1), (norm_ranks(o[ix]) * by).sum(axis=1)
    good = np.isfinite(tx) & np.isfinite(ox)
    return dict(n=len(ids), twin_rho=spearman(x, y), opus_rho=spearman(o, y), twin_p=ps[0], opus_p=ps[1],
                opus_minus_twin_ci=np.quantile((ox - tx)[good], [.025, .975]).tolist())


def partial(rxy, rxo, ryo):
    return (rxy - rxo * ryo) / np.sqrt((1 - rxo ** 2) * (1 - ryo ** 2))


def rank_combination(twin: dict, effect: dict, opus: dict, ids: list) -> dict:
    """Partial rho of the forecast given Opus, and the sum of normalized ranks of forecast and Opus against Opus alone."""
    x, y, o = (np.array([s[t] for t in ids], float) for s in (twin, effect, opus))
    rxy, rxo, ryo = spearman(x, y), spearman(x, o), spearman(y, o)
    comb = float(np.corrcoef(norm_ranks(x) + norm_ranks(o), rankdata(y))[0, 1])
    ix = np.random.default_rng(SEED_METRICS).integers(0, len(ids), (20000, len(ids)))
    X, Y, O = norm_ranks(x[ix]), norm_ranks(y[ix]), norm_ranks(o[ix])
    bxy, bxo, byo = (X * Y).sum(1), (X * O).sum(1), (Y * O).sum(1)
    bp = partial(bxy, bxo, byo)
    S = X + O
    S = S - S.mean(1, keepdims=True)
    S = S / np.sqrt((S * S).sum(1, keepdims=True))
    d = (S * Y).sum(1) - byo
    good = np.isfinite(bp) & np.isfinite(d)
    return dict(twin_opus_rho=rxo, partial=float(partial(rxy, rxo, ryo)), partial_ci=np.quantile(bp[good], [.025, .975]).tolist(),
                combined=comb, combined_spearman=spearman(norm_ranks(x) + norm_ranks(o), y),
                combined_minus_opus_ci=np.quantile(d[good], [.025, .975]).tolist())


def paired_sign(diffs, b: int = 2000, seed: int = 0) -> tuple[str, float, float, float]:
    """Sign rule of section 5.1: mean paired difference B - A over scenarios, 95% percentile bootstrap over scenario pairs;
    '+' if the interval is above zero, '-' if below, '0' otherwise. Re-implemented here for the synthetic demo and the tests
    (the simulator itself is not published)."""
    d = np.asarray(diffs, float)
    rng = np.random.default_rng(seed)
    boots = d[rng.integers(0, len(d), (b, len(d)))].mean(axis=1)
    lo, hi = np.quantile(boots, [.025, .975])
    return ("+" if lo > 0 else "-" if hi < 0 else "0"), float(d.mean()), float(lo), float(hi)


def confusion_metrics(pred: list, truth: list) -> dict:
    """Everything the paper reports from a confusion matrix: correct, per-class counts, '0' answers, opposite signs,
    accuracy by outcome groups, standard balanced accuracy and Cohen's kappa."""
    ids = {f"i{k:04d}": k for k in range(len(truth))}
    g = group_accuracy({i: pred[k] for i, k in ids.items()}, {i: truth[k] for i, k in ids.items()})
    out = dict(n=len(truth), correct=g["correct"], effect_correct=g["effect"][0], effect_n=g["effect"][1],
               null_correct=g["null"][0], null_n=g["null"][1], outcome_group_acc=g["by_groups"], balanced_acc=g["standard"],
               kappa=g["kappa"], opposite_sign=g["reversed"], zero_answers=sum(p == "0" for p in pred),
               nonzero_answers=sum(p in "+-" for p in pred), nonzero_correct=sum(p in "+-" and p == t for p, t in zip(pred, truth)),
               false_effect_on_null=sum(p in "+-" and t == "0" for p, t in zip(pred, truth)),
               false_plus_on_null=sum(p == "+" and t == "0" for p, t in zip(pred, truth)),
               missed_effect=sum(p == "0" and t != "0" for p, t in zip(pred, truth)))
    for lab, name in (("+", "plus"), ("0", "zero"), ("-", "minus")):
        out[f"truth_{name}"] = truth.count(lab)
        out[f"correct_{name}"] = sum(p == t == lab for p, t in zip(pred, truth))
    return out


def binom_p(k: int, n: int) -> float:
    return float(binomtest(k, n).pvalue) if n else 1.0


def power_pairs(delta: float, q: float, alpha: float = .05, power: float = .8) -> int:
    """McNemar approximation: number of paired tests to detect an accuracy difference delta at discordance q."""
    za, zb = norm.ppf(1 - alpha / 2), norm.ppf(power)
    return int(np.ceil((za * sqrt(q) + zb * sqrt(q - delta ** 2)) ** 2 / delta ** 2))
