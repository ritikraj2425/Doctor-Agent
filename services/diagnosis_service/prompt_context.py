"""Keep retrieved evidence compact when building model prompts."""

import re


def compact_text(value: str | None, limit: int) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= limit:
        return text
    marker = " … [middle excerpt shortened] … "
    content_limit = max(0, limit - len(marker))
    head_size = (content_limit * 2) // 3
    tail_size = content_limit - head_size
    head = text[:head_size].rsplit(" ", 1)[0]
    tail = text[-tail_size:].lstrip()
    return head + marker + tail


def compact_sources(results: list[dict] | None, *, count: int = 3, excerpt_chars: int = 1000) -> list[dict]:
    """Drop full-page/raw payloads and pass only short, cited source excerpts to the LLM."""
    compacted = []
    for result in (results or [])[:count]:
        if not isinstance(result, dict):
            continue
        metadata = result.get("metadata") or {}
        if not isinstance(metadata, dict):
            metadata = {}
        item = {}
        for key in ("title", "url"):
            value = result.get(key)
            if value:
                item[key] = compact_text(str(value), 240)
        source = result.get("source") or metadata.get("source") or metadata.get("filename")
        if source:
            item["source"] = compact_text(str(source), 180)
        page = metadata.get("page")
        if page is not None:
            item["page"] = page
        text = result.get("content") or result.get("raw_content") or result.get("snippet") or ""
        item["excerpt"] = compact_text(text, excerpt_chars)
        if item.get("excerpt") or item.get("title") or item.get("source"):
            compacted.append(item)
    return compacted
