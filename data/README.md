# Data contract

`sample_materials.csv` is deterministic synthetic demonstration data, not a source of scientific claims. It mirrors the minimum schema expected from a future C2DB/Materials Project export:

- `material_id`, `formula`, `prototype`: identity and grouping fields;
- `atomic_number_mean`, `electronegativity_mean`, `atomic_radius_mean`, `layer_thickness`, `symmetry_index`: numeric model features;
- `formation_energy_ev_atom`: known stability metadata used as a hard constraint;
- `band_gap_ev`: oracle label hidden from the policy until a query spends budget.

Run `python scripts/generate_sample_data.py` to reproduce it exactly.

