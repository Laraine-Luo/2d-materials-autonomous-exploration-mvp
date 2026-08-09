#!/usr/bin/env python3
"""Render a human-review proposal from collected MP method evidence."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METHOD_AUDIT = ROOT / "artifacts" / "mos2_method_evidence_audit.json"
SUMMARY_RAW = ROOT / ".local-data" / "materials_project_probe.json"
PROPOSAL = ROOT / "artifacts" / "mos2_method_review_proposal.json"
OUTPUT = ROOT / "docs" / "mos2-method-review.md"


def same_number(a, b) -> bool:
    return a is not None and b is not None and abs(float(a) - float(b)) < 1e-10


def main() -> int:
    evidence = json.loads(METHOD_AUDIT.read_text(encoding="utf-8"))
    summaries = json.loads(SUMMARY_RAW.read_text(encoding="utf-8"))["data"]
    summary_by_id = {row["material_id"]: row for row in summaries}
    rows = []
    for record in evidence["records"]:
        material_id = record["material_id"]
        summary = summary_by_id[material_id]
        band_gap_run_types = sorted({
            item["run_type"] for item in record["band_gap_origin_methods"] if item["run_type"]
        })
        band_gap_task_types = sorted({
            item["task_type"] for item in record["band_gap_origin_methods"] if item["task_type"]
        })
        matching_thermo = []
        for thermo in record["stability_thermo_methods"]:
            if (
                same_number(thermo["formation_energy_per_atom"], summary["formation_energy_per_atom"])
                and same_number(thermo["energy_above_hull"], summary["energy_above_hull"])
                and thermo["is_stable"] == summary["is_stable"]
            ):
                matching_thermo.append(thermo["thermo_type"])
        frozen_thermo_match = "GGA_GGA+U_R2SCAN" in matching_thermo
        attention = band_gap_task_types != ["NSCF Line"]
        recommendation = (
            "attention_required" if attention else
            "recommended_pass" if band_gap_run_types == ["GGA"] and frozen_thermo_match else
            "recommended_fail"
        )
        rows.append({
            "material_id": material_id,
            "band_gap_run_types": band_gap_run_types,
            "band_gap_task_types": band_gap_task_types,
            "matching_thermo_types": matching_thermo,
            "frozen_stability_cohort": "GGA_GGA+U_R2SCAN",
            "summary_stability_matches_frozen_cohort": frozen_thermo_match,
            "recommendation": recommendation,
            "human_decision": "pending",
        })

    proposal = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "database_version": evidence["database_version"],
        "frozen_method_cohort": {
            "band_gap_run_type": "GGA",
            "stability_thermo_type": "GGA_GGA+U_R2SCAN",
            "band_gap_task_type_policy": "NSCF Line is normal; other task types require individual attention",
        },
        "automatic_approval": False,
        "recommended_pass_count": sum(r["recommendation"] == "recommended_pass" for r in rows),
        "attention_required_count": sum(r["recommendation"] == "attention_required" for r in rows),
        "recommended_fail_count": sum(r["recommendation"] == "recommended_fail" for r in rows),
        "records": rows,
        "interpretation": "This is a review proposal, not a signed human decision or training promotion.",
    }
    PROPOSAL.write_text(json.dumps(proposal, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# MoS2计算方法一致性人工审核表",
        "",
        f"> 数据库版本：`{evidence['database_version']}`。本表是审核建议，不自动批准训练资格。",
        "",
        "冻结口径：Band Gap 使用 GGA 来源；稳定性使用与 Summary 数值一致的 `GGA_GGA+U_R2SCAN` 热力学方案。",
        "",
        "| MP ID | Band Gap run/task | 稳定性方案匹配 | 建议 | 人工结论 |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        bg = f"{','.join(row['band_gap_run_types'])} / {','.join(row['band_gap_task_types'])}"
        match = "是" if row["summary_stability_matches_frozen_cohort"] else "否"
        lines.append(
            f"| `{row['material_id']}` | {bg} | {match} | {row['recommendation']} | pending |"
        )
    lines += [
        "",
        "## 结果说明",
        "",
        f"方法证据已覆盖12条记录；{proposal['recommended_pass_count']}条建议通过，"
        f"{proposal['attention_required_count']}条需重点复核，{proposal['recommended_fail_count']}条建议不通过。"
        "该结果只说明来源链可追踪且形成统一评价口径，不代表二维性、目标性质或材料发现已经通过。",
        "",
    ]
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(
        f"Method review proposal: {proposal['recommended_pass_count']} pass, "
        f"{proposal['attention_required_count']} attention, {proposal['recommended_fail_count']} fail"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

