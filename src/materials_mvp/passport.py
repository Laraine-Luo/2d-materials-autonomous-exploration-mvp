"""Evidence-passport updates and auditable before/after diffs."""

from __future__ import annotations

from copy import deepcopy

from .promotion import promotion_decision


def apply_api_record(passport: dict, record: dict, frozen_version: str) -> tuple[dict, dict]:
    """Apply an actual mapped MP API record without auto-approving human audits."""
    updated = deepcopy(passport)
    before = {
        "training_eligible": passport.get("exploration_status_training_eligible"),
        "discovery_level": passport.get("exploration_status_discovery_level"),
        "promotion_decision": passport.get("promotion_decision"),
    }
    identity_match = record.get("material_id") == passport.get("material_id")
    version_match = record.get("source_database_version") == frozen_version
    api = updated.setdefault("official_api_evidence", {})
    api.update({
        "status": "received",
        "identity_match": "pass" if identity_match else "fail",
        "database_version_frozen": "pass" if version_match else "fail",
        "origins_task_id": record.get("origins_task_id"),
        "thermo_run_type": record.get("source_calculation_method"),
        "required_properties_verified": all(
            record.get(name) is not None
            for name in (
                "band_gap_ev", "formation_energy_ev_atom",
                "energy_above_hull_ev_atom", "is_stable_mp_flag",
            )
        ),
    })
    updated["source_surface"] = "official API"
    updated["source_database_version"] = record.get("source_database_version")
    for name in (
        "structure", "band_gap_ev", "formation_energy_ev_atom",
        "energy_above_hull_ev_atom", "is_stable_mp_flag",
        "source_calculation_method",
    ):
        updated[name] = record.get(name)

    manual = updated.get("manual_audit", {})
    promotion_record = {
        **updated,
        "api_identity_match": api["identity_match"],
        "database_version_frozen": api["database_version_frozen"],
        "dimensionality_review": manual.get("dimensionality_review", "pending"),
        "calculation_method_review": manual.get("calculation_method_review", "pending"),
    }
    passed, reasons = promotion_decision(promotion_record)
    updated["exploration_status_training_eligible"] = passed
    updated["exploration_status_query_state"] = "unobserved" if passed else "manual_review"
    updated["exploration_status_manual_review_required"] = not passed
    updated["promotion_decision"] = "promoted" if passed else "blocked"
    updated["blocking_reasons"] = reasons
    after = {
        "training_eligible": updated["exploration_status_training_eligible"],
        "discovery_level": updated["exploration_status_discovery_level"],
        "promotion_decision": updated["promotion_decision"],
    }
    return updated, {"material_id": updated["material_id"], "before": before, "after": after, "blocking_reasons": reasons}
