"""Update public passport states only from an actual ignored mapped API file."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAPPED = ROOT / ".local-data/materials_project_mapped.json"
PRIMARY = ROOT / "artifacts/mp-1434-evidence-passport.json"
PASSPORT_DIR = ROOT / "artifacts/mos2_passports"
AUDIT = ROOT / "artifacts/passport_update_audit.json"


def main() -> int:
    event = {
        "attempted_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": ".local-data/materials_project_mapped.json (git-ignored)",
        "credential_recorded": False,
    }
    if not MAPPED.exists():
        event.update({
            "status": "blocked_no_mapped_api_records",
            "records_updated": 0,
            "interpretation": "No passports were changed and no web/synthetic substitute was used.",
        })
        AUDIT.write_text(json.dumps(event, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Passport update blocked: no mapped API records")
        return 1

    # Import only after the fail-closed source check, keeping this script simple to inspect.
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    from materials_mvp.passport import apply_api_record

    records = json.loads(MAPPED.read_text(encoding="utf-8"))
    by_id = {row["material_id"]: row for row in records}
    changes = []
    frozen_versions = {row.get("source_database_version") for row in records if row.get("source_database_version")}
    if len(frozen_versions) != 1:
        event.update({
            "status": "blocked_database_version_not_unique",
            "records_updated": 0,
            "observed_versions": sorted(str(v) for v in frozen_versions),
        })
        AUDIT.write_text(json.dumps(event, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Passport update blocked: database version is missing or not unique")
        return 1
    frozen_version = next(iter(frozen_versions))
    paths = [PRIMARY] + sorted(PASSPORT_DIR.glob("*.json"))
    for path in paths:
        passport = json.loads(path.read_text(encoding="utf-8"))
        record = by_id.get(passport["material_id"])
        if not record:
            continue
        updated, change = apply_api_record(passport, record, frozen_version)
        path.write_text(json.dumps(updated, ensure_ascii=False, indent=2), encoding="utf-8")
        changes.append(change)
    event.update({
        "status": "updated_pending_manual_review",
        "database_version": frozen_version,
        "records_updated": len(changes),
        "changes": changes,
        "interpretation": "API evidence was applied; human 2D/method review remains authoritative.",
    })
    AUDIT.write_text(json.dumps(event, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Updated {len(changes)} passport(s) from mapped API records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
