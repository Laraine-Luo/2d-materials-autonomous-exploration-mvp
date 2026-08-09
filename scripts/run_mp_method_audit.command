#!/bin/zsh
set -u
SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
cd "$PROJECT_DIR" || exit 1

.venv/bin/python scripts/probe_mp_methods.py
STATUS=$?
echo
echo "Audit: artifacts/mos2_method_evidence_audit.json"
echo "Press Return to close this window."
read
exit $STATUS

