#!/bin/zsh
set -u
SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
cd "$PROJECT_DIR" || exit 1

echo "Refreshing the formal MP response with database version metadata..."
.venv/bin/python scripts/run_formal_mp_pipeline.py || exit 1

echo
echo "Resolving web-index IDs through the official API..."
.venv/bin/python scripts/resolve_mos2_ids.py
STATUS=$?
echo
echo "Audit: artifacts/mos2_id_resolution_audit.json"
echo "Press Return to close this window."
read
exit $STATUS

