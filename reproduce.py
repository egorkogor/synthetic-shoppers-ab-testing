"""Recompute the paper's numbers that follow from the published aggregates and compare them with the printed values.

    python reproduce.py   -> results/values.json, results/report.md; exit code 1 on any mismatch

Inputs (data/README.md): confusion matrices and paired correctness by evaluation set, the calibration counts and the
60 calibration scenarios (agent sessions only), the synthetic photo probes. The per-test data of the closed bank are not
in this repository, so values that need them (rank correlations, the replicability model, bootstrap intervals over tests
in their original order) are listed as reported, not recomputed; nothing is reconstructed from the aggregates.
"""
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from abeval import data as D  # noqa: E402
from abeval import stats as S  # noqa: E402

ROOT = Path(__file__).resolve().parent
APPROX_TOL = 0.02  # bootstrap bounds from a confusion matrix in canonical order, against the paper's run order
DERIVED = ("wilson_", "mcnemar_p", "delta_pp", "tango_", "cpb_", "outcome_group_acc", "balanced_acc", "kappa", "before_pct",
           "after_pct", "paired_diff", "ratio", "tests_needed")  # computed by a formula; the other exact values are counts
PRECISION = {"mcnemar_p": 3, "outcome_group_acc": 2, "balanced_acc": 2, "kappa": 2, "kappa_ci_low": 2, "kappa_ci_high": 2,
             "outcome_group_ci_low": 2, "outcome_group_ci_high": 2, "ratio_to_humans": 2, "ratio_ci_low": 2,
             "ratio_ci_high": 2}


def rounded(stat: str, x):
    if isinstance(x, str):
        return x
    if stat in PRECISION:
        return float(f"{float(x):.{PRECISION[stat]}f}")  # printed once, half to even (0.625 -> 0.62)
    if stat.endswith(("_pct", "_pp")):
        return round(float(x), 1)
    return int(x) if float(x).is_integer() else float(x)


class Values:
    """Lazily computed values keyed like data/aggregate_results.csv: (set, method, statistic)."""

    def __init__(self):
        self.cms, self.sizes = D.confusion()
        self.pairs = D.paired()
        self.cache = {}
        self.extra = self._calibration() | self._probes() | self._power()

    def metrics(self, set_, method):
        key = (set_, method)
        if key not in self.cache:
            pred, truth = D.expand(self.cms[key])
            m = S.confusion_metrics(pred, truth)
            lo, hi = S.wilson(m["correct"], m["n"])
            m.update(wilson_low_pct=100 * lo, wilson_high_pct=100 * hi)
            self.cache[key] = m
        return self.cache[key]

    def any_method(self, set_):
        return next(m for (s, m) in self.cms if s == set_)

    def get(self, set_, method, stat):
        if (set_, method, stat) in self.extra:
            return self.extra[(set_, method, stat)]
        if set_ == "blind.mechanical_zero6":  # the six mechanical «0»: the broad set minus the rest
            a, b = self.metrics("blind.broad25", "twin"), self.metrics("blind.without_mechanical_zero19", "twin")
            return a[stat] - b[stat]
        if (stat == "n" and method == "") or method == "history":
            m = self.metrics(set_, self.any_method(set_))
            return m["n"] if stat == "n" else m[stat]
        if "_vs_" in method:
            a, b = method.split("_vs_")
            c = self.pairs[(set_, a, b)]
            if stat in ("only_a", "only_b", "both", "neither"):
                return c[stat]
            if stat == "mcnemar_p":
                return S.mcnemar(c["only_a"], c["only_b"])
            if stat == "delta_pp":
                return 100 * (c["only_a"] - c["only_b"]) / c["n"]
            lo, hi = (S.tango_ci if stat.startswith("tango") else S.cp_bonferroni)(c["only_a"], c["only_b"], c["n"])
            return 100 * (lo if stat.endswith("low_pp") else hi)
        if stat.startswith(("kappa_ci", "outcome_group_ci")):
            return self._boot(set_, method)[stat]
        return self.metrics(set_, method)[stat]

    def _boot(self, set_, method):
        key = ("boot", set_, method)
        if key not in self.cache:
            pred, truth = D.expand(self.cms[(set_, method)])
            ids = [f"i{k:04d}" for k in range(len(truth))]
            b = S.group_accuracy_boot(dict(zip(ids, pred)), dict(zip(ids, truth)))
            self.cache[key] = dict(kappa_ci_low=b["kappa_ci"][0], kappa_ci_high=b["kappa_ci"][1],
                                   outcome_group_ci_low=b["by_groups_ci"][0], outcome_group_ci_high=b["by_groups_ci"][1])
        return self.cache[key]

    @staticmethod
    def _calibration():
        """Table 6 and section 7.1: agent counts; H1 with the pairing of the 60 scenarios kept (agent sessions only)."""
        out = {}
        cal = D.rows("calibration.csv")
        for r in cal:
            sid = "calibration.H1" if r["measure"].startswith("H1") else f"calibration.{r['measure']}"
            out[(sid, "agents", "before_pct")] = 100 * int(r["agents_before_k"]) / int(r["agents_before_n"])
            out[(sid, "agents", "after_pct")] = 100 * int(r["agents_after_k"]) / int(r["agents_after_n"])
        h1 = cal[0]
        k0, n0, k1, n1 = (int(h1[c]) for c in ("agents_before_k", "agents_before_n", "agents_after_k", "agents_after_n"))
        human = float(h1["humans_share_pct"]) / 100
        sc = {}
        for r in D.rows("calibration_h1_scenarios.csv"):
            sc.setdefault(r["version"], {})[r["scenario"]] = (int(r["added"]), int(r["compared"]))
        ks = sorted(set(sc["base"]) & set(sc["full"]), key=int)
        assert sum(sc["base"][k][1] for k in ks) == k0 and sum(sc["full"][k][0] for k in ks) == n1
        rng = np.random.default_rng(S.SEED_METRICS)
        dd, hf = [], []
        for _ in range(20000):
            smp = [ks[i] for i in rng.integers(0, len(ks), len(ks))]
            nb, cb = sum(sc["base"][k][0] for k in smp), sum(sc["base"][k][1] for k in smp)
            nf, cf = sum(sc["full"][k][0] for k in smp), sum(sc["full"][k][1] for k in smp)
            if nb and nf:
                dd.append(cf / nf - cb / nb)
                hf.append(cf / nf)
        lo, hi = np.quantile(dd, [.025, .975])
        out[("calibration.H1", "agents", "paired_diff_pp")] = 100 * (k1 / n1 - k0 / n0)
        out[("calibration.H1", "agents", "paired_diff_ci_low_pp")] = 100 * lo
        out[("calibration.H1", "agents", "paired_diff_ci_high_pp")] = 100 * hi
        rl, rh = np.quantile(hf, [.025, .975])
        out[("calibration.H1", "agents", "ratio_to_humans")] = k1 / n1 / human
        out[("calibration.H1", "agents", "ratio_ci_low")] = rl / human
        out[("calibration.H1", "agents", "ratio_ci_high")] = rh / human
        return out

    @staticmethod
    def _probes():
        out = {}
        for r in D.rows("photo_probes.csv"):
            sid = f"probe.{r['probe']}"
            for st, col in (("diff_pp", "diff"), ("ci_low_pp", "ci_low"), ("ci_high_pp", "ci_high")):
                out[(sid, "twin", st)] = 100 * float(r[col])
            out[(sid, "twin", "sign")] = r["sign"]
            rule = "+" if float(r["ci_low"]) > 0 else "-" if float(r["ci_high"]) < 0 else "0"
            assert rule == r["sign"], r
        return out

    @staticmethod
    def _power():
        return {("power", "", f"tests_needed_discordance_{int(100 * q)}pct"): S.power_pairs(.10, q) for q in (.2, .3, .5)}


