# User Deployment

This directory contains the local user-side deployment for the private wiki.

Local paths:

- private vault: `user/User Wiki`
- shared vault input: `admin/Team Sources`
- ingest runtime: `runtime/user-ingest`
- ingest launcher: `scripts/run_personal_ingest.sh`
- ingest implementation: `scripts/run_personal_ingest.py`

Recommended local flow:

1. Run `scripts/install_user_runtime.sh`
2. Open `user/User Wiki` in Obsidian
3. Review `user/User Wiki/AGENTS.md`
4. Run `scripts/smoke_test_user.sh`
5. Run `scripts/run_personal_ingest.sh`

The private vault follows the `llm-wiki-obsidian` style skeleton, but the evidence layer is externalized into the shared `Team Sources` vault.
