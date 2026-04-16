# Team Sources Vault

This is the local shared-vault skeleton for the administrator host.

Shared layers:

- `00_inbox/`: raw drops from humans or external dumps
- `10_sources/`: canonical normalized source notes
- `11_assets/`: preserved binaries and extracted assets
- `12_indices/`: machine-readable registries
- `20_public_wiki/`: team ground truth distilled from evidence
- `90_governance/`: templates and curation rules

Write policy:

- humans should write to `00_inbox/`
- curator automation writes to `10_sources/`, `11_assets/`, `12_indices/`, and `20_public_wiki/`
- curator runtime state must stay outside this vault
