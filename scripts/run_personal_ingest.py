#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import quote


SOURCE_FOLDER_MAP = {
    "product": "sources",
    "engineering": "sources",
    "research": "sources",
    "process": "sources",
}
PUBLIC_FOLDER_MAP = {
    "decision": "decisions",
    "concept": "concepts",
    "glossary": "concepts",
    "map": "syntheses",
}


def now_iso() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def slugify(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = re.sub(r"-{2,}", "-", lowered).strip("-")
    return lowered or "untitled"


def load_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_jsonl(path: Path, key: str) -> dict[str, dict]:
    records: dict[str, dict] = {}
    if not path.exists():
        return records
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        record = json.loads(line)
        record_key = record.get(key)
        if record_key:
            records[record_key] = record
    return records


def read_markdown(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---\n"):
        return {}, text
    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        return {}, text
    frontmatter_text = parts[0][4:]
    body = parts[1]
    frontmatter: dict[str, object] = {}
    current_list_key: str | None = None
    current_list: list[object] | None = None
    current_dict: dict | None = None

    for raw_line in frontmatter_text.splitlines():
        if not raw_line.strip():
            continue
        if raw_line.startswith("  - ") and current_list is not None:
            item_text = raw_line[4:].strip()
            if ": " in item_text:
                key, value = item_text.split(": ", 1)
                current_dict = {key: value}
                current_list.append(current_dict)
            else:
                current_list.append(item_text)
            continue
        if raw_line.startswith("    ") and current_dict is not None and ": " in raw_line.strip():
            key, value = raw_line.strip().split(": ", 1)
            current_dict[key] = value
            continue
        current_dict = None
        if ": " in raw_line:
            key, value = raw_line.split(": ", 1)
            if value == "[]":
                frontmatter[key] = []
                current_list_key = None
                current_list = None
            else:
                frontmatter[key] = value.strip('"')
                current_list_key = None
                current_list = None
        elif raw_line.endswith(":"):
            key = raw_line[:-1]
            frontmatter[key] = []
            current_list_key = key
            current_list = frontmatter[key]
        else:
            current_list_key = None
            current_list = None
    return frontmatter, body


def obsidian_uri(vault_name: str, relative_path: str) -> str:
    normalized = relative_path.replace("\\", "/")
    if normalized.endswith(".md"):
        normalized = normalized[:-3]
    return f"obsidian://open?vault={quote(vault_name)}&file={quote(normalized, safe='/')}"


def extract_summary(body: str) -> str:
    for block in body.split("\n\n"):
        candidate = block.strip()
        if not candidate or candidate.startswith("#") or candidate.startswith("- "):
            continue
        return candidate[:400]
    return "No summary extracted yet."


def source_note_content(source_record: dict, shared_path: str, summary: str, related_public: list[dict], vault_name: str) -> str:
    source_uri = obsidian_uri(vault_name, shared_path)
    related_lines = "\n".join(
        f"- {item['shared_wiki_id']}: [{item['title']}]({obsidian_uri(vault_name, item['path'])})"
        for item in related_public
    ) or "- none"
    return (
        "---\n"
        "page_type: source\n"
        f"title: \"{source_record.get('title', 'Untitled source')}\"\n"
        "source_refs:\n"
        f"  - source_id: {source_record['source_id']}\n"
        f"    source_uri: {source_uri}\n"
        "shared_wiki_refs: []\n"
        "updated_at: "
        f"{now_iso()}\n"
        "---\n\n"
        f"# {source_record.get('title', source_record['source_id'])}\n\n"
        "## Shared Source\n\n"
        f"- source_id: `{source_record['source_id']}`\n"
        f"- canonical note: [Open shared source]({source_uri})\n\n"
        "## Summary\n\n"
        f"{summary}\n\n"
        "## Related Team Ground Truth\n\n"
        f"{related_lines}\n\n"
        "## Personal Notes\n\n"
        "Add private interpretation, follow-ups, and local links here.\n"
    )


def public_note_content(public_record: dict, frontmatter: dict, body: str, vault_name: str) -> str:
    public_uri = obsidian_uri(vault_name, public_record["path"])
    derived_from = frontmatter.get("derived_from", [])
    if isinstance(derived_from, list):
        source_lines = []
        for item in derived_from:
            if isinstance(item, dict) and item.get("source_id"):
                source_lines.append(f"- `{item['source_id']}`")
            else:
                source_lines.append(f"- {item}")
        sources_block = "\n".join(source_lines) or "- none"
    else:
        sources_block = "- none"
    canonical_statement = extract_summary(body)
    return (
        "---\n"
        f"page_type: {public_record.get('shared_wiki_type', 'concept')}\n"
        f"title: \"{public_record.get('title', public_record['shared_wiki_id'])}\"\n"
        "source_refs: []\n"
        "shared_wiki_refs:\n"
        f"  - shared_wiki_id: {public_record['shared_wiki_id']}\n"
        f"    shared_wiki_uri: {public_uri}\n"
        f"updated_at: {now_iso()}\n"
        "---\n\n"
        f"# {public_record.get('title', public_record['shared_wiki_id'])}\n\n"
        "## Team Ground Truth\n\n"
        f"- shared_wiki_id: `{public_record['shared_wiki_id']}`\n"
        f"- canonical note: [Open team note]({public_uri})\n\n"
        "## Canonical Statement\n\n"
        f"{canonical_statement}\n\n"
        "## Supporting Sources\n\n"
        f"{sources_block}\n\n"
        "## Personal Notes\n\n"
        "Add private interpretation, disagreements, or downstream actions here.\n"
    )


def append_log(log_path: Path, lines: list[str]) -> None:
    existing = log_path.read_text(encoding="utf-8") if log_path.exists() else "# Ingest Log\n\n"
    suffix = "".join(lines)
    log_path.write_text(existing + suffix, encoding="utf-8")


def update_system_index(private_vault: Path, source_count: int, public_count: int) -> None:
    index_path = private_vault / "01_system/index.md"
    content = (
        "# System Index\n\n"
        "## Vault Purpose\n\n"
        "This private vault follows the `llm-wiki-obsidian` compiled-wiki pattern, but it reads evidence and team ground truth from the shared `Team Sources` vault instead of storing canonical shared material locally.\n\n"
        "## Shared Dependency Status\n\n"
        f"- source pages mirrored: {source_count}\n"
        f"- team ground-truth pages mirrored: {public_count}\n"
        f"- last ingest: {now_iso()}\n\n"
        "## Core Paths\n\n"
        "- Home: `00_home/home.md`\n"
        "- Operating layer: `01_system/`\n"
        "- Private knowledge layer: `20_wiki/`\n"
        "- Private outputs: `30_outputs/`\n"
        "- Private workspace: `40_workspace/`\n"
        "- Archive: `90_archive/`\n"
    )
    index_path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Read shared Team Sources artifacts and maintain the private User Wiki.")
    parser.add_argument("--shared-vault", required=True)
    parser.add_argument("--private-vault", required=True)
    parser.add_argument("--state-file", required=True)
    parser.add_argument("--shared-vault-name", default="Team Sources")
    args = parser.parse_args()

    shared_vault = Path(args.shared_vault).expanduser().resolve()
    private_vault = Path(args.private_vault).expanduser().resolve()
    state_file = Path(args.state_file).expanduser().resolve()

    if private_vault == shared_vault or str(private_vault).startswith(str(shared_vault)):
        raise RuntimeError("private vault must not be the shared vault or nested inside it")

    source_registry = read_jsonl(shared_vault / "12_indices/source-registry.jsonl", "source_id")
    public_registry = read_jsonl(shared_vault / "12_indices/public-wiki-registry.jsonl", "shared_wiki_id")
    state = load_json(state_file, {"artifacts": {}, "last_run_at": None})
    artifacts = state.setdefault("artifacts", {})

    log_entries: list[str] = []
    processed_sources = 0
    processed_public = 0

    related_public_map: dict[str, list[dict]] = {}
    for record in public_registry.values():
        for item in record.get("derived_from", []):
            if isinstance(item, str):
                continue
            source_id = item.get("source_id")
            if source_id:
                related_public_map.setdefault(source_id, []).append(record)

    for source_id, record in sorted(source_registry.items()):
        artifact_key = f"source:{source_id}"
        content_hash = record.get("content_hash")
        if artifacts.get(artifact_key, {}).get("content_hash") == content_hash:
            continue
        shared_note_path = shared_vault / record["normalized_path"]
        frontmatter, body = read_markdown(shared_note_path)
        title = frontmatter.get("title") or record.get("title") or source_id
        record["title"] = title
        summary = extract_summary(body)
        related_public = sorted(related_public_map.get(source_id, []), key=lambda item: item.get("shared_wiki_id", ""))
        target_slug = slugify(str(title))
        target_rel = Path("20_wiki") / SOURCE_FOLDER_MAP.get(record.get("domain", "process"), "sources") / f"{source_id}-{target_slug}.md"
        target_path = private_vault / target_rel
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(
            source_note_content(record, record["normalized_path"], summary, related_public, args.shared_vault_name),
            encoding="utf-8",
        )
        artifacts[artifact_key] = {
            "artifact_type": "source",
            "content_hash": content_hash,
            "private_path": target_rel.as_posix(),
            "processed_at": now_iso(),
        }
        log_entries.append(f"- {now_iso()}: ingested source `{source_id}` into `{target_rel.as_posix()}`.\n")
        processed_sources += 1

    for shared_wiki_id, record in sorted(public_registry.items()):
        artifact_key = f"shared_wiki:{shared_wiki_id}"
        content_hash = record.get("content_hash")
        if artifacts.get(artifact_key, {}).get("content_hash") == content_hash:
            continue
        shared_note_path = shared_vault / record["path"]
        frontmatter, body = read_markdown(shared_note_path)
        title = frontmatter.get("title") or record.get("title") or shared_wiki_id
        record["title"] = title
        page_type = frontmatter.get("shared_wiki_type") or record.get("shared_wiki_type") or "concept"
        target_folder = PUBLIC_FOLDER_MAP.get(str(page_type), "syntheses")
        target_slug = slugify(str(title))
        target_rel = Path("20_wiki") / target_folder / f"{shared_wiki_id}-{target_slug}.md"
        target_path = private_vault / target_rel
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(public_note_content(record, frontmatter, body, args.shared_vault_name), encoding="utf-8")
        artifacts[artifact_key] = {
            "artifact_type": "shared_wiki",
            "content_hash": content_hash,
            "private_path": target_rel.as_posix(),
            "processed_at": now_iso(),
        }
        log_entries.append(f"- {now_iso()}: ingested team ground truth `{shared_wiki_id}` into `{target_rel.as_posix()}`.\n")
        processed_public += 1

    state["last_run_at"] = now_iso()
    dump_json(state_file, state)
    update_system_index(private_vault, len(source_registry), len(public_registry))
    if log_entries:
        append_log(private_vault / "01_system/log.md", log_entries)

    print(f"Done. sources_updated={processed_sources} public_updated={processed_public}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
