#!/bin/zsh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="${VENV_DIR:-$ROOT_DIR/.venv-admin}"
TEAM_SOURCES_VAULT="${TEAM_SOURCES_VAULT:-$ROOT_DIR/admin/Team Sources}"
CURATOR_STATE_DIR="${CURATOR_STATE_DIR:-$ROOT_DIR/runtime/admin-curator/state}"

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  echo "Missing Python runtime at $VENV_DIR. Run scripts/install_admin_runtime.sh first." >&2
  exit 1
fi

exec "$VENV_DIR/bin/python" \
  "$ROOT_DIR/scripts/run_curator.py" \
  --vault "$TEAM_SOURCES_VAULT" \
  --state-dir "$CURATOR_STATE_DIR" \
  "$@"
