#!/bin/zsh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="${VENV_DIR:-$ROOT_DIR/.venv-user}"
UV_BIN="${UV_BIN:-$HOME/.local/bin/uv}"

if [[ -x "$UV_BIN" ]]; then
  "$UV_BIN" venv --python 3.12 "$VENV_DIR"
else
  python3 -m venv "$VENV_DIR"
fi

cat <<EOF
User runtime installed.
Venv: $VENV_DIR
Next step: $ROOT_DIR/scripts/run_personal_ingest.sh
EOF
