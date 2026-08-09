# Run 40 — MX2 index acquisition attempt

## Codex-network attempt

The preregistered six-formula query was attempted with the pinned official
`mp-api` client. The Codex execution environment failed DNS resolution for
`api.materialsproject.org` before any formula data were returned.

- returned records: 0;
- public credential value recorded: no;
- fallback web transcription or synthetic substitution: no;
- scientific/index claim produced: no.

The macOS Terminal entry point then executed the identical preregistered request
outside the restricted Codex network.

## Formal terminal result

- Materials Project database version: 2026.04.13;
- returned records: 44 unique MP IDs;
- formula counts: MoS2 12, MoSe2 7, MoTe2 7, WS2 7, WSe2 5, WTe2 6;
- duplicate MP IDs: 0;
- Formation Energy primary-gate pass: 37;
- combined fixed stability prefilter pass: 32;
- public credential value recorded: no.

The successful sanitized audit replaced the earlier transport-failure status at
`artifacts/mp_mx2_validation_index_audit.json`. Raw response data remain in the
ignored local-data directory. All 44 public index rows remain quarantined and
carry no dimensionality, training or discovery eligibility.

## PDF mapping

- 2.1: the independent validation boundary is fixed before acquisition;
- 2.3: API failure is logged without consuming a scientific query budget;
- 3.3: no index or discovery success is claimed when transport returns zero;
- 4.1: the next formal acquisition input and reproducible entry point exist;
- 4.2: DNS/network failure path stops rather than substituting another source;
- 4.3: credentials and raw responses remain excluded from the public package.
