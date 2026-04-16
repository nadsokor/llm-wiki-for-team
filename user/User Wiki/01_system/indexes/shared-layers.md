# Shared Layers

## Shared Evidence

- Vault: `Team Sources`
- Path: `10_sources/`
- Contract: append-only canonical evidence maintained by the source curator

## Shared Ground Truth

- Vault: `Team Sources`
- Path: `20_public_wiki/`
- Contract: team decisions, concepts, glossary, and maps maintained by the source curator

## Cross-Vault Linking

Use `obsidian://open` URIs when storing references to shared artifacts.

Example source link:

```md
[Open source](obsidian://open?vault=Team%20Sources&file=10_sources%2Fproduct%2FSRC-PRO-2026-0001-roadmap-q2)
```

Example ground-truth link:

```md
[Open team decision](obsidian://open?vault=Team%20Sources&file=20_public_wiki%2Fdecisions%2FGT-DEC-2026-0003-beta-scope-freeze)
```
