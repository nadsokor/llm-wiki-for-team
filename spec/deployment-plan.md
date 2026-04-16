# Obsidian LLM Wiki Deployment Plan

## Goal

Build a team knowledge system based on the `llm-wiki-obsidian` style skeleton with these guarantees:

- all shared raw and normalized source material lives in one shared vault
- all team-level ground truth, decisions, and core concepts live in a shared public wiki layer in that same shared vault
- all personal wiki pages, summaries, embeddings, and agent state live in private vaults
- a dedicated source curator agent is the only automated writer to canonical shared sources and shared public wiki notes
- personal ingest agents can read shared sources and shared public wiki notes but must never modify them

## Core Design

Do not treat `10_sources/` as just one folder inside a mixed-permission vault.
Treat the shared layer as two upstream read-only dependencies for users:

- `10_sources/`: evidence and normalized source material
- `20_public_wiki/`: team ground truth distilled from the evidence layer

Use two vault classes:

1. `Team Sources` shared vault
2. `User Wiki` private vault, one per user

Topology:

```text
People -> Team Sources/00_inbox -> Source Curator Agent -> Team Sources/10_sources
                                                           -> Team Sources/11_assets
                                                           -> Team Sources/12_indices
                                                           -> Team Sources/20_public_wiki

Personal Ingest Agent -> reads Team Sources/10_sources + 11_assets + 20_public_wiki
                      -> writes User Wiki/20_wiki + 30_outputs + .agent
```

## Vault Layout

### Shared Vault: `Team Sources`

```text
Team Sources/
  00_inbox/
    product/
    research/
    meeting/
    misc/
  10_sources/
    product/
    engineering/
    research/
    process/
  11_assets/
    SRC-*/
  12_indices/
    source-registry.jsonl
    public-wiki-registry.jsonl
    source-taxonomy.md
  20_public_wiki/
    decisions/
    concepts/
    glossary/
    maps/
  90_governance/
    source-template.md
    public-wiki-template.md
    category-rules.md
    naming-rules.md
```

Rules:

- humans may create or drop files into `00_inbox/`
- humans should not manually edit files under `10_sources/` unless acting as curator maintainers
- humans should not manually edit files under `20_public_wiki/` unless acting as shared knowledge maintainers
- the source curator agent may read all folders and write only `10_sources/`, `11_assets/`, `12_indices/`, and `20_public_wiki/`
- `10_sources/` is the canonical evidence layer used by all ingest agents
- `20_public_wiki/` is the canonical team ground-truth layer used by all ingest agents

### Private Vault: `User Wiki`

```text
User Wiki/
  01_system/
    indexes/
    prompts/
    templates/
  20_wiki/
  30_outputs/
  40_workspace/
  .agent/
    ingest-state.json
    source-cache/
    embeddings/
```

Rules:

- the private ingest agent may read the local copy of `Team Sources`
- the private ingest agent may write anywhere inside the private vault
- the private ingest agent must never modify any file in the shared vault
- personal notes may contain links to shared sources and shared public wiki notes via `obsidian://open` URIs

## Canonical Source Contract

Each normalized source file in `10_sources/` should be Markdown and should preserve references to origin files and attachments.

Suggested frontmatter:

```yaml
---
source_id: SRC-PRD-2026-0001
title: Product roadmap Q2
source_type: prd
domain: product
status: canonical
origin_path: 00_inbox/product/roadmap-q2.docx
origin_filename: roadmap-q2.docx
origin_modified_at: 2026-04-15T09:10:00+08:00
normalized_at: 2026-04-15T09:20:00+08:00
normalized_by: source-curator
content_hash: sha256:...
attachments:
  - 11_assets/SRC-PRD-2026-0001/figure-01.png
tags:
  - product/prd
  - roadmap
---
```

Body rules:

- preserve section hierarchy from the source when possible
- convert tables to Markdown if reasonable, otherwise attach as files and summarize the structure
- keep image references stable and relative to the vault
- append a short `## Source Trace` section with origin information when conversion is lossy

## Shared Public Wiki Contract

Each ground-truth note in `20_public_wiki/` should be concise, stable, and clearly supported by canonical sources.

Suggested frontmatter:

```yaml
---
shared_wiki_id: GT-DEC-2026-0003
title: Beta scope is frozen two weeks before launch
shared_wiki_type: decision
domain: product
status: active
consensus_strength: explicit
maintained_by: source-curator
derived_from:
  - source_id: SRC-PRD-2026-0001
  - source_id: SRC-MTG-2026-0012
last_reviewed_at: 2026-04-16T09:00:00+08:00
content_hash: sha256:...
tags:
  - ground-truth/decision
  - launch
---
```

