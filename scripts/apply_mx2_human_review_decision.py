#!/usr/bin/env python3
"""Apply the project owner's signed MX2 review decision as an audit transaction."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from pymatgen.core import Structure

ROOT = Path(__file__).resolve().parents[1]
PROPOSAL = ROOT / "artifacts" / "mp_mx2_combined_review_proposal.json"
INDEX = ROOT / "artifacts" / "mp_mx2_validation_index.csv"
STRUCTURES = ROOT / ".local-data" / "mp_mx2_structure_response.json"
DIM = ROOT / "artifacts" / "mp_mx2_dimensionality_evidence_audit.json"
METHOD = ROOT / "artifacts" / "mp_mx2_method_robocrys_evidence_audit.json"
AUDIT = ROOT / "artifacts" / "mp_mx2_human_review_decision_audit.json"
PASSPORT_DIR = ROOT / "artifacts" / "mx2_validation_passports"
OBSERVATIONS = ROOT / "artifacts" / "mx2_validation_agent_observations.csv"
LOCAL_ORACLE = ROOT / ".local-data" / "mx2_validation_oracle.csv"
DOC = ROOT / "docs" / "mp-mx2-validation-readiness.md"

DECISION_TEXT = "批准24条建议，mp-1120746继续隔离。"
ACTOR = "project_owner_user"


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def main() -> int:
    existing_transaction = json.loads(AUDIT.read_text(encoding="utf-8")) if AUDIT.exists() else None
    if existing_transaction and existing_transaction.get("decision_text") != DECISION_TEXT:
        raise RuntimeError("A different human decision is already recorded; refusing to overwrite it")
    proposal = json.loads(PROPOSAL.read_text(encoding="utf-8"))
    structure_payload = json.loads(STRUCTURES.read_text(encoding="utf-8"))
    dimension_payload = json.loads(DIM.read_text(encoding="utf-8"))
    method_payload = json.loads(METHOD.read_text(encoding="utf-8"))
    with INDEX.open(encoding="utf-8", newline="") as handle:
        index = {row["material_id"]: row for row in csv.DictReader(handle)}
    structures = {row["material_id"]: row for row in structure_payload["records"]}
    dimensions = {row["material_id"]: row for row in dimension_payload["records"]}
    methods = {row["material_id"]: row for row in method_payload["records"]}
    approved = sorted(
        row["material_id"] for row in proposal["records"]
        if row["combined_recommendation"] == "recommend_training_eligibility_after_human_signature"
    )
    quarantined = sorted(
        row["material_id"] for row in proposal["records"]
        if row["combined_recommendation"] == "remain_quarantined"
    )
    if len(approved) != 24 or quarantined != ["mp-1120746"]:
        raise RuntimeError("Proposal no longer matches the signed 24+1 decision")

    PASSPORT_DIR.mkdir(parents=True, exist_ok=True)
    observations = []
    oracle_rows = []
    transitions = []
    for material_id in sorted(approved + quarantined):
        idx = index[material_id]
        structure = Structure.from_dict(structures[material_id]["structure"])
        abc = list(structure.lattice.abc)
        is_approved = material_id in approved
        passport = {
            "material_id": material_id,
            "formula": idx["query_formula"],
            "source_database": "Materials Project",
            "source_database_version": structure_payload["database_version"],
            "source_index_role": idx["cohort_role"],
            "formation_energy_ev_atom": float(idx["formation_energy_ev_atom"]),
            "energy_above_hull_ev_atom": float(idx["energy_above_hull_ev_atom"]),
            "is_stable_mp_flag": idx["is_stable_mp_flag"].lower() == "true",
            "band_gap_oracle_commitment_sha256": digest(f"{material_id}:{idx['band_gap_ev']}"),
            "dimensionality_evidence": dimensions[material_id],
            "method_evidence": methods[material_id],
            "human_review": {
                "actor": ACTOR,
                "decision_text": DECISION_TEXT,
                "decision_recorded_at_utc": None,
                "dimensionality_decision": "confirmed_2d",
                "method_decision": "pass" if is_approved else "attention_quarantine",
            },
            "exploration_status_validation_eligible": is_approved,
            "exploration_status_training_eligible": False,
            "exploration_status_label_access": "oracle_only",
            "exploration_status_discovery_level": "D0",
            "promotion_decision": "validation_candidate" if is_approved else "quarantined_method_attention",
        }
        observations.append({
            "material_id": material_id,
            "formula": idx["query_formula"],
            "n_sites": len(structure),
            "volume_per_atom_angstrom3": structure.volume / len(structure),
            "density_g_cm3": float(structure.density),
            "lattice_anisotropy": max(abc) / min(abc),
            "layer_component_count": len(dimensions[material_id]["component_dimensions"]),
            "formation_energy_ev_atom": float(idx["formation_energy_ev_atom"]),
            "energy_above_hull_ev_atom": float(idx["energy_above_hull_ev_atom"]),
            "is_stable_mp_flag": idx["is_stable_mp_flag"],
            "exploration_status_validation_eligible": is_approved,
            "exploration_status_label_access": "oracle_only",
        })
        oracle_rows.append({"material_id": material_id, "band_gap_ev": float(idx["band_gap_ev"])})
        transitions.append({
            "material_id": material_id,
            "before": {"human_decision": "pending", "validation_eligible": False, "training_eligible": False},
            "after": {
                "human_decision": "approved_validation_candidate" if is_approved else "method_attention_quarantine",
                "validation_eligible": is_approved,
                "training_eligible": False,
            },
            "reason": "signed_project_owner_decision"
        })
        passport["human_review"]["decision_recorded_at_utc"] = "__TRANSACTION_TIMESTAMP__"
        (PASSPORT_DIR / f"{material_id}.json").write_text(json.dumps(passport, ensure_ascii=False, indent=2), encoding="utf-8")

    recorded_at = (
        existing_transaction["recorded_at_utc"]
        if existing_transaction else datetime.now(timezone.utc).isoformat()
    )
    for path in PASSPORT_DIR.glob("*.json"):
        text = path.read_text(encoding="utf-8").replace("__TRANSACTION_TIMESTAMP__", recorded_at)
        path.write_text(text, encoding="utf-8")
    with OBSERVATIONS.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(observations[0]))
        writer.writeheader()
        writer.writerows(observations)
    LOCAL_ORACLE.parent.mkdir(parents=True, exist_ok=True)
    with LOCAL_ORACLE.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(oracle_rows[0]))
        writer.writeheader()
        writer.writerows(oracle_rows)
    transaction = {
        "recorded_at_utc": recorded_at,
        "actor": ACTOR,
        "authority": "project_owner_human_review",
        "decision_text": DECISION_TEXT,
        "source_proposal": "artifacts/mp_mx2_combined_review_proposal.json",
        "approved_validation_candidate_count": len(approved),
        "approved_material_ids": approved,
        "quarantined_material_ids": quarantined,
        "training_eligible_count": 0,
        "label_isolation": {
            "agent_observation_file": "artifacts/mx2_validation_agent_observations.csv",
            "oracle_file": ".local-data/mx2_validation_oracle.csv (git-ignored)",
            "forbidden_agent_columns": ["band_gap_ev"],
            "public_passport_label_storage": "sha256 commitment only"
        },
        "transitions": transitions,
        "interpretation": "Human approval grants validation-candidate status only; it does not permit training use or expose Band Gap through the agent observation interface."
    }
    AUDIT.write_text(json.dumps(transaction, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# MX2独立验证队列就绪状态", "",
        f"> 人工决定：{DECISION_TEXT}", "",
        f"- 已签署验证候选：{len(approved)}条；",
        "- 方法注意并继续隔离：1条（`mp-1120746`）；",
        "- 获准作为训练数据：0条；",
        "- Agent观察文件不含Band Gap，标签仅由环境oracle在查询后揭示；",
        "- 公开护照只保存Band Gap承诺哈希，不保存oracle数值。", "",
        "## 状态含义", "",
        "验证候选资格表示记录可以进入后续独立评价环境，不表示它已被Agent发现，也不允许其标签参与模型训练。"
        "下一步仍须在运行前冻结初始知识来源、预算、权重消融和评价门槛。", ""
    ]
    DOC.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({
        "approved_validation_candidate_count": len(approved),
        "quarantined_material_ids": quarantined,
        "training_eligible_count": 0,
        "agent_observation_columns": list(observations[0])
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
