#!/usr/bin/env python3
"""Generate two-algorithm dimensionality evidence for the frozen MX2 queue."""

from __future__ import annotations

import csv
import json
import warnings
from datetime import datetime, timezone
from pathlib import Path

from pymatgen.analysis.dimensionality import get_dimensionality_gorai, get_dimensionality_larsen, get_structure_components
from pymatgen.analysis.local_env import CrystalNN
from pymatgen.core import Structure

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / ".local-data" / "mp_mx2_structure_response.json"
INDEX = ROOT / "artifacts" / "mp_mx2_validation_index.csv"
AUDIT = ROOT / "artifacts" / "mp_mx2_dimensionality_evidence_audit.json"
DOC = ROOT / "docs" / "mp-mx2-dimensionality-review.md"


def suggestion(larsen: int, gorai: int) -> tuple[str, str]:
    if larsen == 2 and gorai == 2:
        return "confirmed_2d", "two_algorithm_consensus"
    if larsen == 2 or gorai == 2:
        return "uncertain_2d", "algorithm_disagreement"
    return "non_2d", "two_algorithm_non_2d"


def main() -> int:
    payload = json.loads(RAW.read_text(encoding="utf-8"))
    with INDEX.open(encoding="utf-8", newline="") as handle:
        formulas = {row["material_id"]: row["query_formula"] for row in csv.DictReader(handle)}
    records = []
    for row in payload["records"]:
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
            "query_formula": formulas[row["material_id"]],
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
    records.sort(key=lambda row: row["material_id"])
    audit = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_database": "Materials Project",
        "database_version": payload["database_version"],
        "credential_recorded": False,
        "algorithms": {
            "larsen": "CrystalNN bonded graph + get_dimensionality_larsen",
            "gorai": "get_dimensionality_gorai with library defaults"
        },
        "automatic_approval": False,
        "records_analyzed": len(records),
        "confirmed_2d_proposal_count": sum(r["proposed_dimensionality_status"] == "confirmed_2d" for r in records),
        "uncertain_2d_proposal_count": sum(r["proposed_dimensionality_status"] == "uncertain_2d" for r in records),
        "non_2d_proposal_count": sum(r["proposed_dimensionality_status"] == "non_2d" for r in records),
        "records": records,
        "interpretation": "Algorithmic evidence only; every human decision remains pending and no record is training eligible."
    }
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# MX2独立验证候选二维性审核表", "",
        "> Larsen/CrystalNN与Gorai只生成审核建议；人工结论pending时不得训练。", "",
        "| MP ID | 公式 | Larsen | Gorai | 分量 | 建议 | 人工结论 |",
        "|---|---|---:|---:|---|---|---|"
    ]
    for row in records:
        lines.append(
            f"| `{row['material_id']}` | {row['query_formula']} | {row['larsen_crystalnn_dimensionality']} | "
            f"{row['gorai_dimensionality']} | {','.join(map(str, row['component_dimensions']))} | "
            f"{row['proposed_dimensionality_status']} | pending |"
        )
    lines += ["", "## 结果说明", "", (
        f"25条稳定性预筛候选中，双算法一致建议2D {audit['confirmed_2d_proposal_count']}条，"
        f"算法分歧 {audit['uncertain_2d_proposal_count']}条，双算法不支持2D {audit['non_2d_proposal_count']}条。"
        "分歧和非2D记录保留在审核与偏离统计中，不自动删除或晋级。"
    ), ""]
    DOC.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({k: audit[k] for k in ("records_analyzed", "confirmed_2d_proposal_count", "uncertain_2d_proposal_count", "non_2d_proposal_count")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
