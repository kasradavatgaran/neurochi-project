import html
import json
import math
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from sqlalchemy.orm import Session

import models


CHAT_HISTORY_MAX_TOKENS = max(100, int(os.getenv("CHAT_HISTORY_MAX_TOKENS", "6000")))
CHAT_CONTEXT_MAX_TOKENS = max(500, int(os.getenv("CHAT_CONTEXT_MAX_TOKENS", "12000")))
CHAT_SUMMARY_TRIGGER_TOKENS = max(500, int(os.getenv("CHAT_SUMMARY_TRIGGER_TOKENS", "5000")))
CHAT_RECENT_TURNS = max(1, int(os.getenv("CHAT_RECENT_TURNS", "8")))
RAG_MAX_SOURCES = max(1, int(os.getenv("RAG_MAX_SOURCES", "5")))


def estimate_tokens(value: str) -> int:
    """Conservative, dependency-free estimate for Persian and Latin text."""
    return max(1, math.ceil(len(str(value or "")) / 3.0))


def load_sources_json(value: Optional[str]) -> list[dict]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return []
    return parsed if isinstance(parsed, list) else []


def dump_sources_json(sources: list[dict]) -> str:
    return json.dumps(sources or [], ensure_ascii=False)


def normalize_source(source: dict) -> dict:
    normalized = {
        "title": str(source.get("title") or "").strip(),
        "source_name": str(source.get("source_name") or source.get("source") or "").strip(),
        "url": str(source.get("url") or "").strip(),
    }
    for key in ("content", "source_file", "chunk_index", "chunk_count"):
        if source.get(key) not in (None, ""):
            normalized[key] = source[key]
    return normalized


