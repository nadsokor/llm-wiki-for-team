#!/bin/zsh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="${VENV_DIR:-$ROOT_DIR/.venv-user}"
SHARED_VAULT_PATH="${SHARED_VAULT_PATH:-$ROOT_DIR/admin/Team Sources}"
PRIVATE_VAULT_PATH="${PRIVATE_VAULT_PATH:-$ROOT_DIR/user/User Wiki}"
INGEST_STATE_FILE="${INGEST_STATE_FILE:-$PRIVATE_VAULT_PATH/.agent/ingest-state.json}"

if [[ -x "$VENV_DIR/bin/python" ]]; then
  PYTHON_BIN="$VENV_DIR/bin/python"
else
  PYTHON_BIN="python3"
fi

exec "$PYTHON_BIN" \
  "$ROOT_DIR/scripts/run_personal_ingest.py" \
  --shared-vault "$SHARED_VAULT_PATH" \
  --private-vault "$PRIVATE_VAULT_PATH" \
  --state-file "$INGEST_STATE_FILE" \
  "$@"
