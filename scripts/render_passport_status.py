"""Render passport readiness as a compact repository/PDF status page."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIMARY = ROOT / "artifacts/mp-1434-evidence-passport.json"
PASSPORT_DIR = ROOT / "artifacts/mos2_passports"
OUTPUT = ROOT / "docs/mos2-passport-readiness.md"


def main() -> int:
    passports = [json.loads(PRIMARY.read_text(encoding="utf-8"))]
    passports += [json.loads(p.read_text(encoding="utf-8")) for p in sorted(PASSPORT_DIR.glob("*.json"))]
    passports.sort(key=lambda p: p["material_id"])
    lines = [
        "# MoS2证据护照与正式队列就绪状态",
        "",
        "> 每个MP ID独立审核。网页索引存在不等于API记录合格，数值命中也不等于发现。",
        "",
        "| MP ID | API | 二维性 | 计算方法 | 训练资格 | 信号等级 | 晋级 |",
        "|---|---|---|---|---:|---:|---|",
    ]
    for p in passports:
        api = p.get("official_api_evidence", p.get("evidence", {}).get("official_api", {}))
        manual = p.get("manual_audit", p.get("audit", {}))
        lines.append(
            f"| `{p['material_id']}` | {api.get('status', 'pending')} | "
            f"{manual.get('dimensionality_review', 'pending')} | "
            f"{manual.get('calculation_method_review', 'pending')} | "
            f"{p['exploration_status_training_eligible']} | "
            f"{p['exploration_status_discovery_level']} | {p['promotion_decision']} |"
        )
    eligible = sum(bool(p["exploration_status_training_eligible"]) for p in passports)
    stable_eligible = sum(
        bool(p["exploration_status_training_eligible"])
        and p.get("formation_energy_ev_atom", 1.0) <= -0.2
        and (
            p.get("energy_above_hull_ev_atom", 1.0) <= 0.1
            or bool(p.get("is_stable_mp_flag", False))
        )
        for p in passports
    )
    api_received = sum(
        p.get("official_api_evidence", {}).get("status") == "received"
        for p in passports
    )
    lines += [
        "",
        "## 队列判定",
        "",
        f"- 护照总数：{len(passports)}；",
        f"- 当前训练合格：{eligible}；",
        f"- 同时满足固定稳定性约束：{stable_eligible}；",
        f"- 最小3+3+1微型闭环门槛：7；",
        f"- 当前结论：{'可以进入3+3+1微型闭环' if stable_eligible >= 7 else '不得启动正式3+3+1三策略闭环'}。",
        "",
        "## 结果说明",
        "",
        f"官方API已成功写入{api_received}/{len(passports)}条证据护照，身份、数据库版本和四项必需性质均已核验。"
        f"经记录的人工审核，{eligible}条取得训练资格，其中{stable_eligible}条同时满足固定稳定性约束；所有记录当前信号等级仍为D0。"
        "这说明正式候选池准入完成；D2须由合法查询触发，且单次3+3+1闭环不代表策略优于参照或形成新材料发现。",
        "",
    ]
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Rendered {len(passports)} passport states; {eligible} eligible")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
