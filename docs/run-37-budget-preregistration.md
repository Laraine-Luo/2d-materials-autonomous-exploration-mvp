# Run 37 — 3+3+1 budget preregistration

## Decision made before the valid rerun

The first formal MoS2 cohort contains nine records that passed identity,
dimensionality and method review, but only seven also pass the fixed stability
gate. The earlier 4+4 design therefore could not legally run.

Before inspecting any valid strategy result, the minimum closed-loop budget was
revised to:

- three initial labelled records selected by deterministic farthest-point
  sampling on standardized structural features, without Band Gap labels;
- three sequential oracle queries per policy;
- one candidate left unrevealed after each policy run.

Random, static Top-N and iterative policies share the same initial records,
eligible cohort, target interval, stability gate and query budget.

## Rationale

This is a minimum-environment boundary revision, not a strategy-specific tuning
decision. It preserves the Materials Project-only MoS2 slice, demonstrates the
prediction—selection—feedback—update loop, and retains one holdout so that the
environment does not reveal every label. The revision was recorded before the
valid rerun and must not be used to claim general strategy superiority.

## PDF mapping

- 2.1: fixes the seven-record stable cohort and 3+3+1 budget.
- 2.2: keeps a common observation/action/feedback interface for all policies.
- 2.3: defines three queries and one unrevealed record per policy.
- 3.2: preserves fair baselines through a shared initial state and budget.
- 3.3: replaces an infeasible 4+4 minimum with a preregistered feasible minimum.
- 4.1: defines the first valid formal trial.
- 4.2: records insufficient stable candidates as the reason for revision.
