#!/usr/bin/env python3
"""Collect method provenance for Band Gap and stability without auto-approval."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECRET_FILE = ROOT / ".local-secrets" / "materials_project.env"
RAW_SUMMARY = ROOT / ".local-data" / "materials_project_probe.json"
LOCAL_OUTPUT = ROOT / ".local-data" / "mos2_method_evidence.json"
AUDIT_OUTPUT = ROOT / "artifacts" / "mos2_method_evidence_audit.json"


def load_key() -> str:
    for line in SECRET_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("MP_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("MP_API_KEY missing from local ignored credential file")


def public_id(value) -> str | None:
    return str(value) if value is not None else None


def entry_run_type(entry) -> str | None:
    parameters = getattr(entry, "parameters", None) or {}
    value = parameters.get("run_type") if isinstance(parameters, dict) else None
    return str(value) if value is not None else None


def main() -> int:
    from mp_api.client import MPRester

    summary_payload = json.loads(RAW_SUMMARY.read_text(encoding="utf-8"))
    material_ids = summary_payload["requested_material_ids"]
    summaries = {row["material_id"]: row for row in summary_payload["data"]}
    electronic_task_ids = sorted({
        origin["task_id"]
        for row in summaries.values()
        for origin in row.get("origins", [])
        if origin.get("name") == "electronic_structure" and origin.get("task_id")
    })

    with MPRester(load_key(), mute_progress_bars=True) as mpr:
        database_version = mpr.db_version
        task_docs = mpr.materials.tasks.search(
            task_ids=electronic_task_ids,
            fields=["task_id", "run_type", "task_type"],
        ) if electronic_task_ids else []
        thermo_docs = mpr.materials.thermo.search(
            material_ids=material_ids,
            fields=[
                "material_id", "thermo_type", "entries",
                "formation_energy_per_atom", "energy_above_hull", "is_stable",
            ],
        )

    task_map = {
        public_id(doc.task_id): {
            "run_type": str(doc.run_type) if doc.run_type is not None else None,
            "task_type": str(doc.task_type) if doc.task_type is not None else None,
        }
        for doc in task_docs
    }
    thermo_by_material: dict[str, list[dict]] = {mid: [] for mid in material_ids}
    for doc in thermo_docs:
        entries = []
        for entry_type, entry in (doc.entries or {}).items():
            entries.append({
                "entry_type": str(entry_type),
                "entry_id": public_id(getattr(entry, "entry_id", None)),
                "run_type": entry_run_type(entry),
            })
        thermo_by_material.setdefault(public_id(doc.material_id), []).append({
            "thermo_type": str(doc.thermo_type),
            "entries": entries,
            "formation_energy_per_atom": doc.formation_energy_per_atom,
            "energy_above_hull": doc.energy_above_hull,
            "is_stable": doc.is_stable,
        })

    records = []
    for material_id in material_ids:
        origins = summaries[material_id].get("origins", [])
        electronic_ids = [
            o["task_id"] for o in origins
            if o.get("name") == "electronic_structure" and o.get("task_id")
        ]
        band_gap_methods = [
            {"task_id": task_id, **task_map.get(task_id, {"run_type": None, "task_type": None})}
            for task_id in electronic_ids
        ]
        thermo_evidence = thermo_by_material.get(material_id, [])
        records.append({
            "material_id": material_id,
            "band_gap_origin_methods": band_gap_methods,
            "stability_thermo_methods": thermo_evidence,
            "band_gap_method_resolved": bool(band_gap_methods) and all(x["run_type"] for x in band_gap_methods),
            "stability_method_resolved": bool(thermo_evidence) and all(
                doc["thermo_type"] and doc["entries"] for doc in thermo_evidence
            ),
            "manual_review_required": True,
        })

    payload = {
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_database": "Materials Project",
        "database_version": database_version,
        "credential_recorded": False,
        "method_paths": {
            "band_gap": "summary.origins[electronic_structure].task_id -> tasks.run_type/task_type",
            "stability": "thermo.thermo_type -> thermo.entries[*].parameters.run_type",
        },
        "records": records,
    }
    LOCAL_OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    audit = {
        "retrieved_at_utc": payload["retrieved_at_utc"],
        "source_database": "Materials Project",
        "database_version": database_version,
        "credential_recorded": False,
        "materials_requested": len(material_ids),
        "electronic_structure_task_ids_requested": len(electronic_task_ids),
        "task_documents_returned": len(task_docs),
        "thermo_documents_returned": len(thermo_docs),
        "band_gap_method_resolved_count": sum(r["band_gap_method_resolved"] for r in records),
        "stability_method_resolved_count": sum(r["stability_method_resolved"] for r in records),
        "manual_review_required_count": len(records),
        "records": records,
        "interpretation": (
            "Method evidence was collected on separate Band Gap and stability paths. "
            "No record is automatically approved."
        ),
    }
    AUDIT_OUTPUT.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Method evidence: band gap {audit['band_gap_method_resolved_count']}/{len(records)}, "
        f"stability {audit['stability_method_resolved_count']}/{len(records)} resolved; manual review retained"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