def consistency(v: Values) -> list[str]:
    """Checks between the published files: paired counts against the confusion matrices of both methods."""
    bad = []
    for (s, a, b), c in v.pairs.items():
        ka, kb = v.metrics(s, a)["correct"], v.metrics(s, b)["correct"]
        if c["only_a"] + c["both"] != ka or c["only_b"] + c["both"] != kb or c["n"] != v.sizes[s]:
            bad.append(f"{s}: {a} vs {b}")
    for (s, m) in v.cms:  # the same historical signs for every method of a set
        t = Counter(t for (t, _p), k in v.cms[(s, m)].items() for _ in range(k))
        t0 = Counter(t for (t, _p), k in v.cms[(s, v.any_method(s))].items() for _ in range(k))
        if t != t0:
            bad.append(f"{s}: truth of {m}")
    return bad


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    v = Values()
    out, mism, approx_bad, reported = {}, [], [], []
    for r in D.printed():
        key = (r["set"], r["method"], r["statistic"])
        name = " | ".join(x for x in key if x)
        if r["check"] == "reported":
            reported.append(r)
            continue
        got = v.get(*key)
        printed = r["value"]
        if r["check"] == "approx":
            out[name] = round(float(got), 3)
            if abs(float(got) - float(printed)) > APPROX_TOL:
                approx_bad.append((name, printed, round(float(got), 3)))
            continue
        val = rounded(r["statistic"], got)
        out[name] = val
        try:
            same = abs(float(val) - float(printed)) < 1e-9
        except ValueError:
            same = str(val) == printed
        if not same:
            mism.append((name, printed, val))
    bad = consistency(v)
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "values.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    n_exact = sum(r["check"] == "exact" for r in D.printed())
    n_derived = sum(r["check"] == "exact" and r["statistic"].startswith(DERIVED) for r in D.printed())
    n_approx = sum(r["check"] == "approx" for r in D.printed())
    lines = ["# Reproduction report (published aggregates)", "",
             f"Compared with the paper at the printed precision: {n_exact}; mismatches: {len(mism)}. Of them {n_derived} are "
             f"statistics computed by a formula (intervals, tests, accuracy metrics, kappa, calibration), {n_exact - n_derived} "
             f"are counts read from the aggregate files (for them the check is that the files match the paper).",
             f"Recomputed approximately (bootstrap over items from a confusion matrix, tolerance {APPROX_TOL}): {n_approx}; "
             f"outside the tolerance: {len(approx_bad)}.",
             f"Consistency of paired counts with the confusion matrices: {len(v.pairs)} pairs, {len(bad)} inconsistent.",
             f"Reported only (need closed per-test data, see reproducibility.md): {len(reported)}.", ""]
    for title, items in (("Mismatches", mism), ("Approximate values outside the tolerance", approx_bad)):
        if items:
            lines += [f"## {title}", "", "| Value | Paper | Recomputed |", "|---|---|---|"]
            lines += [f"| {k} | {a} | {b} |" for k, a, b in items] + [""]
    if bad:
        lines += ["## Inconsistent files", ""] + [f"- {x}" for x in bad] + [""]
    lines += ["## Reported only", "", "| Section | Set | Statistic | Value |", "|---|---|---|---|"]
    lines += [f"| {r['section']} | {r['set']} | {r['statistic']} | {r['value']} |" for r in reported]
    (ROOT / "results" / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:6]))
    for k, a, b in mism + approx_bad:
        print(f"  {k}: paper {a}, recomputed {b}")
    sys.exit(1 if mism or approx_bad or bad else 0)


if __name__ == "__main__":
    main()
