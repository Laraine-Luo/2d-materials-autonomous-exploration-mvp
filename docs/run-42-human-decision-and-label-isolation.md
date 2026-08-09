# Run 42 — signed MX2 decision and label isolation

The project owner signed the decision:

> 批准24条建议，mp-1120746继续隔离。

The transaction grants validation-candidate status to 24 records and retains
`mp-1120746` in method quarantine. It grants training eligibility to zero
records, preserving the new formula families as an evaluation cohort.

The Agent observation interface contains MP ID, formula, five structural
features and stability metadata but no Band Gap. Oracle labels are stored in an
ignored local file and may be revealed only by an environment query. Public
passports store a SHA-256 commitment to each label rather than the numeric
value. The public MP index remains an audit artifact, not an Agent input.

The decision transaction is idempotent for the exact same signed text and
timestamp. The application script refuses to overwrite it with a different
decision.

## PDF mapping

- 2.1: validation and training eligibility are separate fixed states;
- 2.2: Band Gap is hidden from observation and revealed only by feedback;
- 2.3: the signed transaction and label commitments are retained;
- 3.1: human approval is evidence-gate promotion, not a discovery event;
- 4.2: interface-level label leakage is tested explicitly;
- 4.3: public evidence can be checked without publishing the local oracle file.
