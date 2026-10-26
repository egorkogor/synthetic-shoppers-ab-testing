"""The synthetic demo runs end to end and its aggregates give the same statistics as its rows."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "demo"))
import make_synthetic  # noqa: E402


def test_generator_is_deterministic_and_matches_committed_data():
    tests, scenarios, direct = make_synthetic.generate()
    assert len(tests) == 40 and len(scenarios) == 40 * 150 and len(direct) == 120
    committed = (ROOT / "demo" / "data" / "synthetic_tests.csv").read_text(encoding="utf-8").splitlines()
    assert len(committed) == 41 and committed[1].startswith(tests[0]["test"] + ",")
    assert all(t["test"].startswith("syn") for t in tests)


def test_demo_runs_and_round_trips():
    r = subprocess.run([sys.executable, str(ROOT / "demo" / "run_demo.py")], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "equal those from the rows: yes" in r.stdout
