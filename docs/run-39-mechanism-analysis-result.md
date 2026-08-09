# Run 39 — exploratory mechanism result

## Direct observations

- Static Top-N queried both target records (`mp-1025874`, `mp-1023939`) in all
  20 runs. Their first two rounds therefore had a 100% D2 rate.
- Static Top-N never queried the below-target `mp-1018809` (Band Gap 1.3361 eV)
  and used it as the holdout in all 20 runs.
- Iterative queried `mp-1018809` in all 20 runs. It omitted `mp-1023939` twice
  and `mp-1025874` three times.
- Mean selected uncertainty was 0.0785 eV for Iterative and 0.0619 eV for
  Static Top-N. Iterative produced eight distinct query sequences; Static
  produced two.
- Iterative D2 rates by round were 70%, 45% and 60%. Static rates were 100%,
  100% and 0%.

## Interpretation boundary

The uncertainty term demonstrably changed the search path and increased path
diversity, but in this four-candidate query pool it repeatedly allocated budget
to a below-target record and occasionally omitted a target record. This is a
plausible explanation for the Run 38 result, not a causal proof.

## Hypotheses for a future preregistered test

1. Static ranking is sufficient when the initial model already separates the
   two target records in a tiny pool.
2. `w=0.35` overprices bootstrap uncertainty for this cohort.
3. Three feedback steps are insufficient to recover the opportunity cost of an
   exploratory miss.
4. Bootstrap spread over five simple structural features is not calibrated to
   target-discovery value.

Testing these hypotheses requires a new preregistered experiment, preferably a
larger MP-only 2D cohort, an untouched evaluation split, and an uncertainty-
weight ablation. The current run must not be used to tune `w` and then re-score
the same seven records as confirmatory evidence.

## PDF mapping

- 3.1: mechanism interpretation for the scoped D3 negative signal;
- 3.2: selection-frequency evidence behind the baseline comparison;
- 4.2: small-pool opportunity cost and post-result tuning leakage risks.
