#!/usr/bin/env python3
"""Freeze the MX2 structure-audit queue using role and stability only."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "artifacts" / "mp_mx2_validation_index.csv"
AUDIT = ROOT / "artifacts" / "mp_mx2_structure_queue_freeze_audit.json"
OUTPUT = ROOT / "config" / "mp_mx2_structure_audit_queue_v1.json"


def as_bool(value: str) -> bool:
    return value.lower() == "true"


def main() -> int:
    with INDEX.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    selected = []
    rejected = []
    for row in rows:
        role_pass = row["cohort_role"] == "independent_validation_candidate_source"
        primary = float(row["formation_energy_ev_atom"]) <= -0.2
        auxiliary = float(row["energy_above_hull_ev_atom"]) <= 0.1 or as_bool(row["is_stable_mp_flag"])
        decision = role_pass and primary and auxiliary
        record = {
            "material_id": row["material_id"],
            "query_formula": row["query_formula"],
            "role_pass": role_pass,
            "formation_energy_primary_pass": primary,
            "auxiliary_stability_pass": auxiliary,
        }
        (selected if decision else rejected).append(record)
    selected.sort(key=lambda row: row["material_id"])
    payload = {
        "queue_id": "mp-mx2-structure-audit-v1",
        "source_database": "Materials Project",
        "database_version": "2026.04.13",
        "selection_fields_used": [
            "cohort_role",
            "formation_energy_ev_atom",
            "energy_above_hull_ev_atom",
            "is_stable_mp_flag"
        ],
        "band_gap_used_for_selection": False,
        "material_ids": [row["material_id"] for row in selected],
        "record_count": len(selected),
        "requested_summary_fields": ["material_id", "formula_pretty", "structure", "origins"],
        "status_after_acquisition": "quarantined_pending_dimensionality_and_method_audit"
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    audit = {
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "queue_id": payload["queue_id"],
        "selection_fields_used": payload["selection_fields_used"],
        "band_gap_used_for_selection": False,
        "selected_count": len(selected),
        "selected_by_formula": {
            formula: sum(row["query_formula"] == formula for row in selected)
            for formula in ("MoSe2", "MoTe2", "WS2", "WSe2", "WTe2")
        },
        "selected_records": selected,
        "rejected_count": len(rejected),
        "interpretation": "The structure queue was frozen without reading or ranking Band Gap values."
    }
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
