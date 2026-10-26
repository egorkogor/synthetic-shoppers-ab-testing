"""Loading the published aggregates (see data/README.md). No per-test rows exist in this repository."""
import csv
from collections import Counter, defaultdict
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "data"
LABELS = ("+", "0", "-", "?", "tie")  # "?" a three-way tie of direct answers, "tie" a zero point difference of the twin


def rows(name: str) -> list[dict]:
    with (DATA / name).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def confusion() -> tuple[dict, dict]:
    """(set, method) -> Counter{(historical sign, predicted sign): count}; set -> number of items."""
    cms, sizes = defaultdict(Counter), {}
    for r in rows("aggregate_confusion.csv"):
        cms[(r["set"], r["method"])][(r["truth"], r["pred"])] += int(r["count"])
        sizes.setdefault(r["set"], int(r["n"]))
    for (s, m), cm in cms.items():
        assert sum(cm.values()) == sizes[s], (s, m)
    return dict(cms), sizes


def paired() -> dict:
    """(set, method_a, method_b) -> numbers of items where only a, only b, both or neither is right."""
    out = {}
    for r in rows("aggregate_paired.csv"):
        c = {k: int(r[k]) for k in ("n", "only_a", "only_b", "both", "neither")}
        assert c["only_a"] + c["only_b"] + c["both"] + c["neither"] == c["n"], r
        out[(r["set"], r["method_a"], r["method_b"])] = c
    return out


def expand(cm: Counter) -> tuple[list, list]:
    """A confusion matrix as two aligned label lists in a canonical order (not the order of any real items).
    Point statistics do not depend on the order; bootstraps over items do, so their recomputation is approximate."""
    pred, truth = [], []
    for (t, p), k in sorted(cm.items(), key=lambda x: (LABELS.index(x[0][0]), LABELS.index(x[0][1]))):
        pred += [p] * k
        truth += [t] * k
    return pred, truth


def printed() -> list[dict]:
    """Printed values of the paper, one per row (data/aggregate_results.csv)."""
    return rows("aggregate_results.csv")
