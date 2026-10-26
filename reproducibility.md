# Reproducibility

The study has two parts with different status:

- **Open:** the method, the protocols, the prompt templates, the statistics code and its tests, a synthetic demonstration, and every result reported over sets of tests.
- **Closed:** the empirical validation. The 47 tests of the bank and the 25 comparisons of the blind held-out set are internal A/B experiments of a retailer. Their identifiers, descriptions, screens, metrics, per-test outcomes, effect sizes, z-statistics and the per-test forecasts of every method are not published, nor are the customer data, profile cards, filled-in prompts, the simulator and the reconstructed app.

The corporate results are therefore **not** reproducible by an external reader. What a reader can do is listed below.

## What can be recomputed

`python reproduce.py` reads only the files in `data/` and compares every recomputed value with the value printed in the paper (`data/aggregate_results.csv`):

| Status | Values | What it covers | Inputs |
|---|---:|---|---|
| exact, computed | 401 | Wilson intervals, McNemar p, Tango and Clopper–Pearson intervals, Δ in pp, outcome-group and balanced accuracy, Cohen's kappa, calibration shares and the paired H1 interval, power | confusion matrices and paired correctness counts per evaluation set; calibration counts and the 60 calibration scenarios (agent sessions only); synthetic photo probes |
| exact, read | 693 | correct signs, discordant pairs, composition of sets, "0" answers, opposite signs, photo probes: counts that are read from the aggregate files, so the check only shows that the files match the paper | same files |
| approx | 26 | bootstrap intervals over tests (kappa, accuracy by outcome groups) | confusion matrices; the paper resampled the same pairs in the original order of the tests, which is closed, so the recomputed bounds agree within 0.011 (tolerance 0.02) |
| reported | 102 | rank associations (Spearman ρ, permutation p, bootstrap intervals, partial ρ, rank combinations, fragility of the blind-set association), the replicability model, agreement of signs between runs, mechanical "0", parse errors, the sign-rule check on every run | per-test values, closed; listed in `results/report.md` for reference |

In addition, `reproduce.py` checks that every paired count agrees with the confusion matrices of both methods (134 pairs).

The code behind the reported-only rank and replicability values is published and tested on synthetic data (`src/abeval/stats.py`, `src/abeval/replicability.py`, `tests/`, `demo/`), but its inputs are not. Not published: the recovery of z-values from the closed reports, the extraction of effects for the blind set, the detection of mechanical "0", and the simulator itself. **Nothing is reconstructed from the aggregates:** no per-test rows are simulated or imputed. The approximate bootstrap uses the multiset of (prediction, truth) pairs that a confusion matrix gives exactly; only the order of the draws differs from the paper.

## What cannot be checked externally

- The historical labels of the tests and the composition of every evaluation set.
- Whether each change was conveyed to the agent as described (Appendix H.1 gives only aggregate counts).
- Every statistic that needs per-test values (the "reported" rows above).
- The simulation itself: profiles, scenarios, screens, trajectories, agents' free-text answers and their coding, costs.
- The behavioural human references (Table 6 and Appendix H.7): internal aggregates of the retailer's app, printed as rounded shares with denominators by order of magnitude.
- The chronology of the blind set and the roles in it: the run rule, the frozen inputs and the deviations are commits in an internal repository without an external timestamp. The sealed ground truth was hashed before the first model call (SHA-256 `d5b6fcd9a9236d61796ef4461e31a82bcb2fa04b49e3b83a2f945dbbf0886bc1`); the file itself contains internal identifiers and stays closed, so the hash can only be checked by someone given the file.

These parts rest on the authors' description in the paper.

## What the public version no longer contains

The first upload of this repository (25 October 2026) contained anonymized per-test data. It was replaced by this de-identified version and the repository was recreated, so its history holds only this version; copies of the first upload made by others cannot be withdrawn. Removed:

| Removed | Was | Replaced by |
|---|---|---|
| `data/tests.csv` | per-test class, historical sign, effect group, effect rank, rounded z, set membership | Table A.1 and `aggregate_confusion.csv` |
| `data/direct_answers.csv`, `data/blind_direct_answers.csv` | every direct-forecast answer per test | confusion matrices and paired counts of the direct forecasts |
| `data/twin_results.csv`, `data/blind_comparisons.csv` | the twin's per-test interval and sign in every run; blind-set signs, effect ranks, flags | confusion matrices and paired counts of the twin |
| `data/probability_readout.csv` | the probability-mode response per test | rank values reported only |
| `data/photo_ab1_products.csv`, `data/photo_ab1_reasons.csv` | a real photo A/B test: per-product human sign and change rank, agent pairs | the agent's pooled response and one statement over the three real photo tests (Section 7.2) |
| `expected/paper_values.json` | printed values, including per-test rows | `data/aggregate_results.csv` (printed values over sets only) |
| `paper/arxiv_submission.zip`, `paper/paper_EN.pdf` | builds of the earlier text with per-test appendices | rebuilt from the current `paper/paper_EN.md` (`tools/build_arxiv.py`) |

