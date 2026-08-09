"""Generate quarantined evidence passports for all 12 MP MoS2 index records."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/materials_project_manual_probe/mos2_formula_index_12.csv"
OUTPUT_DIR = ROOT / "artifacts/mos2_passports"


def passport(row: dict) -> dict:
    return {
        "passport_version": "0.1.0",
        "material_id": row["material_id"],
        "formula": row["formula"],
        "chemical_system": row["chemical_system"],
        "materials_project_index_path": f"Materials Explorer > {row['chemical_system']} > {row['formula']} > {row['material_id']}",
        "source_database": "Materials Project",
        "source_surface": "Materials Explorer",
        "database_version_observed_on_web": row["database_version"],
        "web_index_evidence": {
            "crystal_system": row["crystal_system"],
            "space_group": row["space_group"],
            "sites": int(row["sites"]),
            "energy_above_hull_ev_atom_display": row["web_energy_above_hull_ev_atom"],
            "band_gap_ev_display": row["web_band_gap_ev"],
        },
        "official_api_evidence": {
            "status": "pending_transport",
            "identity_match": "pending",
            "database_version_frozen": "pending",
            "origins_task_id": None,
            "thermo_run_type": None,
            "required_properties_verified": False,
        },
        "manual_audit": {
            "dimensionality_review": "pending",
            "dimensionality_evidence": [],
            "calculation_method_review": "pending",
            "reviewer": None,
            "reviewed_at": None,
        },
        "exploration_status_training_eligible": False,
        "exploration_status_query_state": "manual_review",
        "exploration_status_discovery_level": "D0",
        "exploration_status_manual_review_required": True,
        "promotion_decision": "blocked",
        "blocking_reasons": [
            "official_api_identity_pending",
            "database_version_freeze_pending",
            "dimensionality_review_pending",
            "calculation_method_review_pending",
            "required_properties_pending",
        ],
        "claim_boundary": "Web index evidence only; not a training record, D2 candidate, strategy result or new-material claim.",
    }


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with SOURCE.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        target = OUTPUT_DIR / f"{row['material_id']}.json"
        # Keep the richer manually observed mp-1434 passport as the primary record.
        if row["material_id"] == "mp-1434":
            continue
        target.write_text(json.dumps(passport(row), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Passport set ready for {len(rows)} records (mp-1434 uses its richer primary passport)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
