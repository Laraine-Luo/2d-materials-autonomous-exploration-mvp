#!/usr/bin/env python3
"""Combine dimensionality and method proposals without signing human decisions."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIM = ROOT / "artifacts" / "mos2_dimensionality_evidence_audit.json"
ROBO = ROOT / "artifacts" / "mos2_uncertain_robocrys_audit.json"
METHOD = ROOT / "artifacts" / "mos2_method_review_proposal.json"
OUTPUT_JSON = ROOT / "artifacts" / "formal_queue_review_proposal.json"
OUTPUT_MD = ROOT / "docs" / "formal-queue-combined-review.md"


def main() -> int:
    dim = json.loads(DIM.read_text(encoding="utf-8"))
    robo = json.loads(ROBO.read_text(encoding="utf-8"))
    method = json.loads(METHOD.read_text(encoding="utf-8"))
    robo_by_id = {row["material_id"]: row for row in robo["records"]}
    method_by_id = {row["material_id"]: row for row in method["records"]}
    records = []
    for row in dim["records"]:
        material_id = row["material_id"]
        if row["proposed_dimensionality_status"] == "confirmed_2d":
            dimensionality_proposal = "recommended_confirmed_2d"
            dimensionality_basis = "larsen_gorai_consensus"
        elif material_id in robo_by_id and robo_by_id[material_id]["recommendation"] == "recommended_confirmed_2d":
            dimensionality_proposal = "recommended_confirmed_2d"
            dimensionality_basis = "larsen_robocrys_support; gorai_failure_retained"
        else:
            dimensionality_proposal = row["proposed_dimensionality_status"]
            dimensionality_basis = row["proposal_reason"]
        method_proposal = method_by_id[material_id]["recommendation"]
        proposed_eligible = (
            dimensionality_proposal == "recommended_confirmed_2d"
            and method_proposal == "recommended_pass"
        )
        records.append({
            "material_id": material_id,
            "dimensionality_proposal": dimensionality_proposal,
            "dimensionality_basis": dimensionality_basis,
            "method_proposal": method_proposal,
            "proposed_training_eligible": proposed_eligible,
            "human_dimensionality_decision": "pending",
            "human_method_decision": "pending",
            "final_training_eligible": False,
        })
    proposed_count = sum(row["proposed_training_eligible"] for row in records)
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "database_version": dim["database_version"],
        "automatic_approval": False,
        "formal_loop_minimum": 8,
        "proposed_eligible_count": proposed_count,
        "signed_eligible_count": 0,
        "proposal_reaches_minimum": proposed_count >= 8,
        "formal_loop_ready": False,
        "records": records,
        "interpretation": (
            "The evidence proposal reaches the numerical minimum, but the formal loop remains blocked "
            "until human dimensionality and method decisions are recorded."
        ),
    }
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 首个正式MoS2队列：合并人工审核表",
        "",
        "> 自动证据建议达到门槛，不等于正式队列已经获批。人工二维性与方法结论仍需签署。",
        "",
        "| MP ID | 二维性建议 | 方法建议 | 建议入队 | 人工二维性 | 人工方法 | 最终资格 |",
        "|---|---|---|---:|---|---|---:|",
    ]
    for row in records:
        lines.append(
            f"| `{row['material_id']}` | {row['dimensionality_proposal']} | {row['method_proposal']} | "
            f"{row['proposed_training_eligible']} | pending | pending | False |"
        )
    lines += [
        "",
        "## 队列判定",
        "",
        f"- 自动证据建议入队：{proposed_count}条；",
        "- 人工签署入队：0条；",
        "- 正式闭环最低门槛：8条；",
        "- 当前结论：建议数量达到门槛，但正式闭环仍被人工审核闸门阻断。",
        "",
        "## 结果说明",
        "",
        "合并证据建议9条记录进入正式微型队列，3条作为非二维/方法异常反例保留。"
        "其中三条多层结构记录保留Gorai=1的失败证据，不以最终建议覆盖原始异常。"
        "在人工结论签署前，所有记录的最终训练资格仍为False。",
        "",
    ]
    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Combined proposal: {proposed_count} eligible suggestions; 0 signed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

