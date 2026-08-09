#!/usr/bin/env python3
"""Generate two-algorithm dimensionality evidence; never auto-approve records."""

from __future__ import annotations

import json
import warnings
from datetime import datetime, timezone
from pathlib import Path

from pymatgen.analysis.dimensionality import (
    get_dimensionality_gorai,
    get_dimensionality_larsen,
    get_structure_components,
)
from pymatgen.analysis.local_env import CrystalNN
from pymatgen.core import Structure

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / ".local-data" / "materials_project_probe.json"
AUDIT = ROOT / "artifacts" / "mos2_dimensionality_evidence_audit.json"
OUTPUT = ROOT / "docs" / "mos2-dimensionality-review.md"


def suggestion(larsen: int, gorai: int) -> tuple[str, str]:
    if larsen == 2 and gorai == 2:
        return "confirmed_2d", "two_algorithm_consensus"
    if larsen == 2 or gorai == 2:
        return "uncertain_2d", "algorithm_disagreement"
    return "non_2d", "two_algorithm_non_2d"


def main() -> int:
    payload = json.loads(RAW.read_text(encoding="utf-8"))
    records = []
    for row in payload["data"]:
        structure = Structure.from_dict(row["structure"])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            bonded = CrystalNN().get_bonded_structure(structure)
            larsen = int(get_dimensionality_larsen(bonded))
            gorai = int(get_dimensionality_gorai(structure))
            components = list(get_structure_components(bonded, inc_orientation=True))
        proposed, reason = suggestion(larsen, gorai)
        records.append({
            "material_id": row["material_id"],
            "larsen_crystalnn_dimensionality": larsen,
            "gorai_dimensionality": gorai,
            "component_dimensions": [int(item["dimensionality"]) for item in components],
            "component_orientations": [
                [int(x) for x in item["orientation"]] if item.get("orientation") is not None else None
                for item in components
            ],
            "lattice_abc_angstrom": [float(x) for x in structure.lattice.abc],
            "proposed_dimensionality_status": proposed,
            "proposal_reason": reason,
            "human_decision": "pending",
            "training_eligible": False,
        })

    audit = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_database": "Materials Project",
        "database_version": payload.get("database_version"),
        "credential_recorded": False,
        "algorithms": {
            "larsen": "CrystalNN bonded graph + get_dimensionality_larsen",
            "gorai": "get_dimensionality_gorai with library defaults",
        },
        "automatic_approval": False,
        "confirmed_2d_proposal_count": sum(r["proposed_dimensionality_status"] == "confirmed_2d" for r in records),
        "uncertain_2d_proposal_count": sum(r["proposed_dimensionality_status"] == "uncertain_2d" for r in records),
        "non_2d_proposal_count": sum(r["proposed_dimensionality_status"] == "non_2d" for r in records),
        "formal_loop_minimum": 8,
        "records": records,
        "interpretation": (
            "Algorithmic dimensionality is review evidence only. Uncertain records remain visible in "
            "audit/deviation statistics and are excluded from training until human confirmation."
        ),
    }
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# MoS2二维性人工审核表",
        "",
        "> Larsen/CrystalNN 与 Gorai 双算法只提供审核建议；人工结论为 pending 时，一律不得进入训练。",
        "",
        "| MP ID | Larsen | Gorai | 结构分量 | 建议状态 | 原因 | 人工结论 |",
        "|---|---:|---:|---|---|---|---|",
    ]
    for row in records:
        components = ",".join(map(str, row["component_dimensions"]))
        lines.append(
            f"| `{row['material_id']}` | {row['larsen_crystalnn_dimensionality']} | "
            f"{row['gorai_dimensionality']} | {components} | "
            f"{row['proposed_dimensionality_status']} | {row['proposal_reason']} | pending |"
        )
    lines += [
        "",
        "## 队列影响",
        "",
        f"- 双算法一致支持2D：{audit['confirmed_2d_proposal_count']}条；",
        f"- 算法分歧、不确定：{audit['uncertain_2d_proposal_count']}条；",
        f"- 双算法不支持2D：{audit['non_2d_proposal_count']}条；",
        f"- 正式闭环最低门槛：{audit['formal_loop_minimum']}条；",
        "- 当前自动证据不足以启动正式闭环。",
        "",
        "## 结果说明",
        "",
        "双算法将候选分成一致2D、算法分歧和非2D三类。分歧记录继续出现在审核和偏离统计中，但未经人工确认不进入训练。"
        "该结果说明二维性闸门能够发现公式级MoS2候选池中的结构差异；不代表6条建议记录已完成人工确认。",
        "",
    ]
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(
        f"Dimensionality proposals: {audit['confirmed_2d_proposal_count']} confirmed, "
        f"{audit['uncertain_2d_proposal_count']} uncertain, {audit['non_2d_proposal_count']} non-2D"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

