#!/usr/bin/env python3
"""Acquire a lightweight MP-only MX2 formula index without exposing credentials."""

from __future__ import annotations

import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "mp_mx2_validation_index_v1.json"
SECRET_PATH = ROOT / ".local-secrets" / "materials_project.env"
LOCAL_OUTPUT = ROOT / ".local-data" / "mp_mx2_validation_index_raw.json"
PUBLIC_CSV = ROOT / "artifacts" / "mp_mx2_validation_index.csv"
PUBLIC_AUDIT = ROOT / "artifacts" / "mp_mx2_validation_index_audit.json"


def load_local_env() -> None:
    if not SECRET_PATH.exists():
        return
    for raw in SECRET_PATH.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def serialize(document) -> dict:
    row = document.model_dump(mode="json")
    row["material_id"] = str(document.material_id)
    return row


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    load_local_env()
    api_key = os.environ.get("MP_API_KEY")
    audit = {
        "attempted_at_utc": datetime.now(timezone.utc).isoformat(),
        "queue_id": config["queue_id"],
        "source_database": "Materials Project",
        "client": "mp-api==0.46.4",
        "credential_recorded": False,
        "formula_queries": config["chemical_scope"]["formula_queries"],
        "requested_fields": config["requested_index_fields"],
        "status": "attempted",
    }
    if not api_key:
        audit.update({"status": "failed", "error_type": "MissingCredential"})
        PUBLIC_AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Local MP credential is unavailable; audit written without a credential value", file=sys.stderr)
        return 1

    records = []
    counts = {}
    db_version = None
    try:
        from mp_api.client import MPRester

        with MPRester(api_key, mute_progress_bars=True) as mpr:
            db_version = mpr.db_version
            for formula in config["chemical_scope"]["formula_queries"]:
                documents = mpr.materials.summary.search(
                    formula=formula,
                    fields=config["requested_index_fields"],
                )
                formula_rows = [serialize(document) for document in documents]
                counts[formula] = len(formula_rows)
                role = config["cohort_roles"][formula]
                for row in formula_rows:
                    row["query_formula"] = formula
                    row["cohort_role"] = role
                    records.append(row)
    except Exception as exc:
        message = str(exc).replace(api_key, "[REDACTED]")
        audit.update({
            "status": "failed",
            "error_type": type(exc).__name__,
            "error_message": message,
            "records_returned": 0,
        })
        PUBLIC_AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"MX2 index probe failed: {type(exc).__name__}", file=sys.stderr)
        return 1

    records.sort(key=lambda row: (row["query_formula"], row["material_id"]))
    seen = set()
    duplicates = []
    for row in records:
        if row["material_id"] in seen:
            duplicates.append(row["material_id"])
        seen.add(row["material_id"])
    local_payload = {
        "retrieved_at_utc": audit["attempted_at_utc"],
        "database_version": db_version,
        "query_config": config,
        "records": records,
    }
    LOCAL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    LOCAL_OUTPUT.write_text(json.dumps(local_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    public_rows = []
    for row in records:
        public_rows.append({
            "material_id": row["material_id"],
            "query_formula": row["query_formula"],
            "formula_pretty": row.get("formula_pretty"),
            "chemsys": row.get("chemsys"),
            "band_gap_ev": row.get("band_gap"),
            "formation_energy_ev_atom": row.get("formation_energy_per_atom"),
            "energy_above_hull_ev_atom": row.get("energy_above_hull"),
            "is_stable_mp_flag": row.get("is_stable"),
            "last_updated": row.get("last_updated"),
            "cohort_role": row["cohort_role"],
            "exploration_status_index_only": True,
            "exploration_status_dimensionality": "not_audited",
            "exploration_status_training_eligible": False,
        })
    with PUBLIC_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(public_rows[0]))
        writer.writeheader()
        writer.writerows(public_rows)

    stability_primary = sum(
        row.get("formation_energy_per_atom") is not None and row["formation_energy_per_atom"] <= -0.2
        for row in records
    )
    stability_combined = sum(
        row.get("formation_energy_per_atom") is not None
        and row["formation_energy_per_atom"] <= -0.2
        and (
            (row.get("energy_above_hull") is not None and row["energy_above_hull"] <= 0.1)
            or bool(row.get("is_stable"))
        )
        for row in records
    )
    audit.update({
        "status": "success",
        "database_version": db_version,
        "records_returned": len(records),
        "records_by_formula": counts,
        "unique_material_ids": len(seen),
        "duplicate_material_ids": sorted(set(duplicates)),
        "primary_formation_energy_pass_count": stability_primary,
        "combined_stability_prefilter_pass_count": stability_combined,
        "raw_response_location": ".local-data/mp_mx2_validation_index_raw.json (git-ignored)",
        "public_index_location": "artifacts/mp_mx2_validation_index.csv",
        "interpretation": "Index acquisition only; every record remains quarantined pending explicit structure, dimensionality and method audit.",
    })
    PUBLIC_AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
