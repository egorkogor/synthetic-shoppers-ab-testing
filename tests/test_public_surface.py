"""Leak guard for the public repository: no per-test identifiers, no columns beyond the published schema and no names on the
maintainers' private deny list in any published file, this one included.

A regular-expression guard is a floor, not an audit: it cannot judge whether a sentence describes an identifiable
experiment. The substantive audit is described in reproducibility.md.

The deny list of names (organisation, internal systems and hosts) is deliberately not in the repository: it would
itself disclose them. Maintainers keep it in an untracked file `.leak_guard_words` (one regular expression per line,
ignored by git) or in the environment variable LEAK_GUARD_WORDS (separated by "|"); without it that check is skipped.
"""
import csv
import os
import re
import subprocess
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TEXT = {".md", ".csv", ".py", ".txt", ".json", ".svg", ".tex", ".cfg", ".toml", ".yml", ".yaml", ""}
# a letter followed by two digits: the form of per-test, per-comparison, group, product and setup labels
ID = re.compile(r"\b(?:[TNGMPBHS]\d{2}C?|PA-\d+)\b")
SCHEMA = {
    "data/aggregate_confusion.csv": ["set", "n", "method", "truth", "pred", "count"],
    "data/aggregate_paired.csv": ["set", "n", "method_a", "method_b", "only_a", "only_b", "both", "neither"],
    "data/aggregate_results.csv": ["section", "set", "method", "statistic", "value", "check"],
    "data/calibration.csv": ["measure", "denominator", "agents_before_k", "agents_before_n", "agents_after_k",
                             "agents_after_n", "humans_share_pct", "humans_n_approx", "human_data"],
    "data/calibration_h1_scenarios.csv": ["version", "scenario", "added", "compared"],
    "data/photo_probes.csv": ["probe", "screen", "n_pairs", "mean_a", "mean_b", "diff", "ci_low", "ci_high", "sign"],
    "demo/data/synthetic_tests.csv": ["test", "theta", "z", "truth"],
    "demo/data/synthetic_scenarios.csv": ["test", "scenario", "outcome_a", "outcome_b"],
    "demo/data/synthetic_direct.csv": ["test", "k", "sign", "confidence"],
}


def published():
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT,
                         capture_output=True, text=True, encoding="utf-8", check=True).stdout.split("\n")
    return [ROOT / p for p in out if p and (ROOT / p).exists()]


def text_of(p: Path) -> str:
    if p.suffix == ".zip":
        with zipfile.ZipFile(p) as z:
            return "\n".join(z.read(n).decode("utf-8", errors="replace") for n in z.namelist() if n.endswith(".tex"))
    if p.suffix == ".pdf":
        pymupdf = pytest.importorskip("pymupdf")
        return "\n".join(page.get_text() for page in pymupdf.open(p))
    return p.read_text(encoding="utf-8", errors="replace")


def scanned():
    return [p for p in published() if p.suffix.lower() in TEXT | {".pdf", ".zip"}]


def deny_list():
    words = os.environ.get("LEAK_GUARD_WORDS", "")
    f = ROOT / ".leak_guard_words"
    if f.exists():
        words = "|".join(filter(None, [words, *(ln.strip() for ln in f.read_text(encoding="utf-8").splitlines())]))
    return re.compile(f"(?i){words}") if words else None


def test_no_per_test_identifiers():
    hits = [(p.relative_to(ROOT).as_posix(), m.group(0)) for p in scanned() for m in ID.finditer(text_of(p))]
    assert not hits, hits[:20]


def test_no_names_from_the_private_deny_list():
    words = deny_list()
    if words is None:
        pytest.skip("no private deny list (.leak_guard_words or LEAK_GUARD_WORDS)")
    hits = [(p.relative_to(ROOT).as_posix(), m.group(0)) for p in scanned() for m in words.finditer(text_of(p))]
    assert not hits, hits[:20]


def test_csv_files_follow_the_published_schema():
    for p in published():
        if p.suffix != ".csv":
            continue
        rel = p.relative_to(ROOT).as_posix()
        assert rel in SCHEMA, f"unexpected CSV {rel}"
        with p.open(encoding="utf-8", newline="") as f:
            rows = list(csv.reader(f))
        assert rows[0] == SCHEMA[rel], (rel, rows[0])
        if rel.startswith("demo/data/"):
            assert all(r[0].startswith("syn") for r in rows[1:]), rel


def test_no_per_test_tables_in_the_paper():
    for p in published():
        if p.suffix == ".md":
            rows = [ln for ln in p.read_text(encoding="utf-8").splitlines() if re.match(r"\|\s*[A-Z]\d{2}\s*\|", ln)]
            assert not rows, (p.name, rows[:3])


def test_no_archives_or_binaries_besides_figures_pdf_and_the_arxiv_package():
    allowed = {".png", ".pdf"}
    odd = [p.relative_to(ROOT).as_posix() for p in published() if p.suffix.lower() not in TEXT | allowed]
    assert odd in ([], ["paper/arxiv_submission.zip"]), odd
    zp = ROOT / "paper" / "arxiv_submission.zip"
    if zp.exists():
        with zipfile.ZipFile(zp) as z:
            assert set(z.namelist()) <= {"main.tex"} | {f"figures/{f.name}" for f in (ROOT / "paper" / "figures").glob("*.png")}


def test_printed_values_appear_in_the_paper():
    """Every value checked by reproduce.py is a number printed in paper/paper_EN.md (a coarse check of the transcription)."""
    text = (ROOT / "paper" / "paper_EN.md").read_text(encoding="utf-8").replace("−", "-")
    nums = set()
    for m in re.finditer(r"[-+]?\d[\d,]*\.?\d*", text):
        try:
            nums.add(round(float(m.group(0).replace(",", "").lstrip("+")), 6))
        except ValueError:
            pass
    missing = []
    with (ROOT / "data" / "aggregate_results.csv").open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            try:
                x = float(r["value"])
            except ValueError:
                continue
            if not {round(x, 6), round(abs(x), 6)} & nums:
                missing.append((r["set"], r["method"], r["statistic"], r["value"]))
    assert not missing, missing[:10]
