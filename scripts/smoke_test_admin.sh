#!/bin/zsh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FIXTURE_PATH="$ROOT_DIR/runtime/admin-curator/fixtures/bootstrap-smoke-test.md"
TEST_VAULT="$(mktemp -d /tmp/team-sources-test.XXXXXX)"
TEST_STATE="$(mktemp -d /tmp/curator-state-test.XXXXXX)"
trap 'rm -rf "$TEST_VAULT" "$TEST_STATE"' EXIT

mkdir -p "$TEST_VAULT"
cp -R "$ROOT_DIR/admin/Team Sources/." "$TEST_VAULT/"
mkdir -p "$TEST_VAULT/00_inbox/product"
cp "$FIXTURE_PATH" "$TEST_VAULT/00_inbox/product/bootstrap-smoke-test.md"

"$ROOT_DIR/scripts/run_curator.sh" --vault "$TEST_VAULT" --state-dir "$TEST_STATE"

echo "Smoke test outputs:"
find "$TEST_VAULT/10_sources" -type f | sort
find "$TEST_VAULT/20_public_wiki" -type f | sort
