#!/bin/zsh
# Install the pinned official Materials Project client in the local virtual
# environment, then rerun the fail-closed formal pipeline.

set -u

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
cd "$PROJECT_DIR" || exit 1

echo "Installing the pinned official Materials Project client locally..."

if [[ ! -x ".venv/bin/python" ]]; then
  python3 -m venv .venv || exit 1
fi

.venv/bin/python -m pip install --upgrade pip
if [[ $? -ne 0 ]]; then
  echo "pip upgrade failed; formal pipeline was not run."
  exit 1
fi

.venv/bin/python -m pip install -r requirements-mp-api.txt
if [[ $? -ne 0 ]]; then
  echo "mp-api installation failed; formal pipeline was not run."
  exit 1
fi

echo
echo "Official client installed. Running the formal pipeline..."
.venv/bin/python scripts/run_formal_mp_pipeline.py
STATUS=$?
echo
echo "Machine-readable status: artifacts/formal_queue_pipeline_status.json"
echo "Press Return to close this window."
read
exit $STATUS

