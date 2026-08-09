# Run 43 — cross-formula MX2 validation preregistration

This protocol is frozen before any oracle query in the 24-record validation
pool.

## Data boundary

- initial labelled knowledge: seven audited, stable MoS2 development records;
- independent validation pool: 24 human-approved MX2 records from MoSe2,
  MoTe2, WS2 and WSe2;
- `mp-1120746`: method quarantine and excluded;
- validation labels: accessible only through the ignored oracle file after a
  policy action;
- validation records permitted for initial training: zero.

## Budget and policies

- eight sequential queries per policy, leaving sixteen labels unrevealed;
- twenty explicit shared seeds;
- Random and Static Top-N are required baselines;
- `iterative_w035` is the sole primary iterative policy because `w=0.35` was
  used in the original environment;
- `iterative_w015` and pure uncertainty are diagnostic ablations only and may
  not replace the primary policy after results are known.

## Metrics and signal gate

Metrics include D2 count/rate, first-D2 budget, cumulative discovery curve,
query MAE, formula coverage and stability violations. The primary positive gate
requires `iterative_w035` to exceed both required baselines by at least 10% and
both paired 95% bootstrap intervals to exclude zero positively. A negative gate
is triggered if the interval upper bound against either required baseline is
below the pre-registered 10% meaningful gain.

Any result is scoped to this fixed MP cohort and does not establish experimental
performance, causality or universal active-learning superiority.
