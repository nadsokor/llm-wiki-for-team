#!/bin/zsh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="${VENV_DIR:-$ROOT_DIR/.venv-admin}"
UV_BIN="${UV_BIN:-$HOME/.local/bin/uv}"

if [[ -x "$UV_BIN" ]]; then
  "$UV_BIN" venv --python 3.12 "$VENV_DIR"
  "$UV_BIN" pip install --python "$VENV_DIR/bin/python" "markitdown[all]" pyyaml
else
  python3 -m venv "$VENV_DIR"
  "$VENV_DIR/bin/python" -m pip install --upgrade pip
  "$VENV_DIR/bin/python" -m pip install pyyaml
  cat <<EOF
Warning: uv was not found, so the runtime was created with the system Python.
Official MarkItDown needs Python 3.10+, so install uv first if you want full document conversion support.
EOF
fi

cat <<EOF
Admin runtime installed.
Venv: $VENV_DIR
Next step: $ROOT_DIR/scripts/run_curator.sh
EOF
