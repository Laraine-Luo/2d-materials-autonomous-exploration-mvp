#!/usr/bin/env python3
"""Collect MX2 method provenance and Robocrys review evidence without approval."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECRET = ROOT / ".local-secrets" / "materials_project.env"
SUMMARY_RAW = ROOT / ".local-data" / "mp_mx2_structure_response.json"
DIM_AUDIT = ROOT / "artifacts" / "mp_mx2_dimensionality_evidence_audit.json"
LOCAL_OUTPUT = ROOT / ".local-data" / "mp_mx2_method_robocrys_evidence.json"
AUDIT_OUTPUT = ROOT / "artifacts" / "mp_mx2_method_robocrys_evidence_audit.json"
DOC_OUTPUT = ROOT / "docs" / "mp-mx2-method-robocrys-review.md"


def load_key() -> str:
    for raw in SECRET.read_text(encoding="utf-8").splitlines():
        if raw.startswith("MP_API_KEY="):
            return raw.split("=", 1)[1].strip()
    raise RuntimeError("MP_API_KEY unavailable")


def public(value) -> str | None:
    return str(value) if value is not None else None


def entry_run_type(entry) -> str | None:
    parameters = getattr(entry, "parameters", None) or {}
    value = parameters.get("run_type") if isinstance(parameters, dict) else None
    return str(value) if value is not None else None


def main() -> int:
    from mp_api.client import MPRester

    key = load_key()
    summary = json.loads(SUMMARY_RAW.read_text(encoding="utf-8"))
    dimensions = json.loads(DIM_AUDIT.read_text(encoding="utf-8"))
    material_ids = summary["requested_material_ids"]
    summaries = {row["material_id"]: row for row in summary["records"]}
    dim_map = {row["material_id"]: row for row in dimensions["records"]}
    uncertain_ids = sorted(
        row["material_id"] for row in dimensions["records"]
        if row["proposed_dimensionality_status"] == "uncertain_2d"
    )
    electronic_task_ids = sorted({
        origin["task_id"]
        for row in summaries.values()
        for origin in row.get("origins", [])
        if origin.get("name") == "electronic_structure" and origin.get("task_id")
    })
    audit_base = {
        "attempted_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_database": "Materials Project",
        "requested_material_count": len(material_ids),
        "uncertain_dimensionality_count": len(uncertain_ids),
        "credential_recorded": False,
        "status": "attempted"
    }
    try:
        with MPRester(key, mute_progress_bars=True) as mpr:
            database_version = mpr.db_version
            task_docs = mpr.materials.tasks.search(
                task_ids=electronic_task_ids,
                fields=["task_id", "run_type", "task_type"]
            ) if electronic_task_ids else []
            thermo_docs = mpr.materials.thermo.search(
                material_ids=material_ids,
                fields=["material_id", "thermo_type", "entries", "formation_energy_per_atom", "energy_above_hull", "is_stable"]
            )
            robocrys_docs = mpr.materials.robocrys.search_docs(
                material_ids=uncertain_ids,
                fields=["material_id", "description", "condensed_structure", "robocrys_version"]
            ) if uncertain_ids else []
    except Exception as exc:
        message = str(exc).replace(key, "[REDACTED]")
        audit_base.update({"status": "failed", "error_type": type(exc).__name__, "error_message": message})
        AUDIT_OUTPUT.write_text(json.dumps(audit_base, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"MX2 method/Robocrys probe failed: {type(exc).__name__}", file=sys.stderr)
        return 1

    task_map = {
        public(doc.task_id): {"run_type": public(doc.run_type), "task_type": public(doc.task_type)}
        for doc in task_docs
    }
    thermo_map: dict[str, list[dict]] = {mid: [] for mid in material_ids}
    for doc in thermo_docs:
        entries = []
        for entry_type, entry in (doc.entries or {}).items():
            entries.append({
                "entry_type": str(entry_type),
                "entry_id": public(getattr(entry, "entry_id", None)),
                "run_type": entry_run_type(entry)
            })
        thermo_map.setdefault(public(doc.material_id), []).append({
            "thermo_type": public(doc.thermo_type),
            "entries": entries,
            "formation_energy_per_atom": doc.formation_energy_per_atom,
            "energy_above_hull": doc.energy_above_hull,
            "is_stable": doc.is_stable
        })
    robocrys_map = {public(doc.material_id): doc for doc in robocrys_docs}
    records = []
    for material_id in material_ids:
        origins = summaries[material_id].get("origins", [])
        electronic_ids = [
            origin["task_id"] for origin in origins
            if origin.get("name") == "electronic_structure" and origin.get("task_id")
        ]
        band_methods = [
            {"task_id": task_id, **task_map.get(task_id, {"run_type": None, "task_type": None})}
            for task_id in electronic_ids
        ]
        thermo_evidence = thermo_map.get(material_id, [])
        dim = dim_map[material_id]
        robocrys = robocrys_map.get(material_id)
        robocrys_evidence = None
        if robocrys is not None:
            robocrys_dim = int(robocrys.condensed_structure.dimensionality)
            all_components_2d = bool(dim["component_dimensions"]) and all(value == 2 for value in dim["component_dimensions"])
            recommendation = (
                "recommended_confirmed_2d"
                if robocrys_dim == 2 and dim["larsen_crystalnn_dimensionality"] == 2 and all_components_2d
                else "remain_uncertain_2d"
            )
            robocrys_evidence = {
                "dimensionality": robocrys_dim,
                "version": robocrys.robocrys_version,
                "description": robocrys.description,
                "recommendation": recommendation
            }
        records.append({
            "material_id": material_id,
            "formula": dim["query_formula"],
            "band_gap_origin_methods": band_methods,
            "stability_thermo_methods": thermo_evidence,
            "band_gap_method_resolved": bool(band_methods) and all(item["run_type"] and item["task_type"] for item in band_methods),
            "stability_method_resolved": bool(thermo_evidence) and all(item["thermo_type"] and item["entries"] for item in thermo_evidence),
            "dimensionality_proposal": dim["proposed_dimensionality_status"],
            "robocrys_evidence": robocrys_evidence,
            "manual_review_required": True,
            "training_eligible": False
        })
    records.sort(key=lambda row: row["material_id"])
    payload = {
        "retrieved_at_utc": audit_base["attempted_at_utc"],
        "source_database": "Materials Project",
        "database_version": database_version,
        "credential_recorded": False,
        "method_paths": {
            "band_gap": "summary.origins[electronic_structure].task_id -> tasks.run_type/task_type",
            "stability": "thermo.thermo_type -> thermo.entries[*].parameters.run_type"
        },
        "records": records
    }
    LOCAL_OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    audit = {
        **payload,
        "status": "success",
        "materials_requested": len(material_ids),
        "electronic_task_ids_requested": len(electronic_task_ids),
        "task_documents_returned": len(task_docs),
        "thermo_documents_returned": len(thermo_docs),
        "robocrys_requested": len(uncertain_ids),
        "robocrys_returned": len(robocrys_docs),
        "band_gap_method_resolved_count": sum(row["band_gap_method_resolved"] for row in records),
        "stability_method_resolved_count": sum(row["stability_method_resolved"] for row in records),
        "robocrys_recommended_2d_count": sum(
            row["robocrys_evidence"] is not None and row["robocrys_evidence"]["recommendation"] == "recommended_confirmed_2d"
            for row in records
        ),
        "interpretation": "Method and Robocrys evidence collected; every record still requires recorded human review."
    }
    AUDIT_OUTPUT.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# MX2计算方法与Robocrys补充审核", "",
        "> 方法解析和Robocrys建议均不自动改变人工状态或训练资格。", "",
        "| MP ID | 公式 | Band Gap方法 | 稳定性方法 | 双算法建议 | Robocrys建议 | 人工结论 |",
        "|---|---|---|---|---|---|---|"
    ]
    for row in records:
        band = "; ".join(f"{item['run_type']}/{item['task_type']}" for item in row["band_gap_origin_methods"]) or "missing"
        thermo = "; ".join(item["thermo_type"] for item in row["stability_thermo_methods"]) or "missing"
        robo = row["robocrys_evidence"]["recommendation"] if row["robocrys_evidence"] else "not_requested"
        lines.append(f"| `{row['material_id']}` | {row['formula']} | {band} | {thermo} | {row['dimensionality_proposal']} | {robo} | pending |")
    lines += ["", "## 结果说明", "", (
        f"Band Gap方法链解析{audit['band_gap_method_resolved_count']}/{len(records)}条，稳定性方法链解析"
        f"{audit['stability_method_resolved_count']}/{len(records)}条；Robocrys返回{audit['robocrys_returned']}/"
        f"{audit['robocrys_requested']}条分歧记录，并建议其中{audit['robocrys_recommended_2d_count']}条可供人工确认2D。"
        "所有记录仍为pending，不自动训练。"
    ), ""]
    DOC_OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({
        "database_version": database_version,
        "band_gap_method_resolved_count": audit["band_gap_method_resolved_count"],
        "stability_method_resolved_count": audit["stability_method_resolved_count"],
        "robocrys_returned": audit["robocrys_returned"],
        "robocrys_recommended_2d_count": audit["robocrys_recommended_2d_count"]
    }, ensure_ascii=False, indent=2))
    return 0 if audit["robocrys_returned"] == audit["robocrys_requested"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
