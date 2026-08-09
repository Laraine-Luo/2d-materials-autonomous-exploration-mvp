#!/usr/bin/env python3
"""Apply the project owner's explicit continuation of the combined proposal."""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIMARY = ROOT / "artifacts" / "mp-1434-evidence-passport.json"
PASSPORT_DIR = ROOT / "artifacts" / "mos2_passports"
PROPOSAL = ROOT / "artifacts" / "formal_queue_review_proposal.json"
METHOD = ROOT / "artifacts" / "mos2_method_review_proposal.json"
AUDIT = ROOT / "artifacts" / "human_review_decision_audit.json"


def passport_paths() -> list[Path]:
    return [PRIMARY] + sorted(PASSPORT_DIR.glob("*.json"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--accept-proposal", action="store_true")
    args = parser.parse_args()
    if not args.accept_proposal:
        print("Blocked: --accept-proposal is required", file=sys.stderr)
        return 1

    sys.path.insert(0, str(ROOT / "src"))
    from materials_mvp.promotion import promotion_decision

    proposal = json.loads(PROPOSAL.read_text(encoding="utf-8"))
    methods = json.loads(METHOD.read_text(encoding="utf-8"))
    proposed = {row["material_id"]: row for row in proposal["records"]}
    method_by_id = {row["material_id"]: row for row in methods["records"]}
    reviewed_at = datetime.now(timezone.utc).isoformat()
    changes = []
    for path in passport_paths():
        passport = json.loads(path.read_text(encoding="utf-8"))
        material_id = passport["material_id"]
        decision = proposed[material_id]
        method = method_by_id[material_id]
        before = {
            "training_eligible": passport.get("exploration_status_training_eligible", False),
            "promotion_decision": passport.get("promotion_decision", "blocked"),
            "manual_audit": deepcopy(passport.get("manual_audit", {})),
        }
        dimensionality_review = (
            "confirmed_2d" if decision["dimensionality_proposal"] == "recommended_confirmed_2d"
            else "non_2d"
        )
        method_review = "pass" if method["recommendation"] == "recommended_pass" else "pending"
        manual = passport.setdefault("manual_audit", {})
        manual.update({
            "dimensionality_review": dimensionality_review,
            "dimensionality_evidence": [
                decision["dimensionality_basis"],
                "see artifacts/mos2_dimensionality_evidence_audit.json",
                "see artifacts/mos2_uncertain_robocrys_audit.json where applicable",
            ],
            "calculation_method_review": method_review,
            "calculation_method_evidence": {
                "band_gap_run_types": method["band_gap_run_types"],
                "band_gap_task_types": method["band_gap_task_types"],
                "matching_thermo_types": method["matching_thermo_types"],
                "frozen_stability_cohort": method["frozen_stability_cohort"],
            },
            "reviewer": "project_owner_user",
            "decision_source": "continued after explicit 9-in/3-out proposal in Codex task",
            "reviewed_at": reviewed_at,
            "rationale": (
                "Accepted combined MP-only dimensionality and method evidence proposal; "
                "non-2D and method-attention records remain retained as counterexamples."
            ),
        })
        if method_review == "pass":
            passport["source_calculation_method"] = (
                "band_gap:GGA; stability:GGA_GGA+U_R2SCAN"
            )
        api = passport.get("official_api_evidence", {})
        promotion_record = {
            **passport,
            "api_identity_match": api.get("identity_match"),
            "database_version_frozen": api.get("database_version_frozen"),
            "dimensionality_review": dimensionality_review,
            "calculation_method_review": method_review,
        }
        eligible, reasons = promotion_decision(promotion_record)
        passport["exploration_status_training_eligible"] = eligible
        passport["exploration_status_query_state"] = "unobserved" if eligible else "excluded"
        passport["exploration_status_manual_review_required"] = not eligible
        passport["promotion_decision"] = "promoted" if eligible else "blocked"
        passport["blocking_reasons"] = reasons
        path.write_text(json.dumps(passport, ensure_ascii=False, indent=2), encoding="utf-8")
        changes.append({
            "material_id": material_id,
            "before": before,
            "after": {
                "dimensionality_review": dimensionality_review,
                "calculation_method_review": method_review,
                "training_eligible": eligible,
                "promotion_decision": passport["promotion_decision"],
                "blocking_reasons": reasons,
            },
        })

    audit = {
        "reviewed_at_utc": reviewed_at,
        "reviewer": "project_owner_user",
        "decision_source": "continued after explicit 9-in/3-out proposal in Codex task",
        "decision": "accept_combined_proposal",
        "reversible": True,
        "records_reviewed": len(changes),
        "training_eligible_count": sum(c["after"]["training_eligible"] for c in changes),
        "records": changes,
        "interpretation": (
            "Human-review states were applied to evidence passports. API data, algorithm outputs and "
            "counterexamples were not overwritten."
        ),
    }
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Human review applied: {audit['training_eligible_count']}/{len(changes)} eligible")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

