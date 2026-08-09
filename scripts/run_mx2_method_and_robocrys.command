#!/bin/zsh
set -u
SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
cd "$PROJECT_DIR" || exit 1
export MPLCONFIGDIR="$PROJECT_DIR/.local-data/matplotlib-cache"
mkdir -p "$MPLCONFIGDIR"
echo "Collecting MX2 method provenance and Robocrys evidence..."
"$PROJECT_DIR/.venv/bin/python" "$PROJECT_DIR/scripts/probe_mx2_method_and_robocrys.py"
status=$?
if [[ $status -eq 0 ]]; then
  echo "MX2 method and Robocrys evidence completed. Return to Codex and send: MX2方法完成"
else
  echo "The evidence request stopped; see the sanitized public audit."
fi
read -r "?Press Return to close this window."
exit $status