Body rules:

- keep the first section as the canonical statement or definition
- distinguish `decision` notes from `concept` notes clearly
- link back to supporting `source_id`s or `obsidian://open` source links
- do not create a ground-truth note from weak implication alone; require explicit agreement or repeated strong evidence
- when evidence conflicts, prefer updating or superseding the public wiki note instead of silently drifting

## Private Wiki Contract

Personal wiki notes should keep stable source references instead of copying source content blindly.

Suggested frontmatter:

```yaml
---
title: Q2 roadmap interpretation
source_refs:
  - source_id: SRC-PRD-2026-0001
    source_uri: obsidian://open?vault=Team%20Sources&file=10_sources%2Fproduct%2FSRC-PRD-2026-0001-roadmap-q2
shared_wiki_refs:
  - shared_wiki_id: GT-DEC-2026-0003
    shared_wiki_uri: obsidian://open?vault=Team%20Sources&file=20_public_wiki%2Fdecisions%2FGT-DEC-2026-0003-beta-scope-freeze
ingest:
  source_content_hash: sha256:...
  processed_at: 2026-04-15T10:00:00+08:00
  generated_by: personal-ingest
---
```

## Agent Roles

### Role A: Source Curator Agent

Purpose:

- normalize raw dumps from `00_inbox/`
- convert files into Markdown when possible
- preserve attachments
- classify content into canonical shared source folders
- extract team-level decisions, concepts, and other strong consensus into shared public wiki notes
- update a machine-readable registry of sources

Preferred conversion stack:

- `MarkItDown` for Office docs, PDFs, and rich text when available
- OCR or image extraction tools only when needed
- fallback converters such as `pandoc` when MarkItDown is not sufficient

Write permissions:

- allowed: `10_sources/`, `11_assets/`, `12_indices/`, `20_public_wiki/`
- forbidden: deleting arbitrary inbox material without an explicit archival policy
- forbidden: editing any personal vault

Processing workflow:

1. Scan `00_inbox/` for new or changed files.
2. Compute a fingerprint from path, size, modified time, and content hash.
3. Convert the file to Markdown plus extracted attachments.
4. Assign `source_id`, category, and canonical output path.
5. Write the normalized Markdown to `10_sources/`.
6. Write extracted images or binary attachments to `11_assets/<source_id>/`.
7. Extract explicit team decisions, concepts, and stable terminology where evidence is strong.
8. Upsert or create notes in `20_public_wiki/`.
9. Update `12_indices/source-registry.jsonl` and `12_indices/public-wiki-registry.jsonl`.
10. Optionally move the original file to an inbox archive folder, or leave it in place with a processed marker.

### Role B: Personal Ingest Agent

Purpose:

- detect changes in canonical shared sources
- detect changes in shared public wiki notes
- ingest only changed or new shared artifacts
- generate personal wiki pages, summaries, maps, and outputs
- maintain personal state without touching shared files

Read permissions:

- local copy of `Team Sources`

Write permissions:

- only inside the private vault

Hard safety rule:

- no create, update, move, rename, or delete operation may target the shared vault path

Processing workflow:

1. Read `.agent/ingest-state.json`.
2. Scan `Team Sources/10_sources/`, `20_public_wiki/`, and optionally `11_assets/`.
3. Compare `source_id`, `shared_wiki_id`, and `content_hash` against local state.
4. Build a diff set of new, changed, and removed shared artifacts.
5. Ingest only the diff set.
6. Write or refresh pages in `20_wiki/`.
7. Write summaries and deliverables in `30_outputs/`.
8. Update `.agent/ingest-state.json`.

## Recommended Diff State Format

Store one record per source:

```json
{
  "artifact_type": "source",
  "source_id": "SRC-PRD-2026-0001",
  "source_path": "10_sources/product/SRC-PRD-2026-0001-roadmap-q2.md",
  "content_hash": "sha256:...",
  "last_processed_at": "2026-04-15T10:00:00+08:00",
  "wiki_targets": [
    "20_wiki/product/Q2 roadmap interpretation.md"
  ]
}
```

For shared public wiki notes, use the same state file with `artifact_type: "shared_wiki"` and `shared_wiki_id`.

## Obsidian Recommended Configuration

### Shared Vault Settings: `Team Sources`

Recommended for all human users:

- use this vault for collecting raw material, browsing evidence, and browsing the shared public wiki
- write manually only to `00_inbox/` unless you are a designated curator maintainer or shared knowledge maintainer
- keep plugin usage minimal

