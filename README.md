# Synthetic shoppers vs. direct LLM forecasts on historical A/B tests

Paper (English and Russian), aggregate results and statistics code of *"Can We Simulate Customer Behavior and Use It to Predict A/B Test Outcomes?"*.

The paper compares a population of LLM shopper agents with behavioural profiles against a direct forecast of the same language model on 47 internal historical A/B tests of a grocery retailer (18 positive, 22 null, 7 negative), and on a blind held-out set of 25 further comparisons. Neither the simulation nor its calibration showed a stable advantage over the direct forecast; on the bank the direct forecasts themselves did not beat "always zero". On the blind set, whose inputs were initially built by an agent that did not see the outcomes (five signs later reached it; see below), the frozen version was right in 10 of 25 against 12 for "always zero" and 15 for the strongest direct forecast.

**The A/B tests are proprietary and closed.** This repository publishes the method, the protocols and results over sets of tests; it does not contain identifiable individual tests: no identifiers, no descriptions of individual changes, no per-test outcomes or forecasts. A few results of unnamed, undescribed items can be derived by comparing overlapping sets; reproducibility.md lists them. See [reproducibility.md](reproducibility.md) for what can and cannot be checked.

## Contents

- [paper/paper_EN.md](paper/paper_EN.md) — the paper (English), with [figures](paper/figures/); [paper/paper_EN.pdf](paper/paper_EN.pdf) and the arXiv LaTeX package [paper/arxiv_submission.zip](paper/arxiv_submission.zip) are built from it by `tools/build_arxiv.py` (pandoc and tectonic).
- [paper/paper_RU.md](paper/paper_RU.md) — the Russian version of the same paper (the study was written in Russian first), with [Russian figures](paper/figures_ru/) and a reading copy [paper/paper_RU_preview.pdf](paper/paper_RU_preview.pdf).
- [methodology.md](methodology.md) — the research protocol without the closed material.
- [reproducibility.md](reproducibility.md) — what is open, what is closed, what changed in the de-identification, and its threat model.
- [data/](data/README.md) — aggregate results: every printed number that summarizes tests, confusion matrices and paired correctness counts per evaluation set, calibration counts, synthetic photo probes.
- [src/abeval/](src/abeval/) — the statistics: Wilson intervals, exact McNemar, Tango score interval, Clopper–Pearson with Bonferroni, accuracy by outcome groups, balanced accuracy, Cohen's kappa with bootstrap, Spearman ρ with permutation p, rank combinations, the paired sign rule.
- [reproduce.py](reproduce.py) — recomputes the printed values that follow from the aggregates and compares them with the paper.
- [demo/](demo/README.md) — a fully synthetic bank (not derived from any real test) on which the whole evaluation protocol runs end to end.
- [prompts/](prompts/) — the direct-forecast prompt and the agent rules; examples are fictional.
- [tests/](tests/) — tests of the statistics, of the reproduction, of the demo, and a leak guard over every file.

## Run

```
pip install -r requirements.txt
python reproduce.py          # results/report.md; exit code 1 on any mismatch
python demo/run_demo.py      # results/demo/report.md
python -m pytest -q
```

Tested with Python 3.13, NumPy 2.2.2, SciPy 1.18.1 and pytest 8.4.

`reproduce.py` recomputes 401 printed statistics exactly from the published counts (intervals, tests, accuracy metrics, kappa, calibration) and 26 bootstrap intervals approximately, and checks 693 printed counts against the aggregate files, with no mismatch; 102 values (rank associations, the replicability model and others) need per-test data and are listed as reported only.

## Status of the results

The check on the bank is retrospective: the historical outcomes were known to the developer. Compositions of sets and success criteria were fixed before the corresponding runs where the paper says so; paired intervals, McNemar tests, group metrics and rank combinations were computed after the experiments. On the blind held-out set the tests are still historical, but their inputs were initially built by an agent without access to the outcomes and the truth was sealed and hashed before the first model call. The signs of five comparisons later reached the builder after their inputs were frozen; it then added a third arm of one test and corrected five other screens, and results without the disclosed comparisons and the added arm are reported separately; the records are commits in an internal repository without an external timestamp (paper, Sections 6.2 and 11, Appendix H.8).

## License

Code: MIT (see `LICENSE`). Aggregate data, documentation and prompts: CC BY 4.0.
