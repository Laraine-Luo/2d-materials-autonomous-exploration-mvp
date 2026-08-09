# Run 38 — repeated strategy evaluation preregistration

This document was written before executing the repeated comparison.

## Fixed environment

- Materials Project database version: 2026.04.13.
- Cohort: the same seven audited and stability-eligible MoS2 records.
- Initial set: the same three records selected without Band Gap labels.
- Budget: three sequential queries and one unrevealed holdout per policy.
- Policies: Random, Static Top-N and Iterative.
- Seeds: the explicit 20-seed list in `config/formal_repeated_evaluation_v1.json`.

## Metrics

- D2 count and hit rate;
- Band Gap query MAE;
- budget position of the first D2;
- stability violations;
- paired Iterative-minus-baseline D2 differences.

## Confidence method

For each baseline, the evaluation calculates a paired percentile-bootstrap 95%
confidence interval over 10,000 resamples of the 20 seed-level D2 differences.
The resampling seed is fixed before execution.

## Signal rules

- Positive D3 strategy signal: Iterative mean D2 is at least 10% above both
  baselines and both paired intervals exclude zero on the positive side.
- Negative D3 signal within this environment: for at least one required
  baseline, the paired interval upper bound is below the pre-registered 10%
  minimum meaningful gain.
- Otherwise the repeated evidence remains inconclusive for strategy advantage.

Any D3 classification applies only to repeated behavior within this fixed,
seven-record MP MoS2 environment. It is not evidence of general strategy
superiority, causal structure-property discovery or a new material.
