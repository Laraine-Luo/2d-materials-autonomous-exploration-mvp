#!/usr/bin/env python3
"""Render the repository-visible MP MX2 validation index."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "artifacts" / "mp_mx2_validation_index.csv"
AUDIT_PATH = ROOT / "artifacts" / "mp_mx2_validation_index_audit.json"
OUTPUT = ROOT / "docs" / "mp-mx2-validation-index-catalog.md"


def truth(value: str) -> bool:
    return value.strip().lower() == "true"


def main() -> int:
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    with CSV_PATH.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        formation = float(row["formation_energy_ev_atom"])
        hull = float(row["energy_above_hull_ev_atom"])
        row["combined_stability_prefilter"] = formation <= -0.2 and (hull <= 0.1 or truth(row["is_stable_mp_flag"]))

    validation = [row for row in rows if row["cohort_role"] == "independent_validation_candidate_source"]
    stable_validation = [row for row in validation if row["combined_stability_prefilter"]]
    stable_counts = Counter(row["query_formula"] for row in stable_validation)
    lines = [
        "# Materials Project MX2独立验证索引",
        "",
        f"> 数据库版本：{audit['database_version']}。本页是公式查询索引，不是二维材料合格清单。",
        "",
        "## 索引结论",
        "",
        f"- 六个公式族共{len(rows)}条唯一MP ID；",
        f"- MoS2开发／漂移对照：{sum(row['query_formula'] == 'MoS2' for row in rows)}条；",
        f"- 五个独立验证公式族：{len(validation)}条；",
        f"- 独立验证中通过组合稳定性预筛：{len(stable_validation)}条；",
        "- 预筛通过仍不代表二维性、计算方法一致性、训练资格或发现信号。",
        "",
        "| 公式 | 索引数 | 组合稳定性预筛通过 | 队列角色 |",
        "|---|---:|---:|---|",
    ]
    for formula in ("MoS2", "MoSe2", "MoTe2", "WS2", "WSe2", "WTe2"):
        subset = [row for row in rows if row["query_formula"] == formula]
        stable = sum(row["combined_stability_prefilter"] for row in subset)
        lines.append(f"| {formula} | {len(subset)} | {stable} | {subset[0]['cohort_role']} |")
    lines += [
        "",
        "## 逐MP ID索引",
        "",
        "| MP ID | 查询公式 | Band Gap/eV | Formation Energy/eV atom⁻¹ | E hull/eV atom⁻¹ | MP stable | 预筛 | 状态 |",
        "|---|---|---:|---:|---:|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['material_id']}` | {row['query_formula']} | {float(row['band_gap_ev']):.4f} | "
            f"{float(row['formation_energy_ev_atom']):.4f} | {float(row['energy_above_hull_ev_atom']):.4f} | "
            f"{row['is_stable_mp_flag']} | {'pass' if row['combined_stability_prefilter'] else 'fail'} | "
            "index-only / 2D unaudited |"
        )
    lines += [
        "",
        "## 下一道证据门",
        "",
        "仅对独立验证公式族中通过组合稳定性预筛的MP ID获取结构，随后执行逐记录二维性与计算方法审核。"
        "在新验证协议冻结前，不使用这些记录调整不确定性权重或比较策略。",
        "",
    ]
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Rendered {len(rows)} index rows; {len(stable_validation)} stable-prefilter validation candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
