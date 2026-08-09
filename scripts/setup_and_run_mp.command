#!/bin/zsh
# Local-only credential setup and formal Materials Project probe for macOS.
# The key is entered without terminal echo and written only to a git-ignored file.

set -u

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
SECRET_DIR="$PROJECT_DIR/.local-secrets"
SECRET_FILE="$SECRET_DIR/materials_project.env"

echo "Materials Project formal-data setup"
echo "Use the main 'Your API Key' from the Materials Project dashboard."
echo "Do not use an MPContribs token or an OPTIMADE endpoint."
echo
read -s "MP_KEY_INPUT?Paste the newly rotated API key (input is hidden): "
echo

if [[ -z "$MP_KEY_INPUT" ]]; then
  echo "No key entered. Nothing was changed."
  exit 1
fi

mkdir -p "$SECRET_DIR"
umask 077
printf 'MP_API_KEY=%s\n' "$MP_KEY_INPUT" > "$SECRET_FILE"
unset MP_KEY_INPUT
chmod 600 "$SECRET_FILE"

echo "Credential saved to the local ignored secret directory."
echo "Running the formal Materials Project pipeline..."
cd "$PROJECT_DIR" || exit 1

if [[ -x ".venv/bin/python" ]]; then
  .venv/bin/python scripts/run_formal_mp_pipeline.py
else
  python3 scripts/run_formal_mp_pipeline.py
fi

STATUS=$?
echo
echo "Machine-readable status: artifacts/formal_queue_pipeline_status.json"
if [[ $STATUS -ne 0 ]]; then
  echo "The formal queue is still blocked. Review the status file; no substitute data were used."
fi
exit $STATUS

