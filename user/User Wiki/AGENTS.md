# Personal Wiki Agent Guide

## Mission

This vault is a compiled private wiki. The human asks questions, reviews outputs, and evolves durable pages. The agent reads shared evidence and shared ground truth, then maintains the private wiki.

This deployment keeps the three-layer spirit of `llm-wiki-obsidian`:

1. shared `Team Sources/10_sources/` is the evidence layer
2. private `20_wiki/` is the knowledge layer
3. private `01_system/` is the operating layer with indexes, templates, and logs

## Directory Contract

- `00_home/`
  Human-friendly entry points and dashboards.
- `01_system/`
  Rules, index, log, templates, prompts, and helper materials.
- shared `Team Sources/10_sources/`
  Canonical evidence owned by the shared vault.
- shared `Team Sources/20_public_wiki/`
  Team ground truth owned by the shared vault.
- `20_wiki/`
  Private maintained wiki pages.
- `30_outputs/`
  Exportable private deliverables.
- `40_workspace/`
  Working notes and short-lived drafts.
- `90_archive/`
  Dormant but searchable private material.

## Non-Negotiable Rules

1. Never modify any file in the shared `Team Sources` vault from this vault or its automation.
2. Prefer updating an existing wiki page over creating near-duplicates.
3. Durable conclusions should point back to one or more shared sources or shared public wiki notes.
4. If evidence conflicts, preserve the conflict explicitly.
5. Separate source capture, team ground truth, and personal interpretation.
6. Maintain links aggressively.
7. Record meaningful ingest or review activity in `01_system/log.md`.
8. Keep `01_system/index.md` useful for a new session or a new agent.

## Canonical Page Types

- `area`
- `project`
- `entity`
- `concept`
- `source`
- `synthesis`
- `decision`
- `review`

## Ingest Workflow

1. Read shared canonical material from `Team Sources/10_sources/` and `Team Sources/20_public_wiki/`.
2. Create or update matching pages in `20_wiki/`.
3. Carry forward `source_id`, `shared_wiki_id`, and `obsidian://open` references.
4. Update the relevant `area`, `project`, `entity`, `concept`, and `decision` pages.
5. Add a concise entry to `01_system/log.md`.
6. Update `01_system/index.md` if a new durable page was added.

## Query Workflow

1. Read `01_system/index.md` first.
2. Prefer reading `20_wiki/` before dropping down to the shared vault.
3. Use the shared vault for verification or unresolved ambiguity.
4. Save reusable answers into `20_wiki/syntheses/` when valuable.
