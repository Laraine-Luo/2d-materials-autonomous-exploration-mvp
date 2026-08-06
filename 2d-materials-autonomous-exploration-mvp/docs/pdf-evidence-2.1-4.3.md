# PDF 2.1–4.3 evidence map

This is a report-writing source derived from the runnable MVP, not a claim that real-material validation is complete.

## 2.1 Fixed rules

State the environment boundary precisely: a fixed candidate pool, fixed feature schema, hidden Band Gap oracle, Formation Energy ≤ -0.2 eV/atom, target Band Gap 1.5–2.5 eV, 12 initial labeled samples, 20 oracle queries, and seed 42. Cite `config.json` and show a compact boundary table. Rules cannot be changed by a policy during a run.

## 2.2 Observation / action / feedback

Use a loop figure: known samples + stable pool + predictions + uncertainty + remaining budget → select one candidate → reveal true Band Gap + error + hit flag → update training set. Cite one row from `artifacts/exploration_log_iterative.csv`. The policy never observes an unqueried Band Gap.

## 2.3 Records and budget

Show the log schema: round, policy, material ID, formula, prediction, uncertainty, true Band Gap, Formation Energy, stability flag, hit flag, error, reason, and budget. Each query costs one unit; the run terminates at 20. Cite the CSV and `summary.json`.

## 3.1 What counts as discovery

For the MVP, pre-register these signals:

- positive candidate: queried material satisfies both the stability and target Band Gap constraints;
- model anomaly: large high-confidence prediction error (threshold to be calibrated on real validation data);
- stable negative result: no target hit in a predeclared region after a minimum number of queries;
- failure mode: iterative strategy does not exceed random/static baselines across repeated seeds;
- problem revision: evidence that target interval, stability threshold, feature representation, or uncertainty proxy is not scientifically defensible.

Do not call hits in the synthetic dataset material discoveries. They only demonstrate that signals can be detected and recorded.

## 3.2 Trivial / random / no-intervention references

Random selection is the chance baseline. Frozen static Top-N is the no-learning baseline. The iterative policy is compared under identical initial labels, pool, constraints, and budget. Compare target-hit count/rate, queries to first hit, unique prototype coverage, and MAE trajectory. Superiority should require repeated-seed improvement with uncertainty intervals; the one-run summary is only a smoke test.

## 3.3 Minimum success and failure standards

Minimum technical success: one command completes all three 20-query runs, every selection respects stability, labels remain hidden before query, logs contain 20 complete rows per policy, and rerunning seed 42 reproduces identical artifacts. Scientific-strategy success should be pre-registered after a real dataset audit (recommended: statistically reliable improvement over both baselines across repeated seeds). Failure is declared if leakage occurs, constraints are violated, results are seed-fragile, or the iterative policy fails to improve. Retain logs and revise the hypothesis rather than redefining success afterward.

## 4.1 One trial run

Input: config plus CSV. Steps: generate/load data → initialize identical labeled/pool split → run random, static Top-N, and iterative policies → consume 20 queries each → save logs and summary → run acceptance test. Output: three logs, one comparison summary, console table. Use the actual console table or a cropped log row as evidence.

## 4.2 Main risks and failure paths

| Risk | Detection evidence | Response |
|---|---|---|
| Synthetic-to-real gap | real-data distribution/schema audit | replace CSV; rerun unchanged interface |
| Label leakage | test observation payload and code review | keep oracle label inside environment only |
| Biased/uncalibrated uncertainty | calibration and repeated-seed plots | replace or calibrate uncertainty estimator |
| Stability proxy too weak | literature/domain review | add decomposition energy/dynamic stability stages |
| DFT provenance mismatch | dataset metadata audit | restrict or harmonize calculation settings |
| Strategy wins by seed luck | repeated seeds and intervals | report negative result; revise policy |

## 4.3 Reproduction and open source

The repository currently uses Python 3.10+ standard library only, deterministic generation, fixed seed, versioned configuration, one-command run, and automated acceptance test. Plan to publish source, config, schema, logs, license, and real-data provenance/usage terms. Any future Materials Project/C2DB data must follow its license and redistribution conditions; disclose versions and retrieval date.

## Figures with highest four-page value

1. Environment boundary and hidden-label diagram (supports 2.1–2.2).
2. One complete prediction–selection–feedback–update loop with a real log row (supports 2.2–2.3).
3. Baseline comparison table/plot generated from repeated real-data runs (supports 3.1–3.3).
4. Minimal validation and risk/evidence flow (supports 4.1–4.3).
