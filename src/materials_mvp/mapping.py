"""Materials Project-only canonical mapping and eligibility checks."""

from __future__ import annotations

import json
from pathlib import Path


def load_mapping_list(path: Path) -> list[dict]:
    mappings = json.loads(path.read_text(encoding="utf-8"))
    mapped_names = [item["mapped_name"] for item in mappings]
    if len(mapped_names) != len(set(mapped_names)):
        raise ValueError("Mapped names must be unique")
    return mappings


def map_materials_project_record(raw: dict, mappings: list[dict]) -> dict:
    """Map direct MP fields only; derived/audit fields are produced elsewhere."""
    canonical = {}
    for item in mappings:
        if item["group"] in {"derived_audit", "exploration_state"}:
            continue
        original = item["original_name"]
        if original in raw:
            canonical[item["mapped_name"]] = raw[original]
        elif item.get("required"):
            canonical[item["mapped_name"]] = None
    canonical["source_database"] = "Materials Project"
    return canonical


def scientific_pool_eligibility(record: dict, frozen_version: str, frozen_method: str) -> tuple[bool, list[str]]:
    """Strict gate for the scientific pool; test fixtures never pass this gate."""
    reasons = []
    if record.get("source_database") != "Materials Project":
        reasons.append("source_is_not_materials_project")
    if record.get("source_database_version") != frozen_version:
        reasons.append("database_version_mismatch_or_missing")
    if record.get("source_calculation_method") != frozen_method:
        reasons.append("calculation_method_mismatch_or_missing")
    if not record.get("material_id"):
        reasons.append("material_id_missing")
    if record.get("dimensionality_status") != "confirmed_2d":
        reasons.append("dimensionality_not_confirmed_2d")
    required_properties = (
        "band_gap_ev",
        "formation_energy_ev_atom",
        "energy_above_hull_ev_atom",
        "is_stable_mp_flag",
    )
    if any(record.get(name) is None for name in required_properties):
        reasons.append("required_property_missing")
    return not reasons, reasons
