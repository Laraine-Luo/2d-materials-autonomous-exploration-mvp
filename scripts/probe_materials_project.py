"""Small Materials Project connectivity/schema probe; never prints the API key."""

from __future__ import annotations

import json
import csv
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECRET_FILE = ROOT / ".local-secrets" / "materials_project.env"
OUTPUT_DIR = ROOT / ".local-data"
AUDIT_DIR = ROOT / "artifacts"
BASE_URL = "https://api.materialsproject.org"
INDEX_FILE = ROOT / "data" / "materials_project_manual_probe" / "mos2_formula_index_12.csv"


def load_local_env() -> None:
    if not SECRET_FILE.exists():
        return
    for raw_line in SECRET_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def api_get(route: str, params: dict[str, str]) -> dict:
    api_key = os.environ.get("MP_API_KEY")
    if not api_key:
        raise RuntimeError("MP_API_KEY is missing; set it in the environment or local ignored credential file")
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(
        f"{BASE_URL}{route}?{query}",
        headers={"X-API-KEY": api_key, "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.load(response)


def load_formal_material_ids() -> list[str]:
    with INDEX_FILE.open(encoding="utf-8", newline="") as handle:
        return [row["material_id"] for row in csv.DictReader(handle)]


def serialize_summary_document(document) -> dict:
    """Serialize an MP document while preserving its public ID representation.

    MPID is a string subclass. Generic pydantic JSON serialization can expose
    its compact internal value instead of the public ``mp-<number>`` string.
    Identity fields are therefore normalized explicitly.
    """
    row = document.model_dump(mode="json")
    row["material_id"] = str(document.material_id)
    normalized_origins = []
    for origin in document.origins or []:
        item = origin.model_dump(mode="json") if hasattr(origin, "model_dump") else dict(origin)
        item["task_id"] = str(origin.task_id)
        normalized_origins.append(item)
    row["origins"] = normalized_origins
    return row


def mp_api_search(api_key: str, fields: list[str], material_ids: list[str]) -> tuple[list[dict], str | None]:
    """Use Materials Project's supported document model and JSON serialization."""
    from mp_api.client import MPRester

    with MPRester(api_key, mute_progress_bars=True) as mpr:
        documents = mpr.materials.summary.search(material_ids=material_ids, fields=fields)
        data = [serialize_summary_document(document) for document in documents]
        return data, mpr.db_version


def sanitized_error(exc: Exception, api_key: str | None) -> str:
    message = str(exc)
    return message.replace(api_key, "[REDACTED]") if api_key else message


def main() -> int:
    load_local_env()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    requested_fields = (
        "material_id,formula_pretty,chemsys,structure,band_gap,"
        "formation_energy_per_atom,energy_above_hull,is_stable,last_updated"
        ",origins"
    )
    api_key = os.environ.get("MP_API_KEY")
    formal_material_ids = load_formal_material_ids()
    audit = {
        "attempted_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_database": "Materials Project",
        "base_url": BASE_URL,
        "route": "/materials/summary/",
        "query": {
            "selector": "frozen_material_ids",
            "formula_context": "MoS2",
            "material_ids": formal_material_ids,
            "fields": requested_fields.split(","),
        },
        "credential_recorded": False,
        "response_status": "attempted",
        "client_preference": ["mp-api==0.46.4", "REST fallback"],
        "client_attempts": [],
    }
    data = None
    database_version = None
    try:
        if not api_key:
            raise RuntimeError("MP_API_KEY is missing; set it in the local ignored credential file")
        data, database_version = mp_api_search(api_key, requested_fields.split(","), formal_material_ids)
        audit["client_attempts"].append({"client": "mp-api==0.46.4", "status": "success"})
    except ImportError as exc:
        audit["client_attempts"].append({
            "client": "mp-api==0.46.4",
            "status": "unavailable",
            "error_type": type(exc).__name__,
            "error_message": sanitized_error(exc, api_key),
        })
    except Exception as exc:
        audit["client_attempts"].append({
            "client": "mp-api==0.46.4",
            "status": "failed",
            "error_type": type(exc).__name__,
            "error_message": sanitized_error(exc, api_key),
        })

    if data is None:
        try:
            payload = api_get(
                "/materials/summary/",
                {"material_ids": ",".join(formal_material_ids), "_fields": requested_fields},
            )
            data = payload.get("data", [])
            audit["client_attempts"].append({"client": "REST fallback", "status": "success"})
        except Exception as exc:
            audit["client_attempts"].append({
                "client": "REST fallback",
                "status": "failed",
                "error_type": type(exc).__name__,
                "error_message": sanitized_error(exc, api_key),
            })

    if data is None:
        last = audit["client_attempts"][-1]
        audit.update({
            "response_status": "failed",
            "records_returned": 0,
            "error_type": last["error_type"],
            "error_message": last["error_message"],
            "interpretation": "All client paths failed; no Materials Project data were claimed or mapped.",
        })
        (AUDIT_DIR / "materials_project_api_response_audit.json").write_text(
            json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"Materials Project probe failed after {len(audit['client_attempts'])} client attempt(s)", file=sys.stderr)
        print("Failure audit written to artifacts/materials_project_api_response_audit.json", file=sys.stderr)
        return 1

    returned_ids = sorted(str(row.get("material_id")) for row in data)
    requested_ids = sorted(formal_material_ids)
    identity_exact_match = returned_ids == requested_ids
    if not identity_exact_match:
        audit.update({
            "response_status": "failed_identity_mismatch",
            "database_version": database_version,
            "records_returned": len(data),
            "requested_material_ids": requested_ids,
            "returned_material_ids": returned_ids,
            "identity_exact_match": False,
            "interpretation": (
                "Transport succeeded, but returned IDs did not exactly match the frozen formal queue; "
                "mapping was blocked."
            ),
        })
        (AUDIT_DIR / "materials_project_api_response_audit.json").write_text(
            json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print("Materials Project probe blocked: returned IDs do not match the frozen queue", file=sys.stderr)
        return 1

    safe_record = {
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE_URL,
        "route": "/materials/summary/",
        "query_selector": "frozen_material_ids",
        "formula_context": "MoS2",
        "requested_material_ids": formal_material_ids,
        "records_returned": len(data),
        "database_version": database_version,
        "identity_exact_match": True,
        "data": data,
        "note": "Raw API response for local audit; formula-level matches still require per-record 2D review.",
    }
    output = OUTPUT_DIR / "materials_project_probe.json"
    output.write_text(json.dumps(safe_record, ensure_ascii=False, indent=2), encoding="utf-8")
    returned_fields = sorted({key for row in data for key in row})
    audit.update({
        "response_status": "success",
        "database_version": database_version,
        "requested_material_ids": requested_ids,
        "returned_material_ids": returned_ids,
        "identity_exact_match": True,
        "records_returned": len(data),
        "returned_fields": returned_fields,
        "missing_requested_fields": sorted(set(requested_fields.split(",")) - set(returned_fields)),
        "raw_response_location": ".local-data/materials_project_probe.json (git-ignored)",
        "interpretation": "API transport and requested-field schema succeeded; 2D and method audits remain separate gates.",
    })
    (AUDIT_DIR / "materials_project_api_response_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Materials Project probe succeeded: {len(data)} record(s); saved to .local-data/materials_project_probe.json")
    if data:
        print("Returned fields: " + ", ".join(sorted(data[0].keys())))
    print("Response audit written to artifacts/materials_project_api_response_audit.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
