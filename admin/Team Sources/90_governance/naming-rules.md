# Naming Rules

Source note file name:

- `<source_id>-<slug>.md`
- example: `SRC-PRO-2026-0001-roadmap-q2.md`

Public wiki file name:

- `<shared_wiki_id>-<slug>.md`
- example: `GT-DEC-2026-0003-beta-scope-freeze.md`

Identifier rules:

- source IDs use `SRC-<domain-code>-<year>-<sequence>`
- public wiki IDs use `GT-<type-code>-<year>-<sequence>`

Domain codes:

- `PRO`: product
- `ENG`: engineering
- `RES`: research
- `PRC`: process

Public wiki type codes:

- `DEC`: decision
- `CON`: concept
- `GLS`: glossary
- `MAP`: map

Slug rules:

- lowercase
- use `-` as separator
- keep only ascii letters and digits when possible
- prefer deterministic slugs derived from the title or source file stem
