# Methodology

This file describes the research protocol of the paper *"Can We Simulate Customer Behavior and Use It to Predict A/B Test Outcomes?"* without the closed material: no test of the bank or of the blind set is identified or described, and no per-test outcome is given. Section numbers refer to [paper/paper_EN.md](paper/paper_EN.md). What can and cannot be checked from this repository is in [reproducibility.md](reproducibility.md).

## Research question

Can a population of LLM shopper agents with behavioural profiles predict the outcome of interface A/B tests (the sign of the change in the primary metric, and the order of tests by effect size) better than simple competitors: a direct forecast by the same language model from the test description, stronger models, and the rules "always zero" and "always +"? Separately: how close are the agents' actions to human actions, and does bringing them closer transfer to forecast accuracy?

Hypotheses tested, each with a stated status (pilot, exploratory, or set and criterion recorded before the run): simulation gives more correct signs than the direct forecast and "always zero"; its responses rank effects; ten improvements of the simulator (input closer to what a person sees, the fold and semantic changes, a visit instead of one action, more scenarios, a realistic environment, a longer visit, behaviour closer to humans, a stronger agent model, action probabilities, combination with the direct forecast) raise accuracy (Section 8).

## Units

- **Unit of evaluation:** one historical A/B test (in the blind set, one comparison of a variant with A). A historical "+" or "−" is a significant change of the primary metric in B relative to A under the rule of the original report; "0" is no significant change.
- **Unit of simulation:** a scenario with one profile card, one visit goal and one start state, run through A and B separately. More scenarios reduce simulator noise but do not add independent experiments.

## Data used (closed)

- **Bank:** 47 internal historical tests of one grocery retailer with an unambiguous sign (18 "+", 22 "0", 7 "−"), from 68 reports found; four mixed cases and 17 out-of-scope, borderline or algorithmic changes without a screen were excluded. Tests are grouped into classes F (findability and path), P (preference and interpretation of the design) and R (recommendations of additional products).
- **Blind held-out set:** 25 comparisons from 23 further tests outside the bank (two tests have a third arm).
- **Shopper population:** tens of thousands of shoppers described over a six-month window; held-out human events of other accounts for behavioural calibration.

None of these are published. Aggregate composition: Appendix A of the paper.

## Agent and environment

- **Profile card** from purchases and app events: tenure, stable basket patterns, usual order size, visit time, discounts; no explicit demographics. **Goal** from a purchase in which the tested screen could have been met. Profile and goal are identical in A and B. The catalogue of personas and missions was built before the runs and not tuned on the results.
- **Agent rules:** [prompts/agent.md](prompts/agent.md). The agent imitates a real shopper with a goal, does not know about the test or the other variant, and does not rate the design.
- **Visit:** at each step the agent gets the rules, profile, goal, time, visit history, cart and a phone screenshot, and answers with one action (tap with coordinates, scroll, back, search query, leave). One call per step. Limits: 5 or 10 steps in A/B forecasting, 30 in behavioural calibration.
- **Representations** (Table 1 of the paper): action list, HTML, screenshot with coordinate taps, a second frame after scrolling, sessions in a reconstructed catalogue with search, categories, product cards and a cart.
- **Models:** claude-haiku-5-5 for the agents (claude-sonnet-5-5 in one comparison), called through Claude Code with an empty working folder and the study's own system prompt; default sampling parameters.

## Forecasts and competitors

- **Twin sign rule (Section 5.1):** the paired difference B − A per scenario, mean over scenarios, 95% percentile bootstrap over scenario pairs (2 000 resamples): "+" above zero, "−" below, "0" otherwise. Implemented for the demo as `paired_sign` in [src/abeval/stats.py](src/abeval/stats.py).
- **Direct forecast:** [prompts/direct_forecast.md](prompts/direct_forecast.md); three answers per test from each of Haiku, Sonnet and Opus 5.5, sign by strict majority, a three-way tie "?" counts as wrong.
- **Simple rules:** "always zero", "always +", and the most frequent outcome within the test's class excluding the test itself.

## Pre-recorded rules

Before each run after the pilots: the set of tests, the metric, the success criterion. Examples: at least 10 of 15 correct signs for the realistic catalogue; for probability ranking a positive ρ with one-sided p < 0.05 and no lower than direct Opus; for the blind set, more correct signs than both "always zero" and direct Haiku at p < 0.05 in both exact McNemar tests. Paired intervals, McNemar tests, group metrics and rank combinations were computed after the experiments under rules recorded before the computation and are exploratory. The full summary is Appendix C of the paper; the original records are commits in an internal repository without an external timestamp.

## Statistics

In [src/abeval/stats.py](src/abeval/stats.py) and [src/abeval/replicability.py](src/abeval/replicability.py), tested on synthetic inputs in [tests/](tests/):

- Wilson 95% intervals for proportions of correct signs;
- exact two-sided McNemar test on discordant pairs; Tango score interval for a paired difference of proportions; Clopper–Pearson with Bonferroni as a conservative check;
- accuracy by outcome groups (mean of accuracy on tests with an effect and on null tests; 0.5 for "always zero"), standard three-class balanced accuracy, Cohen's kappa with a percentile bootstrap over tests;
- Spearman ρ with a one-sided permutation p (10 000 permutations, the share of permuted ρ at least as large, without the +1 correction, so a p of 0 is possible in principle; the smallest p in the paper is 0.005) and a paired bootstrap of the difference of correlations (20 000 resamples); partial ρ and rank combinations;
- a model-based estimate of verdict replicability from recovered z-statistics (flat prior and spike-and-slab sensitivity), Section 5.5; the recovery of z from the closed reports is not published;
- the McNemar power approximation of Section 5.3.

## Blind held-out protocol (Section 6.2, Appendix H.8)

1. The run rule is committed before the builder starts.
2. An operator who has seen the outcomes prepares the package: report texts truncated at the first place with an outcome, decision and profit fields and outcome words removed; the ground truth (sign of the first primary metric and the mapping of neutral numbers to reports) is sealed and hashed.
3. A separate builder agent without access to outcomes selects the tests by a fixed rule and assembles the inputs (passports for the twin, screens, descriptions for the direct models); the inputs are frozen with a commit.
4. Any disclosure after freezing is recorded as a deviation; the main analysis and a sensitivity analysis without the disclosed items are fixed before unsealing. In the paper's run the signs of five comparisons reached the builder after their inputs were frozen; afterwards it added a third arm of one test and, after a blind cross-check, corrected five other screens. A sensitivity analysis without all inputs changed after the disclosure (those five screens included) was not computed.
5. The frozen twin and the direct forecasts run; then the truth is unsealed. Any later analysis (here: the rank association) is labelled exploratory.

## Behavioural calibration (Section 7.1)

H1 is the share of agent sessions with an add-to-cart in which at least two different product cards were opened, compared with the human share on held-out events. Adoption criterion recorded before the run: agent-to-human ratio of 0.67–1.5; starting product cards no farther from humans than the baseline; search and category pages between 0.67 of the lower and 1.5 of the upper bound of the human reference. The paired change of H1 on the same 60 scenarios is recomputed from [data/calibration_h1_scenarios.csv](data/calibration_h1_scenarios.csv).