def dedupe_sources(sources: list[dict]) -> list[dict]:
    result = []
    seen = set()
    for source in sources:
        normalized = normalize_source(source)
        if not normalized["title"] and not normalized["source_name"] and not normalized["url"]:
            continue
        key = (
            normalized["url"].lower(),
            normalized["title"].casefold(),
            normalized["source_name"].casefold(),
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(normalized)
    return result[:RAG_MAX_SOURCES]


def source_records_from_documents(documents: list) -> list[dict]:
    records = []
    for doc in documents or []:
        metadata = doc.metadata or {}
        title = str(metadata.get("title") or Path(str(metadata.get("source_file") or "")).stem).strip()
        source_name = str(
            metadata.get("source_name")
            or metadata.get("source")
            or metadata.get("url")
            or "آرشیو محلی"
        ).strip()
        if not source_name or "Ù†Ø§Ù…Ø´Ø®Øµ" in source_name or "نامشخص" in source_name:
            source_name = Path(str(metadata.get("source_file") or "")).stem.strip() or "آرشیو محلی"
        chunk_text = str(getattr(doc, "page_content", "") or "").strip()
        if "\n\n" in chunk_text:
            chunk_text = chunk_text.split("\n\n", 1)[1].strip()
        records.append({
            "title": title,
            "source_name": source_name,
            "url": str(metadata.get("url") or "").strip(),
            "content": chunk_text,
            "source_file": str(metadata.get("source_file") or "").strip(),
            "chunk_index": metadata.get("chunk_index"),
            "chunk_count": metadata.get("chunk_count"),
        })
    return dedupe_sources(records)


def _strip_tags(value: str) -> str:
    value = re.sub(r"<br\s*/?>", "\n", value or "", flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", "", value)
    return html.unescape(value).strip()


def _source_from_anchor(match: re.Match, tail: str) -> dict:
    attrs = match.group("attrs") or ""
    href_match = re.search(r"\bhref\s*=\s*[\"']([^\"']+)[\"']", attrs, flags=re.IGNORECASE)
    url = html.unescape(href_match.group(1)).strip() if href_match else ""
    return {
        "title": _strip_tags(match.group("label")),
        "source_name": urlparse(url).netloc.lower().removeprefix("www.") if url else "",
        "url": url,
    }


def extract_legacy_sources(raw_text: str) -> tuple[str, list[dict]]:
    """Extract old HTML/plain citations and return clean body plus structured sources."""
    raw = str(raw_text or "")
    if not raw:
        return "", []

    sources = []
    source_start = None
    anchor_pattern = re.compile(
        r"<a\b(?P<attrs>[^>]*class\s*=\s*[\"'][^\"']*rag-source-link[^\"']*[\"'][^>]*)>"
        r"(?P<label>.*?)</a>",
        flags=re.IGNORECASE | re.DOTALL,
    )
    anchors = list(anchor_pattern.finditer(raw))
    if anchors:
        source_start = min(match.start() for match in anchors)
        for match in anchors:
            source = _source_from_anchor(match, raw[match.end():])
            after = raw[match.end():]
            site_match = re.search(
                r'class\s*=\s*["\'][^"\']*rag-source-site[^"\']*["\'][^>]*>(.*?)</(?:bdi|span)>',
                after,
                flags=re.IGNORECASE | re.DOTALL,
            )
            if site_match:
                source["source_name"] = _strip_tags(site_match.group(1))
            else:
                plain_after = _strip_tags(after)
                plain_after = re.split(r"[)\n|]", plain_after, maxsplit=1)[0]
                plain_after = plain_after.replace("،", "").replace(",", "").strip(" -")
                source["source_name"] = plain_after
            sources.append(source)

    citation_match = re.search(r"<span\b[^>]*rag-source-citation", raw, flags=re.IGNORECASE)
    if citation_match:
        source_start = citation_match.start() if source_start is None else min(source_start, citation_match.start())

    plain_match = re.search(
        r"(?P<tail>(?:\([^()\n]{1,200}[،,]\s*[^()\n]{1,200}\)\s*)+)$",
        raw,
        flags=re.DOTALL,
    )
    if plain_match:
        source_start = plain_match.start() if source_start is None else min(source_start, plain_match.start())
        for item in re.finditer(r"\((?P<title>[^()\n]{1,200})[،,]\s*(?P<source>[^()\n]{1,200})\)", plain_match.group("tail")):
            sources.append({
                "title": item.group("title").strip(),
                "source_name": item.group("source").strip(),
                "url": "",
            })

    markdown_match = re.search(r"(?P<tail>(?:\[[^\]]+\]\(https?://[^)]+\)\s*)+)$", raw, flags=re.IGNORECASE)
    if markdown_match:
        source_start = markdown_match.start() if source_start is None else min(source_start, markdown_match.start())
        for item in re.finditer(r"\[(?P<title>[^\]]+)\]\((?P<url>https?://[^)]+)\)", markdown_match.group("tail"), flags=re.IGNORECASE):
            url = item.group("url").strip()
            sources.append({
                "title": item.group("title"),
                "source_name": urlparse(url).netloc.lower().removeprefix("www."),
                "url": url,
            })

    if source_start is None:
        return raw, []

    body = raw[:source_start]
    body = _strip_tags(body).strip()
    return body, dedupe_sources(sources)


def sources_to_legacy_html(sources: list[dict]) -> str:
    """Compatibility output for older clients; new clients use structured sources."""
    parts = []
    for source in dedupe_sources(sources):
        title = html.escape(source["title"] or source["source_name"])
        site = html.escape(source["source_name"] or source["url"])
        if source["url"]:
            href = html.escape(source["url"], quote=True)
            title = f'<a class="rag-source-link" href="{href}" target="_blank" rel="noopener noreferrer"><bdi>{title}</bdi></a>'
        parts.append(
            '<span class="rag-source-citation" dir="rtl">'
            f'({title}<span class="rag-source-separator">،</span> '
            f'<bdi class="rag-source-site" dir="auto">{site}</bdi>)</span>'
        )
    return " | ".join(parts)


def get_or_create_chat_session(
    db: Session,
    user_id: int,
    child_id: Optional[int],
    session_id: Optional[int] = None,
    title: Optional[str] = None,
) -> models.ChatSession:
    scope_filter = (
        models.ChatSession.child_id.is_(None)
        if child_id is None
        else models.ChatSession.child_id == child_id
    )
    session = None
    if session_id is not None:
        session = db.query(models.ChatSession).filter(
            models.ChatSession.id == session_id,
            models.ChatSession.user_id == user_id,
            scope_filter,
        ).first()
        if not session:
            raise ValueError("Chat session not found")
    else:
        session = db.query(models.ChatSession).filter(
            models.ChatSession.user_id == user_id,
            scope_filter,
        ).order_by(models.ChatSession.updated_at.desc(), models.ChatSession.id.desc()).first()

    if not session:
        session = models.ChatSession(
            user_id=user_id,
            child_id=child_id,
            title=title or "گفتگوی جدید",
        )
        db.add(session)
        db.flush()
    return session


def serialize_chat_session(session: models.ChatSession, db: Session) -> dict:
    return {
        "id": session.id,
        "child_id": session.child_id,
        "title": session.title,
        "summary_text": session.summary_text,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "message_count": db.query(models.ChatMessage).filter(
            models.ChatMessage.session_id == session.id
        ).count(),
    }
