# Run 40 — MP-only MX2 validation index preregistration

This scope was frozen before querying the new formula families.

## Purpose

The seven-record MoS2 cohort remains the development environment. A second,
larger Materials Project-only candidate index will be built from MX2 formula
families, where M is Mo or W and X is S, Se or Te.

## Formula roles

- `MoS2`: development-cohort drift control only;
- `MoSe2`, `MoTe2`, `WS2`, `WSe2`, `WTe2`: independent validation candidate
  sources.

## Stage boundary

Run 40 performs only a lightweight official-API formula index query. Returned
records remain quarantined. Formula identity does not prove two-dimensionality,
stability, method consistency, training eligibility or discovery status.

The query records MP ID, formula, chemical system, Band Gap, Formation Energy,
Energy Above Hull, MP stability flag and update time. Raw responses remain in
the ignored local-data directory. The repository-visible index contains source
metadata and candidate rows but no credential.

## Next gate

After index acquisition, the fixed stability rule may reduce the number of
records requiring structure retrieval. Explicit retained MP IDs must then pass
the same dimensionality and calculation-method audit used for MoS2. No model
weight or search strategy may be tuned on the validation formulas before a new
evaluation protocol is frozen.
