# Admin Deployment

This directory contains the local administrator deployment for the shared knowledge system.

Local paths:

- shared vault: `admin/Team Sources`
- curator runtime state: `runtime/admin-curator`
- curator launcher: `scripts/run_curator.sh`
- curator implementation: `scripts/run_curator.py`

Recommended local flow:

1. Run `scripts/install_admin_runtime.sh`
2. Run `scripts/smoke_test_admin.sh`
3. Drop raw files into `admin/Team Sources/00_inbox/...`
4. Run `scripts/run_curator.sh`
5. Review generated canonical notes in `admin/Team Sources/10_sources/`
6. Review generated ground-truth notes in `admin/Team Sources/20_public_wiki/`

If you later connect this machine to Obsidian Sync:

- point the shared vault to `admin/Team Sources`
- keep curator runtime state outside the vault
- use a dedicated config folder such as `.obsidian-curator`
