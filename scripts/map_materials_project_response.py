"""Map an ignored raw MP response and publish only a safe schema audit."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / ".local-data" / "materials_project_probe.json"
MAPPING_PATH = ROOT / "config" / "materials_project_mapping_list.json"
LOCAL_CANONICAL = ROOT / ".local-data" / "materials_project_mapped.json"
AUDIT_PATH = ROOT / "artifacts" / "materials_project_mapping_audit.json"


def main() -> int:
    mapping = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))
    audit = {
        "attempted_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_database": "Materials Project",
        "mapping_path": "config/materials_project_mapping_list.json",
        "raw_response_path": ".local-data/materials_project_probe.json (git-ignored)",
        "canonical_output_path": ".local-data/materials_project_mapped.json (git-ignored)",
    }
    if not RAW_PATH.exists():
        audit.update({
            "status": "blocked_no_raw_response",
            "records_mapped": 0,
            "interpretation": "API acquisition has not succeeded; no placeholder records were substituted.",
        })
        AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Mapping blocked: no raw API response; audit written")
        return 1

    payload = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    rows = payload.get("data", [])
    database_version = payload.get("database_version")
    direct = [item for item in mapping if item["group"] not in {"derived_audit", "exploration_state"}]
    mapped_rows = []
    missing_counts = {item["mapped_name"]: 0 for item in direct}
    for raw in rows:
        mapped = {"source_database": "Materials Project"}
        for item in direct:
            original = item["original_name"]
            # Multi-endpoint provenance paths are audited separately.
            if " -> " in original:
                value = None
            elif original == "database_version":
                value = database_version
            else:
                value = raw.get(original)
            mapped[item["mapped_name"]] = value
            if value is None:
                missing_counts[item["mapped_name"]] += 1
        mapped.update({
            "dimensionality_status": "uncertain_2d",
            "exploration_status_training_eligible": False,
            "exploration_status_query_state": "manual_review",
            "exploration_status_discovery_level": "D0",
            "exploration_status_manual_review_required": True,
            "exploration_status_budget_position": 0,
        })
        mapped_rows.append(mapped)

    LOCAL_CANONICAL.write_text(json.dumps(mapped_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    audit.update({
        "status": "mapped_pending_audit",
        "records_mapped": len(mapped_rows),
        "missing_field_counts": missing_counts,
        "training_eligible_count": 0,
        "interpretation": "Direct fields were mapped; all records remain quarantined until 2D and method audits pass.",
    })
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Mapped {len(mapped_rows)} record(s); all remain in manual review")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
