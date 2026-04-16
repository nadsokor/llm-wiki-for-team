#!/bin/zsh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEST_SHARED="$(mktemp -d /tmp/team-sources-user-test.XXXXXX)"
TEST_PRIVATE="$(mktemp -d /tmp/user-wiki-test.XXXXXX)"
TEST_ADMIN_STATE="$(mktemp -d /tmp/admin-curator-state-test.XXXXXX)"
trap 'rm -rf "$TEST_SHARED" "$TEST_PRIVATE" "$TEST_ADMIN_STATE"' EXIT

cp -R "$ROOT_DIR/admin/Team Sources/." "$TEST_SHARED/"
mkdir -p "$TEST_SHARED/00_inbox/product"
cp "$ROOT_DIR/runtime/admin-curator/fixtures/bootstrap-smoke-test.md" "$TEST_SHARED/00_inbox/product/bootstrap-smoke-test.md"
"$ROOT_DIR/scripts/run_curator.sh" --vault "$TEST_SHARED" --state-dir "$TEST_ADMIN_STATE" >/dev/null

cp -R "$ROOT_DIR/user/User Wiki/." "$TEST_PRIVATE/"
"$ROOT_DIR/scripts/run_personal_ingest.sh" \
  --shared-vault "$TEST_SHARED" \
  --private-vault "$TEST_PRIVATE" \
  --state-file "$TEST_PRIVATE/.agent/ingest-state.json"

echo "Smoke test outputs:"
find "$TEST_PRIVATE/20_wiki" -type f | sort