In the paper (English `paper/paper_EN.md` and Russian `paper/paper_RU.md`, cleaned the same way): the per-test tables of Appendix A (signs, effect groups, direct and twin answers by setup), Appendix H.1 (what changed in each test and how it reached the agent) and Appendix H.4 (signs of the four transfer tests) were replaced by aggregates; test labels were removed from the text; statements about individual tests (the two bank photo tests, a test that could not be shown in a static frame, the pair of indistinguishable tests, the pooled-scenario errors, the transfer control, a z-value, the five disclosed blind comparisons and their signs, the "lower is better" comparisons, the largest effects of the blind set) were dropped or generalised.

### Effect on the results

- **No reported number was changed.** The numbers that remain are those of the earlier edition. Before the per-test data were withdrawn, the 607 values computable from them matched the paper with 0 mismatches; the aggregates published here were then exported from the same data, and 1,094 printed values are matched from them (401 recomputed by formula) with 0 mismatches.
- **The photo finding is kept as one statement over three tests.** The earlier edition discussed the real photo tests one by one. The public version keeps only the summary that the human response to a photo change was reproduced in none of the three real tests (two in the bank, one outside it), together with the agent-side evidence (synthetic photo probes and the agent's pooled response on the real test outside the bank). Their individual outcomes, the products and the per-product human results are not published.
- **Lost detail:** per-test inspection of errors (which tests the twin, the direct forecasts and "always zero" got right), the per-test mapping of changes to conveyance and metrics, effect-size ranks and z-values. Readers can no longer recompute rank correlations or the replicability model, which the first upload allowed approximately.

## Threat model of the de-identification

The confidential information is the outcome of an identifiable corporate experiment. A test becomes identifiable through an identifier, a description of its change, its screens or a combination of files. The public version therefore contains:

- no identifiers, including the pseudonymous test and comparison labels of the first upload, which are gone from every file;
- no description of any individual change linked to an outcome or a forecast; changes are described only as categories with counts (Appendix H.1);
- results only over evaluation sets that are themselves not identifiable (setups, Summary-27, the blind set and its pre-registered variants); the smallest printed set has three tests;
- no per-test effects, ranks or z-values, so effects cannot be recovered from several tables.

Overlapping sets do let someone derive the result of an unnamed item from two aggregates: for example, the 36 and 33 one-screen sets differ by the three pilot tests selected by outcome (the paper itself says the frozen version got all three right), the bank and the 44 run tests differ by three tests that were not run, and the 20 and 19 blind comparisons differ by the arm added after the disclosure. None of these items is described, so the derived result cannot be linked to a real experiment without the closed reports. Small groups that *are* describable are reported without their individual outcomes: the four transfer tests by counts only (no confusion matrix), the pair of indistinguishable tests without their signs, and the three real photo tests by one summary statement (the human response was reproduced in none of them), which the data owner's request for anonymized A/B results allows.

`tests/test_public_surface.py` is a regular-expression floor over every file of the repository (identifiers, per-test columns, internal names, archives); it is not a substitute for the substantive review described above.

This de-identification minimizes what is disclosed. It is not by itself a permission to publish the aggregates; that decision rests with the owner of the data.

## Corrections after the blind reviews (26 October 2026)

Two independent reviews of this public version (run without access to the closed data) found an error in the permutation p-value of the rank associations: the observed ρ and the permuted ρ were computed by different formulas, so with tied ranks permutations reproducing the observed ρ exactly were sometimes dropped, which could only make p smaller. The function is fixed (`src/abeval/stats.py`, test against full enumeration in `tests/test_stats.py`). Recomputed on the closed data, two printed p-values change in the third decimal, 0.023 → 0.024 (Table H.8.2, without the sign discrepancy) and 0.078 → 0.079 (the blind-set click ρ without the largest effect, abstract and Sections 6.3, H.8); no other printed p-value of the bank or the blind set changes, and no conclusion about significance changes. One value outside the published reproduction (ρ ≈ +0.05 on 18 tests, p = 0.426, Section 6.3) was computed by a separate closed script and not rechecked; the error can only have lowered it, so it remains non-significant.
