#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


try:
    from markitdown import MarkItDown
except ImportError:  # pragma: no cover - optional dependency
    MarkItDown = None


INBOX_DIRS = {"product", "research", "meeting", "misc"}
DOMAIN_DIR_MAP = {
    "product": "product",
    "research": "research",
    "meeting": "process",
    "misc": "process",
}
DOMAIN_CODE_MAP = {
    "product": "PRO",
    "engineering": "ENG",
    "research": "RES",
    "process": "PRC",
}
PUBLIC_TYPE_CODE_MAP = {
    "decision": "DEC",
    "concept": "CON",
    "glossary": "GLS",
    "map": "MAP",
}
TEXT_SUFFIXES = {".md", ".markdown", ".txt"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}


@dataclass
class ConversionResult:
    markdown: str
    title: str
    preserve_original: bool
    warnings: list[str]


def now_iso() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def file_iso(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).astimezone().replace(microsecond=0).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def slugify(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = re.sub(r"-{2,}", "-", lowered).strip("-")
    return lowered or "untitled"


def escape_yaml(value: str) -> str:
    escaped = value.replace('"', '\\"')
    return f'"{escaped}"'


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dump_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def read_jsonl(path: Path, key: str) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return records
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            record = json.loads(line)
            if record.get(key):
                records[record[key]] = record
    return records


def write_jsonl(path: Path, records: dict[str, dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record_key in sorted(records):
            handle.write(json.dumps(records[record_key], ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def compute_fingerprint(path: Path) -> str:
    stat = path.stat()
    basis = f"{path.name}:{stat.st_size}:{int(stat.st_mtime)}"
    content_hash = sha256_bytes(path.read_bytes())
    return sha256_text(f"{basis}:{content_hash}")


def detect_title(path: Path, text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return path.stem.replace("_", " ").replace("-", " ").strip() or path.stem


def convert_file(path: Path) -> ConversionResult:
    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown"}:
        text = path.read_text(encoding="utf-8", errors="replace")
        return ConversionResult(markdown=text, title=detect_title(path, text), preserve_original=False, warnings=[])

    if suffix == ".txt":
        text = path.read_text(encoding="utf-8", errors="replace")
        markdown = f"# {path.stem}\n\n{text.strip()}\n"
        return ConversionResult(markdown=markdown, title=path.stem, preserve_original=False, warnings=[])

    if suffix in IMAGE_SUFFIXES:
        markdown = f"# {path.stem}\n\n_Image source preserved as an attachment._\n"
        return ConversionResult(markdown=markdown, title=path.stem, preserve_original=True, warnings=["image-preserved"])

    if MarkItDown is None:
        raise RuntimeError("markitdown is not installed; run scripts/install_admin_runtime.sh")

    converter = MarkItDown()
    result = converter.convert(str(path))
    text_content = getattr(result, "text_content", None) or ""
    title = getattr(result, "title", None) or detect_title(path, text_content) or path.stem
    if not text_content.strip():
        raise RuntimeError("conversion returned empty content")
    markdown = text_content.strip() + "\n"
    return ConversionResult(markdown=markdown, title=title, preserve_original=True, warnings=[])


def source_frontmatter(
    source_id: str,
    title: str,
    source_type: str,
    domain: str,
    origin_rel: str,
    origin_name: str,
    origin_modified_at: str,
    normalized_at: str,
    content_hash: str,
    attachments: list[str],
    warnings: list[str],
) -> str:
    attachment_block = "attachments: []\n" if not attachments else "attachments:\n" + "\n".join(f"  - {item}" for item in attachments) + "\n"
    tag_items = [f"{domain}/{source_type}"] + warnings
    tag_lines = "\n".join(f"  - {item}" for item in tag_items)
    return (
        "---\n"
        f"source_id: {source_id}\n"
        f"title: {escape_yaml(title)}\n"
        f"source_type: {source_type}\n"
        f"domain: {domain}\n"
        "status: canonical\n"
        f"origin_path: {escape_yaml(origin_rel)}\n"
        f"origin_filename: {escape_yaml(origin_name)}\n"
        f"origin_modified_at: {origin_modified_at}\n"
        f"normalized_at: {normalized_at}\n"
        "normalized_by: source-curator\n"
        f"content_hash: sha256:{content_hash}\n"
        f"{attachment_block}"
        "tags:\n"
        f"{tag_lines}\n"
        "---\n\n"
    )


def public_wiki_frontmatter(
    shared_wiki_id: str,
    title: str,
    note_type: str,
    domain: str,
    derived_from: list[str],
    content_hash: str,
) -> str:
    derived_block = "derived_from: []\n" if not derived_from else "derived_from:\n" + "\n".join(f"  - source_id: {source_id}" for source_id in derived_from) + "\n"
    consensus_strength = "explicit" if note_type == "decision" else "strong"
    tags = {
        "decision": ["ground-truth/decision"],
        "concept": ["ground-truth/concept"],
        "glossary": ["ground-truth/glossary"],
        "map": ["ground-truth/map"],
    }[note_type]
    tag_lines = "\n".join(f"  - {tag}" for tag in tags)
    return (
        "---\n"
        f"shared_wiki_id: {shared_wiki_id}\n"
        f"title: {escape_yaml(title)}\n"
        f"shared_wiki_type: {note_type}\n"
        f"domain: {domain}\n"
        "status: active\n"
        f"consensus_strength: {consensus_strength}\n"
        "maintained_by: source-curator\n"
        f"{derived_block}"
        f"last_reviewed_at: {now_iso()}\n"
        f"content_hash: sha256:{content_hash}\n"
        "tags:\n"
        f"{tag_lines}\n"
        "---\n\n"
    )


def extract_shared_wiki_candidates(text: str) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    current_section = ""
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        heading = re.match(r"^#{1,6}\s+(.*)$", line)
        if heading:
            lowered = heading.group(1).strip().lower()
            if "decision" in lowered:
                current_section = "decision"
            elif "concept" in lowered:
                current_section = "concept"
            elif "glossary" in lowered or "term" in lowered:
                current_section = "glossary"
            else:
                current_section = ""
            continue

        for note_type, label in (("decision", "Decision"), ("concept", "Concept")):
            direct = re.match(rf"^(?:[-*]\s+)?{label}:\s+(.+)$", line, re.IGNORECASE)
            if direct:
                candidates.append({"type": note_type, "title": direct.group(1).strip(), "statement": direct.group(1).strip()})
                break
        else:
            if current_section in {"decision", "concept"}:
                bullet = re.match(r"^(?:[-*]|\d+\.)\s+(.+)$", line)
                if bullet:
                    statement = bullet.group(1).strip()
                    candidates.append({"type": current_section, "title": statement, "statement": statement})
                    continue
            if current_section == "glossary":
                glossary = re.match(r"^(?:[-*]\s+)?([^:]{2,}):\s+(.+)$", line)
                if glossary:
                    term = glossary.group(1).strip()
                    definition = glossary.group(2).strip()
                    candidates.append({"type": "glossary", "title": term, "statement": definition})
    return candidates


def next_source_id(state: dict[str, Any], domain: str, year: str) -> str:
    seq = int(state.get("next_source_seq", 1))
    state["next_source_seq"] = seq + 1
    return f"SRC-{DOMAIN_CODE_MAP[domain]}-{year}-{seq:04d}"


def next_public_id(state: dict[str, Any], note_type: str, year: str) -> str:
    seq = int(state.get("next_public_seq", 1))
    state["next_public_seq"] = seq + 1
    return f"GT-{PUBLIC_TYPE_CODE_MAP[note_type]}-{year}-{seq:04d}"


def write_text(path: Path, content: str, dry_run: bool) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def copy_file(source: Path, target: Path, dry_run: bool) -> None:
    if dry_run:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def build_source_body(
    title: str,
    converted_markdown: str,
    origin_rel: str,
    warnings: list[str],
    attachments: list[str],
    source_note_path: Path,
    vault_path: Path,
) -> str:
    sections = [f"# {title}", "", "## Content", "", converted_markdown.strip(), ""]
    if attachments:
        sections.extend(["## Attachments", ""])
        for item in attachments:
            attachment_path = vault_path / item
            relative_link = Path(os.path.relpath(attachment_path, start=source_note_path.parent))
            sections.append(f"- [{Path(item).name}]({relative_link.as_posix()})")
        sections.append("")
    sections.extend(["## Source Trace", "", f"- Original file: `{origin_rel}`"])
    if warnings:
        sections.append(f"- Conversion notes: {', '.join(warnings)}")
    else:
        sections.append("- Conversion notes: none")
    sections.append("- Lossy areas: review if the original file had complex layout or embedded attachments")
    sections.append("")
    return "\n".join(sections)


def build_public_body(title: str, statement: str, source_id: str, domain: str, source_rel: str) -> str:
    source_uri = f"obsidian://open?vault=Team%20Sources&file={source_rel.replace('/', '%2F').replace(' ', '%20').replace('.md', '')}"
    return (
        f"# {title}\n\n"
        "## Canonical Statement\n\n"
        f"{statement}\n\n"
        "## Rationale\n\n"
        "Promoted from the shared evidence layer because the statement was explicit or strongly repeated.\n\n"
        "## Evidence\n\n"
        f"- source_id: {source_id}\n"
        f"- source_link: {source_uri}\n\n"
        "## Change Log\n\n"
        f"- reviewed_at: {now_iso()}\n"
        f"- change_summary: refreshed from `{domain}` evidence\n"
    )


def process_one(
    inbox_file: Path,
    vault_path: Path,
    state: dict[str, Any],
    source_registry: dict[str, dict[str, Any]],
    public_registry: dict[str, dict[str, Any]],
    default_year: str,
    dry_run: bool,
) -> dict[str, Any]:
    inbox_rel = inbox_file.relative_to(vault_path).as_posix()
    fingerprint = compute_fingerprint(inbox_file)
    processed = state.setdefault("processed", {})
    existing_state = processed.get(inbox_rel)
    source_id = existing_state.get("source_id") if existing_state else None

    inbox_rel_parts = inbox_file.relative_to(vault_path).parts
    inbox_category = inbox_rel_parts[1] if len(inbox_rel_parts) > 1 else "misc"
    domain = DOMAIN_DIR_MAP.get(inbox_category, "process")
    source_type = inbox_category if inbox_category in INBOX_DIRS else "misc"
    year = default_year

    conversion = convert_file(inbox_file)
    if not source_id:
        source_id = next_source_id(state, domain, year)

    slug = slugify(inbox_file.stem)
    source_rel = f"10_sources/{domain}/{source_id}-{slug}.md"
    source_note_path = vault_path / source_rel
    attachments: list[str] = []

    if conversion.preserve_original:
        original_name = f"original{inbox_file.suffix.lower()}"
        asset_rel = f"11_assets/{source_id}/{original_name}"
        attachments.append(asset_rel)
        copy_file(inbox_file, vault_path / asset_rel, dry_run)
        if inbox_file.suffix.lower() in IMAGE_SUFFIXES:
            relative_link = Path(os.path.relpath(vault_path / asset_rel, start=source_note_path.parent)).as_posix()
            conversion.markdown = f"{conversion.markdown.strip()}\n\n![{inbox_file.stem}]({relative_link})\n"

    body = build_source_body(
        title=conversion.title,
        converted_markdown=conversion.markdown,
        origin_rel=inbox_rel,
        warnings=conversion.warnings,
        attachments=attachments,
        source_note_path=source_note_path,
        vault_path=vault_path,
    )
    content_hash = sha256_text(body)
    frontmatter = source_frontmatter(
        source_id=source_id,
        title=conversion.title,
        source_type=source_type,
        domain=domain,
        origin_rel=inbox_rel,
        origin_name=inbox_file.name,
        origin_modified_at=file_iso(inbox_file),
        normalized_at=now_iso(),
        content_hash=content_hash,
        attachments=attachments,
        warnings=conversion.warnings,
    )
    write_text(source_note_path, frontmatter + body, dry_run)

    source_registry[source_id] = {
        "content_hash": f"sha256:{content_hash}",
        "domain": domain,
        "normalized_path": source_rel,
        "origin_path": inbox_rel,
        "source_id": source_id,
        "source_type": source_type,
        "status": "canonical",
        "title": conversion.title,
        "updated_at": now_iso(),
    }

    public_candidates = extract_shared_wiki_candidates(conversion.markdown)
    generated_public_ids: list[str] = []
    existing_by_slug = {
        (record.get("shared_wiki_type"), record.get("slug")): record
        for record in public_registry.values()
    }
    for candidate in public_candidates:
        note_type = candidate["type"]
        title = candidate["title"]
        statement = candidate["statement"]
        public_slug = slugify(title)
        existing_public = existing_by_slug.get((note_type, public_slug))
        shared_wiki_id = existing_public["shared_wiki_id"] if existing_public else next_public_id(state, note_type, year)
        public_rel = f"20_public_wiki/{note_type}s/{shared_wiki_id}-{public_slug}.md" if note_type != "glossary" else f"20_public_wiki/glossary/{shared_wiki_id}-{public_slug}.md"
        public_path = vault_path / public_rel
        public_body = build_public_body(title, statement, source_id, domain, source_rel)
        public_hash = sha256_text(public_body)
        public_frontmatter = public_wiki_frontmatter(
            shared_wiki_id=shared_wiki_id,
            title=title,
            note_type=note_type,
            domain=domain,
            derived_from=[source_id],
            content_hash=public_hash,
        )
        write_text(public_path, public_frontmatter + public_body, dry_run)
        public_registry[shared_wiki_id] = {
            "content_hash": f"sha256:{public_hash}",
            "derived_from": [source_id],
            "domain": domain,
            "path": public_rel,
            "shared_wiki_id": shared_wiki_id,
            "shared_wiki_type": note_type,
            "slug": public_slug,
            "status": "active",
            "title": title,
            "updated_at": now_iso(),
        }
        generated_public_ids.append(shared_wiki_id)

    processed[inbox_rel] = {
        "fingerprint": fingerprint,
        "generated_public_ids": generated_public_ids,
        "source_id": source_id,
        "source_rel": source_rel,
    }

    return {
        "generated_public_ids": generated_public_ids,
        "source_id": source_id,
        "source_rel": source_rel,
        "title": conversion.title,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Curate raw inbox files into canonical sources and shared public wiki notes.")
    parser.add_argument("--vault", required=True, help="Path to the Team Sources vault")
    parser.add_argument("--state-dir", required=True, help="Path to local curator state")
    parser.add_argument("--default-year", default=datetime.now().strftime("%Y"), help="Year used in generated IDs")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without writing files")
    args = parser.parse_args()

    vault_path = Path(args.vault).expanduser().resolve()
    state_dir = Path(args.state_dir).expanduser().resolve()
    state_path = state_dir / "curator-state.json"
    source_registry_path = vault_path / "12_indices/source-registry.jsonl"
    public_registry_path = vault_path / "12_indices/public-wiki-registry.jsonl"

    state = load_json(state_path, {"next_source_seq": 1, "next_public_seq": 1, "processed": {}})
    source_registry = read_jsonl(source_registry_path, "source_id")
    public_registry = read_jsonl(public_registry_path, "shared_wiki_id")

    inbox_files = sorted(
        path
        for path in (vault_path / "00_inbox").rglob("*")
        if path.is_file() and not path.name.startswith(".")
    )

    processed_count = 0
    skipped_count = 0
    for inbox_file in inbox_files:
        inbox_rel = inbox_file.relative_to(vault_path).as_posix()
        fingerprint = compute_fingerprint(inbox_file)
        existing_state = state.get("processed", {}).get(inbox_rel)
        if existing_state and existing_state.get("fingerprint") == fingerprint:
            skipped_count += 1
            continue
        result = process_one(
            inbox_file=inbox_file,
            vault_path=vault_path,
            state=state,
            source_registry=source_registry,
            public_registry=public_registry,
            default_year=args.default_year,
            dry_run=args.dry_run,
        )
        processed_count += 1
        print(f"Curated {inbox_rel} -> {result['source_rel']}")
        if result["generated_public_ids"]:
            print(f"  public wiki: {', '.join(result['generated_public_ids'])}")

    if not args.dry_run:
        dump_json(state_path, state)
        write_jsonl(source_registry_path, source_registry)
        write_jsonl(public_registry_path, public_registry)

    print(f"Done. processed={processed_count} skipped={skipped_count} dry_run={args.dry_run}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
