#!/bin/zsh
set -u
SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
cd "$PROJECT_DIR" || exit 1
.venv/bin/python scripts/probe_uncertain_dimensionality.py
STATUS=$?
echo
echo "Audit: artifacts/mos2_uncertain_robocrys_audit.json"
echo "Press Return to close this window."
read
exit $STATUS

