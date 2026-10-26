"""Demo of the evaluation protocol on the SYNTHETIC bank of demo/data (see demo/make_synthetic.py). Nothing here comes from
the closed bank of the paper; the numbers say nothing about real shoppers or real tests.

Steps, as in sections 5-6 of the paper:
  1. per synthetic test: the twin's sign by the paired bootstrap rule, the direct forecast by majority of three answers
  2. correct signs of the twin, the direct forecast, "always zero" and "always +"; Wilson intervals; exact McNemar and the
     Tango interval for the twin against each competitor; accuracy by outcome groups, balanced accuracy, kappa and its
     bootstrap interval; Spearman rho of the twin's difference with the "human" z and its permutation p; the binary metric
  3. the same rows reduced to the aggregate files of the public repository (confusion matrices, paired correctness) and the
     statistics recomputed from those aggregates: they must match step 2, which is what reproduce.py relies on

    python demo/run_demo.py     -> results/demo/report.md, results/demo/aggregate_confusion.csv, aggregate_paired.csv
"""
import csv
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from abeval import stats as S  # noqa: E402

DATA, OUT = ROOT / "demo" / "data", ROOT / "results" / "demo"


def read(name):
    with (DATA / name).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def per_test(boot: int = 2000):
    tests = {r["test"]: r for r in read("synthetic_tests.csv")}
    diffs = {}
    for r in read("synthetic_scenarios.csv"):
        diffs.setdefault(r["test"], []).append(int(r["outcome_b"]) - int(r["outcome_a"]))
    twin, point = {}, {}
    for k, (t, d) in enumerate(sorted(diffs.items())):
        twin[t], point[t], _lo, _hi = S.paired_sign(d, b=boot, seed=k)
    answers = {}
    for r in read("synthetic_direct.csv"):
        answers.setdefault(r["test"], []).append(r)
    direct, score = {}, {}
    for t, a in answers.items():
        c = Counter(x["sign"] for x in a).most_common()
        direct[t] = "?" if len(c) > 1 and c[0][1] == c[1][1] else c[0][0]
        score[t] = np.mean([{"+": 1, "-": -1}.get(x["sign"], 0) * int(x["confidence"]) / 10 for x in a])
    truth = {t: r["truth"] for t, r in tests.items()}
    z = {t: float(r["z"]) for t, r in tests.items()}
    return truth, z, twin, point, direct, score


def evaluate(truth, z, twin, point, direct, score) -> dict:
    ids = sorted(truth)
    methods = {"twin": twin, "direct": direct, "always_zero": {t: "0" for t in ids}, "always_plus": {t: "+" for t in ids}}
    res = {}
    for m, p in methods.items():
        res[m] = S.confusion_metrics([p[t] for t in ids], [truth[t] for t in ids])
        res[m]["wilson"] = S.wilson(res[m]["correct"], len(ids))
    ok = {m: [p[t] == truth[t] for t in ids] for m, p in methods.items()}
    res["paired"] = {}
    for c in ("direct", "always_zero", "always_plus"):
        a = sum(x and not y for x, y in zip(ok["twin"], ok[c]))
        b = sum(y and not x for x, y in zip(ok["twin"], ok[c]))
        res["paired"][c] = dict(only_a=a, only_b=b, p=S.mcnemar(a, b), tango=S.tango_ci(a, b, len(ids)))
    res["kappa_ci"] = S.group_accuracy_boot({t: twin[t] for t in ids}, {t: truth[t] for t in ids}, b=2000)["kappa_ci"]
    rk = S.ranking(point, z, score, ids)
    res["rank"] = dict(twin_rho=rk["twin_rho"], twin_p=rk["twin_p"], direct_rho=rk["opus_rho"], direct_p=rk["opus_p"])
    eff = [t for t in ids if truth[t] != "0"]
    sg = {t: "+" if point[t] > 0 else "-" if point[t] < 0 else "tie" for t in eff}
    a = sum(sg[t] == truth[t] and truth[t] == "-" for t in eff)
    b = sum(sg[t] != truth[t] and truth[t] == "+" for t in eff)
    res["binary"] = dict(n=len(eff), twin=sum(sg[t] == truth[t] for t in eff), always_plus=sum(truth[t] == "+" for t in eff),
                         p=S.mcnemar(a, b))
    return res


