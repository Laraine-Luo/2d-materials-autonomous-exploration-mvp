# 2D Materials Autonomous Exploration MVP

A minimal, reproducible evidence package for an open-exploration competition submission. The demo implements a finite-budget loop for finding **stable 2D-material candidates whose Band Gap lies in a target interval**.

> Important: the included dataset is deterministic synthetic data for validating the environment and interfaces. It must not be presented as a scientific discovery. A real C2DB or Materials Project export can later replace the CSV under the same data contract.

## What the demo proves

1. A candidate's Band Gap label is hidden until the policy spends one query.
2. Candidates violating the Formation Energy threshold are excluded before selection.
3. Every policy receives the same initial samples, stable candidate pool, target interval, and query budget.
4. The iterative policy predicts, selects, receives the true label, retrains, and repeats.
5. Random and frozen-model static Top-N baselines run through the same environment.
6. Every decision, reason, prediction, feedback value, and budget change is logged.

## Reproduce

Requires Python 3.10+ and no third-party packages.

```bash
python scripts/run_demo.py
python -m unittest discover -s tests -v
```

Outputs:

- `artifacts/summary.json`: comparable metrics for all policies;
- `artifacts/exploration_log_random.csv`;
- `artifacts/exploration_log_static_topn.csv`;
- `artifacts/exploration_log_iterative.csv`.

Regenerate the sample CSV with:

```bash
python scripts/generate_sample_data.py
```

## Environment contract

| Item | MVP definition |
|---|---|
| Fixed rules | Dataset, target interval, Formation Energy threshold, initial sample count, query budget, seed |
| Observation | Known labels, stable unexplored pool, model prediction and bootstrap uncertainty, remaining budget |
| Action | Select one stable candidate for oracle query |
| Feedback | True Band Gap, prediction error, target-hit flag, budget consumption |
| Update | Iterative policy adds feedback to training data and retrains |
| Termination | Budget exhausted or candidate pool empty |

All fixed values live in `config.json`. The default target is 1.5–2.5 eV, the stability condition is Formation Energy ≤ -0.2 eV/atom, and the query budget is 20.

## Baselines

- `random`: uniformly samples the stable candidate pool.
- `static_topn`: ranks candidates using the initial frozen model and never learns from feedback.
- `iterative`: combines target-interval score and bootstrap uncertainty, then retrains after every query.

The MVP reports hit rate and prediction MAE. A competition-grade experiment should repeat runs across several seeds and report confidence intervals before claiming superiority.

## Repository map

```text
config.json                         fixed rules and budget
data/sample_materials.csv           replaceable data source
src/materials_mvp/data.py           data contract and generator
src/materials_mvp/model.py          dependency-free predictor + uncertainty
src/materials_mvp/environment.py    observation/action/feedback loop and policies
scripts/run_demo.py                 one-command reproducible run
tests/test_demo.py                  closed-loop acceptance test
artifacts/                           generated evidence and logs
docs/pdf-evidence-2.1-4.3.md         report evidence mapped to implementation
```

## Current limits

- Synthetic data validates the product loop, not materials science validity.
- Formation Energy is treated as known metadata and a hard pre-filter.
- Bootstrap spread is a simple uncertainty proxy, not calibrated uncertainty.
- The demo searches a fixed pool; it does not generate structures or call DFT.
- A single run is evidence of operability, not evidence that the iterative policy is scientifically superior.

These limits are intentional for the initial four-page submission and define the next validation steps clearly.

