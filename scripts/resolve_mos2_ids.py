#!/usr/bin/env python3
"""Resolve web-index IDs to current MP material IDs using an official API method."""

from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECRET_FILE = ROOT / ".local-secrets" / "materials_project.env"
INDEX_FILE = ROOT / "data" / "materials_project_manual_probe" / "mos2_formula_index_12.csv"
LOCAL_OUTPUT = ROOT / ".local-data" / "mos2_id_resolution.json"
AUDIT_OUTPUT = ROOT / "artifacts" / "mos2_id_resolution_audit.json"


def load_key() -> str:
    for line in SECRET_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("MP_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("MP_API_KEY missing from local ignored credential file")


def main() -> int:
    from mp_api.client import MPRester

    old_ids = []
    with INDEX_FILE.open(encoding="utf-8", newline="") as handle:
        old_ids = [row["material_id"] for row in csv.DictReader(handle)]

    mappings = []
    with MPRester(load_key(), mute_progress_bars=True) as mpr:
        database_version = mpr.db_version
        for old_id in old_ids:
            current_id = mpr.get_material_id_from_task_id(old_id)
            mappings.append({"web_index_id": old_id, "current_api_material_id": current_id})
        formula_docs = mpr.materials.summary.search(formula="MoS2", fields=["material_id"])
        formula_query_ids = sorted(str(doc.material_id) for doc in formula_docs)

    resolved = [item for item in mappings if item["current_api_material_id"]]
    unique_current = {item["current_api_material_id"] for item in resolved}
    resolved_set = set(unique_current)
    formula_set = set(formula_query_ids)
    payload = {
        "resolved_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_database": "Materials Project",
        "database_version": database_version,
        "resolution_method": "MPRester.get_material_id_from_task_id(web_index_id)",
        "credential_recorded": False,
        "mappings": mappings,
        "formula_query_material_ids": formula_query_ids,
    }
    LOCAL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    LOCAL_OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    audit = {
        "resolved_at_utc": payload["resolved_at_utc"],
        "source_database": "Materials Project",
        "database_version": database_version,
        "resolution_method": payload["resolution_method"],
        "credential_recorded": False,
        "web_ids_submitted": len(old_ids),
        "ids_resolved": len(resolved),
        "unique_current_ids": len(unique_current),
        "all_resolved_one_to_one": len(resolved) == len(old_ids) == len(unique_current),
        "formula_query_count": len(formula_query_ids),
        "resolved_ids_equal_formula_query_ids": resolved_set == formula_set,
        "resolved_only": sorted(resolved_set - formula_set),
        "formula_query_only": sorted(formula_set - resolved_set),
        "mappings": mappings,
        "interpretation": (
            "Legacy/task-ID resolution is one-to-one, but formula-query membership is audited separately. "
            "A mismatch is candidate-space drift, not an identity mapping between the two sets."
        ),
    }
    AUDIT_OUTPUT.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Resolved {len(resolved)}/{len(old_ids)} web IDs; "
        f"one-to-one={audit['all_resolved_one_to_one']}; "
        f"equals formula query={audit['resolved_ids_equal_formula_query_ids']}"
    )
    return 0 if audit["all_resolved_one_to_one"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
