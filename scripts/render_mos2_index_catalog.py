"""Render the MP MoS2 web-index CSV as a repository-facing Markdown catalog."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "materials_project_manual_probe" / "mos2_formula_index_12.csv"
OUTPUT = ROOT / "docs" / "mos2-materials-project-index-catalog.md"


def main() -> int:
    with SOURCE.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    lines = [
        "# MoS2在Materials Project中的索引清单",
        "",
        "> 自动生成自`data/materials_project_manual_probe/mos2_formula_index_12.csv`。这是Materials Explorer网页索引证据，不是API响应或正式训练集。",
        "",
        "索引路径：`Materials Explorer → Mo–S → MoS2 → mp-id`。`MoS2`位于化学式/组成层，具体候选身份由MP ID确定。网页核验数据库版本为`v2026.04.13`。",
        "",
        "| MP ID | 晶系 | 空间群 | Sites | 网页E_hull (eV/atom) | 网页Band Gap (eV) | 当前资格 |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['material_id']}` | {row['crystal_system']} | {row['space_group']} | "
            f"{row['sites']} | {row['web_energy_above_hull_ev_atom']} | {row['web_band_gap_ev']} | "
            "隔离，待API/二维性/方法审核 |"
        )
    target_hits = sum(1 for row in rows if 1.5 <= float(row["web_band_gap_ev"]) <= 2.5)
    zero_gap = sum(1 for row in rows if float(row["web_band_gap_ev"]) == 0)
    hull_over = sum(
        1 for row in rows
        if not row["web_energy_above_hull_ev_atom"].startswith("<")
        and float(row["web_energy_above_hull_ev_atom"]) > 0.1
    )
    lines += [
        "",
        "## 网页索引层描述统计",
        "",
        f"- 结构记录数：{len(rows)}；",
        f"- 网页Band Gap落入MVP目标区间1.5–2.5 eV：{target_hits}条；",
        f"- 网页Band Gap为0 eV：{zero_gap}条；",
        f"- 网页Energy Above Hull明确高于0.1 eV/atom：{hull_over}条。",
        "",
        "这些统计只能用于说明首队列包含不同结构和性质结果。Formation Energy、`is_stable`、二维性和计算方法尚不完整，因此不能据此产生D1/D2、训练模型或比较策略。正式结果以官方API响应和审核队列为准。",
        "",
        "## 与仓库其他证据的关系",
        "",
        "- 原始索引清单：`data/materials_project_manual_probe/mos2_formula_index_12.csv`；",
        "- 逐记录审核状态：`artifacts/mos2_record_audit_queue.csv`；",
        "- 索引层级定义：`docs/materials-project-index-hierarchy.md`；",
        "- 正式队列配置：`config/first_formal_queue.json`；",
        "- 晋级门控：`config/formal_record_promotion_rules.json`。",
        "",
    ]
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Rendered {len(rows)} records to docs/mos2-materials-project-index-catalog.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
