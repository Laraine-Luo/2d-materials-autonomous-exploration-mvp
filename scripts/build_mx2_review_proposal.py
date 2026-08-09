#!/usr/bin/env python3
"""Build a non-binding combined human-review proposal for MX2 records."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIM = ROOT / "artifacts" / "mp_mx2_dimensionality_evidence_audit.json"
METHOD = ROOT / "artifacts" / "mp_mx2_method_robocrys_evidence_audit.json"
OUTPUT = ROOT / "artifacts" / "mp_mx2_combined_review_proposal.json"
DOC = ROOT / "docs" / "mp-mx2-combined-review-proposal.md"


def main() -> int:
    dim = json.loads(DIM.read_text(encoding="utf-8"))
    method = json.loads(METHOD.read_text(encoding="utf-8"))
    dim_map = {row["material_id"]: row for row in dim["records"]}
    records = []
    for row in method["records"]:
        dimension = dim_map[row["material_id"]]
        if dimension["proposed_dimensionality_status"] == "confirmed_2d":
            dim_recommendation = "recommend_confirmed_2d"
            dim_basis = "larsen_gorai_consensus"
        elif (
            row["robocrys_evidence"] is not None
            and row["robocrys_evidence"]["recommendation"] == "recommended_confirmed_2d"
        ):
            dim_recommendation = "recommend_confirmed_2d"
            dim_basis = "larsen_all_components_and_robocrys_support_2d; gorai_disagrees"
        else:
            dim_recommendation = "remain_uncertain_2d"
            dim_basis = "evidence_not_sufficiently_consistent"
        band_combos = {
            (item["run_type"], item["task_type"])
            for item in row["band_gap_origin_methods"]
        }
        method_recommendation = (
            "recommend_method_pass"
            if band_combos == {("GGA", "NSCF Line")} and row["stability_method_resolved"]
            else "method_attention_required"
        )
        records.append({
            "material_id": row["material_id"],
            "formula": row["formula"],
            "dimensionality_recommendation": dim_recommendation,
            "dimensionality_basis": dim_basis,
            "gorai_disagreement_retained": dimension["gorai_dimensionality"] != dimension["larsen_crystalnn_dimensionality"],
            "band_gap_method_combinations": [f"{a}/{b}" for a, b in sorted(band_combos)],
            "stability_method_resolved": row["stability_method_resolved"],
            "method_recommendation": method_recommendation,
            "combined_recommendation": (
                "recommend_training_eligibility_after_human_signature"
                if dim_recommendation == "recommend_confirmed_2d" and method_recommendation == "recommend_method_pass"
                else "remain_quarantined"
            ),
            "human_decision": "pending",
            "training_eligible": False
        })
    records.sort(key=lambda row: row["material_id"])
    proposal = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_database": "Materials Project",
        "database_version": method["database_version"],
        "automatic_approval": False,
        "proposal_only": True,
        "records_reviewed": len(records),
        "recommended_confirmed_2d_count": sum(row["dimensionality_recommendation"] == "recommend_confirmed_2d" for row in records),
        "recommended_method_pass_count": sum(row["method_recommendation"] == "recommend_method_pass" for row in records),
        "method_attention_count": sum(row["method_recommendation"] == "method_attention_required" for row in records),
        "recommended_training_after_signature_count": sum(row["combined_recommendation"] == "recommend_training_eligibility_after_human_signature" for row in records),
        "records": records,
        "interpretation": "Recommendations are non-binding. No exploration status changes until a human-signed decision is recorded."
    }
    OUTPUT.write_text(json.dumps(proposal, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# MX2联合人工审核建议", "",
        "> 本页只提供建议；未签署前25条记录全部保持隔离。", "",
        "| MP ID | 公式 | 二维性建议 | 方法建议 | 联合建议 | 人工结论 |",
        "|---|---|---|---|---|---|"
    ]
    for row in records:
        lines.append(
            f"| `{row['material_id']}` | {row['formula']} | {row['dimensionality_recommendation']} | "
            f"{row['method_recommendation']} | {row['combined_recommendation']} | pending |"
        )
    lines += ["", "## 结果说明", "", (
        f"25条记录均获得确认2D建议；其中{proposal['recommended_method_pass_count']}条方法一致，"
        f"{proposal['method_attention_count']}条为方法注意项。建议在人工作出统一签署后，最多"
        f"{proposal['recommended_training_after_signature_count']}条进入验证候选池。Gorai分歧仍保留为算法失败证据。"
    ), ""]
    DOC.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({k: proposal[k] for k in (
        "records_reviewed", "recommended_confirmed_2d_count", "recommended_method_pass_count",
        "method_attention_count", "recommended_training_after_signature_count"
    )}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
