"""Build a public, non-training audit queue from the MP web index manifest."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "materials_project_manual_probe" / "mos2_formula_index_12.csv"
OUTPUT = ROOT / "artifacts" / "mos2_record_audit_queue.csv"


def main() -> int:
    with SOURCE.open(encoding="utf-8") as f:
        records = list(csv.DictReader(f))
    queue = []
    for row in records:
        queue.append({
            "material_id": row["material_id"],
            "formula": row["formula"],
            "api_identity_match": "pending",
            "database_version_frozen": "pending",
            "dimensionality_review": "pending",
            "dimensionality_evidence": "",
            "calculation_method_review": "pending",
            "source_calculation_method": "",
            "method_task_id": "",
            "required_property_check": "pending",
            "formation_energy_ev_atom": "",
            "energy_above_hull_ev_atom": row["web_energy_above_hull_ev_atom"],
            "is_stable_mp_flag": "",
            "band_gap_ev": row["web_band_gap_ev"],
            "exploration_status_training_eligible": "False",
            "exploration_status_query_state": "manual_review",
            "exploration_status_discovery_level": "D0",
            "exploration_status_manual_review_required": "True",
            "blocking_reasons": "api_identity;dimensionality;calculation_method;required_properties",
            "reviewer_conclusion": "",
        })
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(queue[0]))
        writer.writeheader()
        writer.writerows(queue)
    print(f"Wrote {len(queue)} quarantined records to artifacts/mos2_record_audit_queue.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
