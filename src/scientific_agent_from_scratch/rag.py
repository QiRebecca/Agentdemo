from __future__ import annotations

import re
from typing import Any


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9_]+", text.lower()))


def keyword_score(query: str, document_text: str) -> int:
    return len(tokenize(query) & tokenize(document_text))


def _stable_key(record: dict[str, Any]) -> str:
    for key in ("id", "name", "path", "memory_id"):
        if key in record:
            return str(record[key])
    return str(record)


def retrieve(
    query: str,
    records: list[dict[str, Any]],
    text_fields: list[str],
    top_k: int,
) -> list[dict[str, Any]]:
    scored = []
    for record in records:
        text = " ".join(str(record.get(field, "")) for field in text_fields)
        score = keyword_score(query, text)
        if score > 0:
            item = dict(record)
            item["score"] = score
            scored.append(item)
    scored.sort(key=lambda item: (-item["score"], _stable_key(item)))
    return scored[:top_k]
