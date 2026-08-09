#!/bin/zsh
set -u

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
cd "$PROJECT_DIR" || exit 1

export MPLCONFIGDIR="$PROJECT_DIR/.local-data/matplotlib-cache"
mkdir -p "$MPLCONFIGDIR"

echo "Running the preregistered Materials Project MX2 index query..."
echo "Raw API data will remain in the ignored .local-data directory."

if [[ ! -x "$PROJECT_DIR/.venv/bin/python" ]]; then
  echo "The project virtual environment is unavailable. Run scripts/setup_and_run_mp.command first."
  read -r "?Press Return to close this window."
  exit 1
fi

"$PROJECT_DIR/.venv/bin/python" "$PROJECT_DIR/scripts/probe_mp_mx2_validation_index.py"
status=$?

if [[ $status -eq 0 ]]; then
  echo "MX2 index acquisition completed. Return to Codex and send: MX2索引完成"
else
  echo "MX2 index acquisition stopped. The public audit contains a sanitized failure record."
fi

read -r "?Press Return to close this window."
exit $status
