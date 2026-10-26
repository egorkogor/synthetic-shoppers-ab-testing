# Data

All files are UTF-8 CSV. They contain **aggregates over evaluation sets only**: no test, comparison or product identifier, no description of a change, no per-test outcome, effect, rank or z-value, and no customer data. What is closed and why: [../reproducibility.md](../reproducibility.md).

Signs: `+` a significant increase of the primary metric in B relative to A (for two "lower is better" metrics of the blind set, an improvement), `-` a significant decrease, `0` no significant difference; `?` a three-way tie of the direct forecasts (counts as wrong); `tie` a zero point difference of the twin (binary metric only).

## aggregate_confusion.csv

One row per cell of a confusion matrix: `set`, `n` (items in the set), `method`, `truth` (historical sign), `pred` (predicted sign), `count`. Only the methods a printed value needs are included.

## aggregate_paired.csv

Two methods on the same set: `set`, `n`, `method_a`, `method_b`, `only_a`, `only_b`, `both`, `neither` (items where only a, only b, both or neither is right). These are the inputs of the exact McNemar test, the Tango interval and the Clopper–Pearson check. `reproduce.py` checks them against the confusion matrices.

## aggregate_results.csv

Every printed number of the paper that summarizes tests, one per row: `section`, `set`, `method`, `statistic`, `value`, `check` (`exact`, `approx` or `reported`, see [../reproducibility.md](../reproducibility.md)). A method `a_vs_b` is a paired comparison; `history` is the historical composition of the set.

## Sets

| Set | Paper |
|---|---|
| `setup.action_list`, `setup.html`, `setup.coordinates` | pilots, Table 2 |
| `setup.fold` | exploratory pilot (fold and semantic changes) |
| `setup.heldout_screens` | held-out screens |
| `setup.reco_first`, `setup.reco_replication`, `setup.reco_pooled` | recommendation sessions: first sample, replication, both pooled |
| `setup.design` | design sessions |
| `setup.catalogue`, `setup.cut2`, `setup.cut3` | realistic catalogue and its truncations |
| `setup.onescreen_extra` | one screen, additional check |
| `setup.frozen36`, `setup.frozen33` | the frozen one-screen version on all 36 one-screen tests, and without the three selected by outcome |
| `summary27.first`, `.replication`, `.pooled` | Summary-27 with each variant of the recommendations (Table 3) |
| `summary27.*.combination` | the three rules combining the twin with the direct forecast (Section 8.10) |
| `summary27.direct_tie_rules` | the two tie rules of the direct forecast (Appendix D) |
| `all44.*` | all 44 tests with a twin forecast, one forecast per test |
| `bank47` | the direct forecasts on the whole bank |
| `frames43` | direct forecasts with the agent's frames against text (Section 4.3) |
| `heldout12.agent_model` | the agent model swapped on the held-out screens (Section 8.8) |
| `transfer4` | the four transfer tests (Section 7.3) |
| `h1.*` | subsets of Appendix H.1: change conveyed in full, action metric, money or order metric |
| `binary.*` | tests with a historical effect only, the twin's point sign against "always +" (Appendix F, Table F.1) |
| `direction.*` | tests with a recovered z: direction of the point estimate (Appendix H.2) |
| `blind.broad25`, `.strict8`, `.without_exposed20`, `.exposed5`, `.without_exposed_and_late19`, `.without_mechanical_zero19` | the blind held-out set and its variants (Section 6.2, Appendix H.8) |
| `pooled61` | the frozen version on the 36 bank tests and the 25 blind comparisons, pooled descriptively |

Methods: `twin`, `twin_point` (sign of the point difference), `twin_*` (other runs of the twin), `haiku`, `sonnet`, `opus` (direct forecasts, strict majority), `*_first_answer` (the other tie rule), `*_frames`, `comb_*`, `always_zero`, `always_plus`.

## calibration.csv

Table 6 and Section 7.1: agent counts before and after the calibration and the human reference shares. The human values are internal aggregates of the retailer's app: rounded shares and rounded denominators (about 14k for H1; the two largest only by order of magnitude).

## calibration_h1_scenarios.csv

Section 7.1: for each of the 60 calibration scenarios and each version (`base`, `full`), whether the agent added a product (`added`) and whether, in a session with an add, it opened at least two different product cards (`compared`). Agent sessions only; scenario numbers are positions in the run, not customer identifiers.

## photo_probes.csv

Section 7.2: probes on synthetic screens built around the agent's own goal, 150 scenarios each, outcome "add to cart" on the marked product. `card`: KF1 the photo shows another product, KF2 no photo, K4 the price doubled (control). `listing`: a 2 x 2 listing of similar products, KG1 a grey, dark, blurred photo of the same product, KG2 the price +30% (control). Columns: `n_pairs`, `mean_a`, `mean_b`, `diff`, `ci_low`, `ci_high` (95% percentile bootstrap over scenario pairs), `sign`.
