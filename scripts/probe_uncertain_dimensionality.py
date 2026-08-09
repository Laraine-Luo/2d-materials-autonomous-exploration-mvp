#!/usr/bin/env python3
"""Fetch MP Robocrystallographer evidence for the uncertain 2D subset."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECRET_FILE = ROOT / ".local-secrets" / "materials_project.env"
DIM_AUDIT = ROOT / "artifacts" / "mos2_dimensionality_evidence_audit.json"
LOCAL_OUTPUT = ROOT / ".local-data" / "mos2_uncertain_robocrys.json"
AUDIT_OUTPUT = ROOT / "artifacts" / "mos2_uncertain_robocrys_audit.json"
DOC_OUTPUT = ROOT / "docs" / "mos2-uncertain-dimensionality-review.md"


def load_key() -> str:
    for line in SECRET_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("MP_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("MP_API_KEY missing from local ignored credential file")


def main() -> int:
    from mp_api.client import MPRester

    dim = json.loads(DIM_AUDIT.read_text(encoding="utf-8"))
    uncertain = {
        row["material_id"]: row for row in dim["records"]
        if row["proposed_dimensionality_status"] == "uncertain_2d"
    }
    with MPRester(load_key(), mute_progress_bars=True) as mpr:
        database_version = mpr.db_version
        docs = mpr.materials.robocrys.search_docs(
            material_ids=sorted(uncertain),
            fields=["material_id", "description", "condensed_structure", "robocrys_version"],
        )

    evidence = []
    for doc in docs:
        material_id = str(doc.material_id)
        prior = uncertain[material_id]
        robocrys_dim = int(doc.condensed_structure.dimensionality)
        components_all_2d = bool(prior["component_dimensions"]) and all(
            value == 2 for value in prior["component_dimensions"]
        )
        if robocrys_dim == 2 and prior["larsen_crystalnn_dimensionality"] == 2 and components_all_2d:
            recommendation = "recommended_confirmed_2d"
            rationale = "robocrys_and_larsen_support_2d; all_components_2d; gorai_disagrees"
        else:
            recommendation = "remain_uncertain_2d"
            rationale = "independent_evidence_not_sufficiently_consistent"
        evidence.append({
            "material_id": material_id,
            "robocrys_dimensionality": robocrys_dim,
            "robocrys_version": doc.robocrys_version,
            "description": doc.description,
            "larsen_dimensionality": prior["larsen_crystalnn_dimensionality"],
            "gorai_dimensionality": prior["gorai_dimensionality"],
            "component_dimensions": prior["component_dimensions"],
            "recommendation": recommendation,
            "rationale": rationale,
            "human_decision": "pending",
            "training_eligible": False,
        })
    evidence.sort(key=lambda row: row["material_id"])
    payload = {
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_database": "Materials Project",
        "database_version": database_version,
        "credential_recorded": False,
        "records_requested": len(uncertain),
        "records_returned": len(evidence),
        "records": evidence,
    }
    LOCAL_OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    audit = {
        **payload,
        "recommended_confirmed_2d_count": sum(
            row["recommendation"] == "recommended_confirmed_2d" for row in evidence
        ),
        "remain_uncertain_count": sum(row["recommendation"] == "remain_uncertain_2d" for row in evidence),
        "interpretation": (
            "Robocrystallographer is independent MP-generated review evidence. "
            "Recommendations do not change human decisions or training eligibility."
        ),
    }
    AUDIT_OUTPUT.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# MoS2不确定二维记录补充审核",
        "",
        "> 第三证据来自Materials Project Robocrystallographer；建议不等于人工签署。",
        "",
        "| MP ID | Larsen | Gorai | Robocrys | 分量 | 建议 | 人工结论 |",
        "|---|---:|---:|---:|---|---|---|",
    ]
    for row in evidence:
        lines.append(
            f"| `{row['material_id']}` | {row['larsen_dimensionality']} | {row['gorai_dimensionality']} | "
            f"{row['robocrys_dimensionality']} | {','.join(map(str, row['component_dimensions']))} | "
            f"{row['recommendation']} | pending |"
        )
    lines += [
        "",
        "## 结果说明",
        "",
        f"补充证据覆盖{len(evidence)}/{len(uncertain)}条不确定记录，其中"
        f"{audit['recommended_confirmed_2d_count']}条获得人工确认2D建议，"
        f"{audit['remain_uncertain_count']}条建议继续隔离。"
        "Gorai分歧被保留为算法失败模式，不从审计中删除。",
        "",
    ]
    DOC_OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(
        f"Robocrys evidence: {len(evidence)}/{len(uncertain)} returned; "
        f"{audit['recommended_confirmed_2d_count']} recommended 2D"
    )
    return 0 if len(evidence) == len(uncertain) else 1


if __name__ == "__main__":
    raise SystemExit(main())

