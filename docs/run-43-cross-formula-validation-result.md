# Run 43 — cross-formula MX2 validation result

## Environment

- seven labelled MoS2 development records;
- 24 label-isolated validation candidates across MoSe2, MoTe2, WS2 and WSe2;
- eight sequential queries, sixteen unrevealed labels per run;
- twenty shared seeds;
- zero validation records used for initial training;
- zero stability violations.

The validation pool contains eight target-window records: six WS2 and two WSe2.

## Aggregate result

| Policy | Role | Mean D2 / 8 | Hit rate | Query MAE/eV | First D2 budget |
|---|---|---:|---:|---:|---:|
| Random | required baseline | 2.60 | 32.50% | 0.3028 | 2.80 |
| Static Top-N | required baseline | 3.85 | 48.13% | 0.2568 | 2.70 |
| Iterative w=0.35 | primary | 3.40 | 42.50% | 0.3021 | 4.00 |
| Iterative w=0.15 | diagnostic only | 4.70 | 58.75% | 0.2234 | 2.90 |
| Pure uncertainty | diagnostic only | 1.85 | 23.13% | 0.4032 | 5.60 |

Primary Iterative minus Random was +0.80 D2 with paired bootstrap 95% CI
[0.10, 1.60]. Primary Iterative minus Static Top-N was -0.45 with CI
[-0.90, 0.00]. The primary strategy therefore exceeded Random but failed the
pre-registered requirement to exceed both baselines; its minimum meaningful
advantage over Static was excluded.

## Discovery-signal classification

`D3_negative_no_preregistered_cross_formula_advantage`

This reproduces the scoped failure mode outside the MoS2-only micro-pool: the
original uncertainty weight does not achieve its preregistered dual-baseline
advantage. The `w=0.15` ablation performs best descriptively, but the
anti-cherry-pick rule prohibits replacing `w=0.35` as the primary result after
observation. It is a hypothesis for a future independent cohort, not a positive
claim from this cohort.

Pure uncertainty performs worst on yield, MAE and first-discovery budget. This
supports the interpretation that uncalibrated uncertainty alone is not a useful
discovery objective in the current feature/model setting.

## Claim boundary

The result concerns repeated algorithmic trajectories over one fixed MP MX2
cohort. It does not show experimental performance, causality, universal active-
learning inferiority or new-material discovery.
