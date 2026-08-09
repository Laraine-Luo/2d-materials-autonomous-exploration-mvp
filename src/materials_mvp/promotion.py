"""Fail-closed promotion from manual review to the formal MP candidate pool."""

from __future__ import annotations


def promotion_decision(record: dict) -> tuple[bool, list[str]]:
    reasons = []
    if record.get("source_database") != "Materials Project":
        reasons.append("source_database_not_materials_project")
    if record.get("source_surface") != "official API":
        reasons.append("source_surface_not_official_api")
    if record.get("api_identity_match") != "pass":
        reasons.append("api_identity_not_verified")
    if record.get("database_version_frozen") != "pass":
        reasons.append("database_version_not_frozen")
    if record.get("dimensionality_review") != "confirmed_2d":
        reasons.append("dimensionality_not_confirmed")
    if record.get("calculation_method_review") != "pass":
        reasons.append("calculation_method_not_verified")
    required = (
        "material_id", "formula", "chemical_system", "structure",
        "band_gap_ev", "formation_energy_ev_atom",
        "energy_above_hull_ev_atom", "is_stable_mp_flag",
    )
    if any(record.get(name) in (None, "") for name in required):
        reasons.append("required_fields_missing")
    return not reasons, reasons
