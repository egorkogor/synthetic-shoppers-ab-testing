"""reproduce.py on the published aggregates: no mismatch with the printed values, consistent files."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from abeval import data as D  # noqa: E402


def test_reproduce_has_no_mismatch():
    r = subprocess.run([sys.executable, str(ROOT / "reproduce.py")], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "mismatches: 0" in r.stdout


def test_aggregate_files_load_and_agree():
    cms, sizes = D.confusion()
    pairs = D.paired()
    for (s, a, b), c in pairs.items():
        assert (s, a) in cms and (s, b) in cms, (s, a, b)
        assert c["n"] == sizes[s]
    checks = {r["check"] for r in D.printed()}
    assert checks <= {"exact", "approx", "reported"}
