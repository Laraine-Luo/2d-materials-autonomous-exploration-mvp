# Run 38 — repeated evaluation result statement

## Result

Twenty preregistered seeds were run on the same seven-record Materials Project
MoS2 environment, with three common initial records and three queries per
policy. No stability violation occurred.

| Policy | Mean D2 / 3 | Mean hit rate | Mean MAE (eV) | Mean budget to first D2 |
|---|---:|---:|---:|---:|
| Random | 1.45 | 48.33% | 0.06884 | 1.80 |
| Static Top-N | 2.00 | 66.67% | 0.01960 | 1.00 |
| Iterative | 1.75 | 58.34% | 0.06053 | 1.30 |

Iterative minus Random had a paired mean D2 difference of +0.30 with a 95%
bootstrap interval of [0.05, 0.55]. Iterative minus Static Top-N had a paired
mean difference of -0.25 with an interval of [-0.45, -0.05].

## Interpretation

Iterative exceeded Random inside this fixed environment but did not exceed
Static Top-N. Because the preregistered positive rule required it to exceed both
baselines, the positive D3 gate failed. The upper bound against Static Top-N was
also below the preregistered minimum meaningful gain of +0.20 D2 hits, so the
result is classified as a D3 negative strategy signal: **the iterative policy
did not achieve its preregistered advantage within this environment**.

This does not show that active learning is generally inferior to static
screening. Seeds represent repeated algorithmic trajectories over one small,
fixed cohort, not independent material datasets. No causal, cross-material or
new-material claim is made.

## PDF mapping

- 3.1: an executable example of a repeated negative strategy signal;
- 3.2: paired Random, Static Top-N and Iterative comparison;
- 3.3: the preregistered positive gate failed and negative gate passed;
- 4.1: reproducible 20-seed validation after the minimum closed-loop run;
- 4.2: fixed-cohort dependence is retained as the principal external-validity risk.