Recommended Sync settings:

- enable note sync
- enable image sync
- enable PDF sync
- enable `unsupported` file sync if the team still drops `.docx`, `.pptx`, `.xlsx`, or other binaries into `00_inbox/`
- disable config syncing for the shared vault to avoid cross-user settings pollution

Recommended operational notes:

- do not rely on shared-vault permissions for isolation; Obsidian shared vault collaborators have equivalent file permissions except sharing management
- use a dedicated machine or node for the source curator agent if it needs headless sync
- do not run Obsidian desktop sync and Obsidian Headless sync on the same vault on the same device

### Private Vault Settings: `User Wiki`

Recommended Sync settings:

- each user gets a separate private remote vault
- enable config sync so personal settings can travel across that user's devices
- enable file recovery

Recommended plugins and features:

- Templates
- Properties
- Search
- Graph and backlinks for private knowledge pages
- optional Dataview or other community plugins only in the private vault, not the shared vault

## Cross-Vault References

Private notes may reference shared source notes and shared public wiki notes using Obsidian URI links:

```md
[Open source](obsidian://open?vault=Team%20Sources&file=10_sources%2Fproduct%2FSRC-PRD-2026-0001-roadmap-q2)
[Open team decision](obsidian://open?vault=Team%20Sources&file=20_public_wiki%2Fdecisions%2FGT-DEC-2026-0003-beta-scope-freeze)
```

Guidelines:

- do not depend on cross-vault `[[wikilink]]` behavior
- keep a stable `source_id` in both shared and private notes
- keep a stable `shared_wiki_id` for team ground-truth notes
- generate `obsidian://open` links from those IDs plus canonical paths

## Deployment Pattern

### Administrator Side

Use one dedicated source-curation node:

- connects to the `Team Sources` remote vault
- runs the source curator agent
- owns canonical writes to `10_sources/`, `11_assets/`, `12_indices/`, and `20_public_wiki/`

Recommended bootstrap order:

1. Create the shared `Team Sources` remote vault.
2. Create the folder structure shown above.
3. Add `90_governance/` templates and naming rules.
4. Invite team members.
5. Set up one dedicated curator machine or server.
6. Install conversion tools such as MarkItDown.
7. Configure the source curator agent with the prompt in `prompts/source-curator-agent.md`.

Example dedicated-node bootstrap:

```sh
npm install -g obsidian-headless
mkdir -p "$TEAM_SOURCES_PATH"
cd "$TEAM_SOURCES_PATH"
ob login
ob sync-setup --vault "Team Sources" --config-dir .obsidian-curator
ob sync-config --mode bidirectional --file-types image,pdf,unsupported --configs ""
```

### User Side

Each user sets up two local vaults:

1. local copy of `Team Sources`
2. local `User Wiki`

Recommended bootstrap order:

1. Join the shared `Team Sources` vault.
2. Create a private remote vault for `User Wiki`.
3. Create the private folder structure.
4. Configure the personal ingest agent with the prompt in `prompts/personal-ingest-agent.md`.
5. Point the ingest agent at the local `Team Sources` path in read-only mode.
6. Store ingest state only in the private vault.

Optional private-node bootstrap for a dedicated personal automation machine:

```sh
npm install -g obsidian-headless
mkdir -p "$USER_WIKI_PATH"
cd "$USER_WIKI_PATH"
ob login
ob sync-setup --vault "User Wiki" --config-dir .obsidian
ob sync-config --mode bidirectional --file-types image,pdf --configs app,appearance,appearance-data,hotkey,core-plugin,core-plugin-data,community-plugin,community-plugin-data
```

## Non-Negotiable Safety Rules

- `Team Sources/10_sources/` is canonical and shared
- `Team Sources/20_public_wiki/` is canonical and shared
- only the source curator agent may write canonical shared sources and automated shared public wiki notes
- personal ingest agents are read-only with respect to the shared vault
- no personal state may be stored in the shared vault
- no embeddings, checkpoints, caches, or temporary outputs may be stored in the shared vault

## Success Criteria

The deployment is correct when all of the following are true:

- team members can drop raw material into `00_inbox/`
- the curator agent converts and classifies raw material into canonical Markdown sources
- the curator agent extracts explicit decisions and concepts into `20_public_wiki/`
- attachments remain accessible from canonical source notes
- each user can ingest diffs from both shared sources and shared public wiki into a private wiki
- private outputs sync across that user's devices without leaking to the shared vault
- no personal agent ever writes back into `Team Sources`
