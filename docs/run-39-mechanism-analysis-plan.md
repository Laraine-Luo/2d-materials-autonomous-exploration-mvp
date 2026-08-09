# Run 39 — exploratory mechanism analysis plan

This analysis is intentionally labelled **post-result exploratory analysis**.
The Run 38 aggregate result is already known, so findings here may generate
future preregistered hypotheses but cannot retroactively become confirmatory
evidence or causal discovery.

## Questions

1. Which MP IDs are selected, omitted and selected first by each policy?
2. Does Iterative spend queries on below-target candidates more often than
   Static Top-N?
3. Is Iterative selection associated with larger bootstrap uncertainty but
   lower target yield?
4. Does feedback materially change the Iterative sequence after round one?
5. Are results concentrated in one or two records in this seven-record cohort?

## Candidate explanations to inspect

- the candidate pool is too small for feedback updates to add value;
- bootstrap uncertainty rewards candidates that are structurally distinct but
  not target-relevant;
- the fixed uncertainty weight (`w=0.35`) is too influential for this cohort;
- the initial frozen model already ranks the two target candidates effectively;
- the five structural features do not support transferable target learning.

## Outputs

- one row per seed-policy-query with predictions, uncertainty and outcomes;
- MP-ID selection/holdout/target frequency table;
- round-level policy summary;
- structure-feature and true-property table;
- a scoped result statement separating observations from hypotheses.
