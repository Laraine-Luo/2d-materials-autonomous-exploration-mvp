#!/usr/bin/env python3
"""Fetch structure and Summary origins for the frozen MX2 audit queue."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "config" / "mp_mx2_structure_audit_queue_v1.json"
SECRET = ROOT / ".local-secrets" / "materials_project.env"
LOCAL_OUTPUT = ROOT / ".local-data" / "mp_mx2_structure_response.json"
AUDIT_OUTPUT = ROOT / "artifacts" / "mp_mx2_structure_response_audit.json"


def load_env() -> None:
    for raw in SECRET.read_text(encoding="utf-8").splitlines():
        if "=" in raw and not raw.lstrip().startswith("#"):
            key, value = raw.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def serialize(document) -> dict:
    row = document.model_dump(mode="json")
    row["material_id"] = str(document.material_id)
    origins = []
    for origin in document.origins or []:
        item = origin.model_dump(mode="json") if hasattr(origin, "model_dump") else dict(origin)
        item["task_id"] = str(origin.task_id)
        origins.append(item)
    row["origins"] = origins
    return row


def main() -> int:
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    load_env()
    key = os.environ.get("MP_API_KEY")
    audit = {
        "attempted_at_utc": datetime.now(timezone.utc).isoformat(),
        "queue_id": queue["queue_id"],
        "source_database": "Materials Project",
        "requested_material_ids": queue["material_ids"],
        "requested_count": queue["record_count"],
        "requested_fields": queue["requested_summary_fields"],
        "credential_recorded": False,
        "status": "attempted"
    }
    try:
        from mp_api.client import MPRester

        with MPRester(key, mute_progress_bars=True) as mpr:
            documents = mpr.materials.summary.search(
                material_ids=queue["material_ids"],
                fields=queue["requested_summary_fields"]
            )
            db_version = mpr.db_version
        records = [serialize(document) for document in documents]
    except Exception as exc:
        message = str(exc).replace(key, "[REDACTED]") if key else str(exc)
        audit.update({"status": "failed", "records_returned": 0, "error_type": type(exc).__name__, "error_message": message})
        AUDIT_OUTPUT.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"MX2 structure probe failed: {type(exc).__name__}", file=sys.stderr)
        return 1
    requested = sorted(queue["material_ids"])
    returned = sorted(row["material_id"] for row in records)
    exact = requested == returned
    audit.update({
        "status": "success" if exact else "failed_identity_mismatch",
        "database_version": db_version,
        "records_returned": len(records),
        "returned_material_ids": returned,
        "identity_exact_match": exact,
        "structures_returned": sum(bool(row.get("structure")) for row in records),
        "origins_returned": sum(bool(row.get("origins")) for row in records),
        "raw_response_location": ".local-data/mp_mx2_structure_response.json (git-ignored)" if exact else None,
        "interpretation": "Structure and origin evidence only; no record is automatically approved."
    })
    AUDIT_OUTPUT.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    if not exact:
        print("MX2 structure response identity mismatch; local mapping blocked", file=sys.stderr)
        return 1
    LOCAL_OUTPUT.write_text(json.dumps({
        "retrieved_at_utc": audit["attempted_at_utc"],
        "database_version": db_version,
        "requested_material_ids": requested,
        "records": records
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
