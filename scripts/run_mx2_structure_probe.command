#!/bin/zsh
set -u

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
cd "$PROJECT_DIR" || exit 1
export MPLCONFIGDIR="$PROJECT_DIR/.local-data/matplotlib-cache"
mkdir -p "$MPLCONFIGDIR"

echo "Fetching structures and origins for the frozen 25-record MX2 queue..."
"$PROJECT_DIR/.venv/bin/python" "$PROJECT_DIR/scripts/probe_mp_mx2_structures.py"
status=$?
if [[ $status -eq 0 ]]; then
  echo "MX2 structure acquisition completed. Return to Codex and send: MX2结构完成"
else
  echo "MX2 structure acquisition stopped; see the sanitized public audit."
fi
read -r "?Press Return to close this window."
exit $status
