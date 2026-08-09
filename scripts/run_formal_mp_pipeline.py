"""One reproducible entry point for MP acquisition, mapping and queue readiness."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUS_PATH = ROOT / "artifacts" / "formal_queue_pipeline_status.json"


def run_script(name: str) -> dict:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / name)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "script": f"scripts/{name}",
        "exit_code": completed.returncode,
        "status": "success" if completed.returncode == 0 else "failed",
        "stdout_tail": completed.stdout.strip().splitlines()[-3:],
        "stderr_tail": completed.stderr.strip().splitlines()[-3:],
    }


def main() -> int:
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    acquisition = run_script("probe_materials_project.py")
    stages = [acquisition]
    if acquisition["exit_code"] == 0:
        stages.append(run_script("map_materials_project_response.py"))
    else:
        stages.append({
            "script": "scripts/map_materials_project_response.py",
            "status": "not_run",
            "reason": "acquisition_failed; no substitute data allowed",
        })
    ready = all(stage.get("status") == "success" for stage in stages)
    status = {
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "queue_id": "mp-mos2-polymorph-demo-v1",
        "source_database": "Materials Project",
        "python_executable": sys.executable,
        "stages": stages,
        "queue_ready_for_manual_audit": ready,
        "queue_ready_for_closed_loop": False,
        "next_gate": "manual dimensionality and calculation-method audit" if ready else "successful official API acquisition",
        "result_statement": (
            "Acquisition and mapping succeeded; records remain quarantined pending audit."
            if ready else
            "Formal queue is not ready. The pipeline stopped without substituting synthetic or web-transcribed data."
        ),
    }
    STATUS_PATH.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    print(status["result_statement"])
    print("Status written to artifacts/formal_queue_pipeline_status.json")
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