def to_aggregates(truth, twin, direct):
    """The de-identification step of the public repository, on synthetic rows: only counts leave this function."""
    ids = sorted(truth)
    methods = {"twin": twin, "direct": direct, "always_zero": {t: "0" for t in ids}, "always_plus": {t: "+" for t in ids}}
    conf = [("synthetic40", len(ids), m, t, p, k) for m, pr in methods.items()
            for (t, p), k in sorted(Counter((truth[i], pr[i]) for i in ids).items())]
    pairs = []
    for c in ("direct", "always_zero", "always_plus"):
        a = [twin[i] == truth[i] for i in ids]
        b = [methods[c][i] == truth[i] for i in ids]
        pairs.append(("synthetic40", len(ids), "twin", c, sum(x and not y for x, y in zip(a, b)),
                      sum(y and not x for x, y in zip(a, b)), sum(x and y for x, y in zip(a, b)),
                      sum(not x and not y for x, y in zip(a, b))))
    return conf, pairs


def from_aggregates(conf, pairs) -> dict:
    cms = {}
    for _s, _n, m, t, p, k in conf:
        cms.setdefault(m, Counter())[(t, p)] += k
    out = {}
    for m, cm in cms.items():
        pred, tr = [], []
        for (t, p), k in cm.items():
            pred += [p] * k
            tr += [t] * k
        out[m] = S.confusion_metrics(pred, tr)
    out["paired"] = {r[3]: dict(only_a=r[4], only_b=r[5], p=S.mcnemar(r[4], r[5])) for r in pairs}
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    truth, z, twin, point, direct, score = per_test()
    res = evaluate(truth, z, twin, point, direct, score)
    conf, pairs = to_aggregates(truth, twin, direct)
    back = from_aggregates(conf, pairs)
    same = all(back[m][k] == res[m][k] for m in ("twin", "direct", "always_zero", "always_plus")
               for k in ("correct", "kappa", "outcome_group_acc", "balanced_acc", "zero_answers"))
    same &= all(back["paired"][c]["p"] == res["paired"][c]["p"] for c in res["paired"])
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "aggregate_confusion.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["set", "n", "method", "truth", "pred", "count"])
        w.writerows(conf)
    with (OUT / "aggregate_paired.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["set", "n", "method_a", "method_b", "only_a", "only_b", "both", "neither"])
        w.writerows(pairs)
    n = len(truth)
    comp = Counter(truth.values())
    lines = ["# Demo on a SYNTHETIC bank (not real experiments)", "",
             f"{n} synthetic tests: {comp['+']} '+', {comp['0']} '0', {comp['-']} '-' (generated by demo/make_synthetic.py).", "",
             "| Method | Correct | Wilson 95% | Effect tests | Null tests | Outcome-group acc. | Kappa |", "|---|---|---|---|---|---|---|"]
    for m in ("twin", "direct", "always_zero", "always_plus"):
        r = res[m]
        og = "-" if r["outcome_group_acc"] is None else f"{r['outcome_group_acc']:.2f}"
        lines.append(f"| {m} | {r['correct']}/{n} | {100 * r['wilson'][0]:.1f}-{100 * r['wilson'][1]:.1f}% | "
                     f"{r['effect_correct']}/{r['effect_n']} | {r['null_correct']}/{r['null_n']} | {og} | {r['kappa']:.2f} |")
    lines += ["", "| Twin against | Only twin : only competitor | McNemar p | Tango 95%, pp |", "|---|---|---|---|"]
    for c, r in res["paired"].items():
        lines.append(f"| {c} | {r['only_a']}:{r['only_b']} | {r['p']:.3f} | [{100 * r['tango'][0]:.1f}; {100 * r['tango'][1]:.1f}] |")
    rk, bi = res["rank"], res["binary"]
    lines += ["", f"Twin kappa, bootstrap 95%: [{res['kappa_ci'][0]:.2f}; {res['kappa_ci'][1]:.2f}].",
              f"Spearman rho with the 'human' z: twin {rk['twin_rho']:+.3f} (one-sided p {rk['twin_p']:.3f}), "
              f"direct score {rk['direct_rho']:+.3f} (p {rk['direct_p']:.3f}).",
              f"Binary metric on the {bi['n']} tests with an effect: twin {bi['twin']}, 'always +' {bi['always_plus']} "
              f"(McNemar p {bi['p']:.3f}).", "",
              f"Statistics recomputed from the aggregate files equal those from the rows: {'yes' if same else 'NO'}."]
    (OUT / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    sys.exit(0 if same else 1)


if __name__ == "__main__":
    main()
