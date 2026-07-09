"""Normalize Decidim Open Data exports into contribution JSONL."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import re
from dataclasses import asdict, dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from zipfile import ZipFile


class _HTMLStripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def text(self) -> str:
        return " ".join(part.strip() for part in self.parts if part.strip())


@dataclass
class Contribution:
    source: str
    source_file: str
    source_id: str
    contribution_type: str
    title: str | None = None
    body: str | None = None
    author: str | None = None
    url: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    locale: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def strip_html(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    if not text:
        return None
    stripper = _HTMLStripper()
    stripper.feed(text)
    stripped = stripper.text() or text
    return re.sub(r"\s+", " ", html.unescape(stripped)).strip() or None


def _clean_row(row: dict[str, Any]) -> dict[str, str]:
    return {str(k).strip(): "" if v is None else str(v).strip() for k, v in row.items()}


def _pick(row: dict[str, str], *names: str) -> str | None:
    lower = {key.lower(): value for key, value in row.items()}
    for name in names:
        value = lower.get(name.lower())
        if value:
            return value
    return None


def _type_from_name(name: str) -> str:
    stem = Path(name).stem.lower()
    for kind in (
        "proposal",
        "comment",
        "meeting",
        "debate",
        "result",
        "project",
        "accountability",
        "budget",
        "survey",
    ):
        if kind in stem:
            return kind
    return stem.replace("-", "_")


def _stable_id(source_file: str, row: dict[str, str]) -> str:
    native = _pick(row, "id", "proposal_id", "comment_id", "resource_id", "gid")
    if native:
        return native
    digest = hashlib.sha256(
        json.dumps(row, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return f"{Path(source_file).stem}:{digest[:16]}"


def row_to_contribution(source_file: str, row: dict[str, Any]) -> Contribution | None:
    clean = _clean_row(row)
    title = strip_html(_pick(clean, "title", "name", "subject"))
    body = strip_html(
        _pick(
            clean,
            "body",
            "description",
            "comment",
            "comments",
            "text",
            "answer",
            "closing_report",
            "summary",
        )
    )
    if not title and not body:
        return None
    return Contribution(
        source="decidim",
        source_file=source_file,
        source_id=_stable_id(source_file, clean),
        contribution_type=_type_from_name(source_file),
        title=title,
        body=body,
        author=_pick(clean, "author", "author_name", "user_name", "nickname", "creator"),
        url=_pick(clean, "url", "resource_url", "reference_url"),
        created_at=_pick(clean, "created_at", "published_at", "start_time", "created"),
        updated_at=_pick(clean, "updated_at", "updated"),
        locale=_pick(clean, "locale", "language"),
        metadata={k: v for k, v in clean.items() if v},
    )


def normalize_open_data_zip(zip_path: Path, out_path: Path) -> dict[str, Any]:
    contributions: list[Contribution] = []
    seen: set[tuple[str, str]] = set()
    with ZipFile(zip_path) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            name = info.filename
            suffix = Path(name).suffix.lower()
            if suffix == ".csv":
                with zf.open(info) as raw:
                    text = raw.read().decode("utf-8-sig", errors="replace").splitlines()
                for row in csv.DictReader(text):
                    contribution = row_to_contribution(name, row)
                    if not contribution:
                        continue
                    key = (contribution.source_file, contribution.source_id)
                    if key not in seen:
                        seen.add(key)
                        contributions.append(contribution)
            elif suffix == ".json":
                with zf.open(info) as raw:
                    payload = json.loads(raw.read().decode("utf-8-sig", errors="replace"))
                rows = payload if isinstance(payload, list) else payload.get("data", [])
                if isinstance(rows, list):
                    for row in rows:
                        if isinstance(row, dict):
                            contribution = row_to_contribution(name, row)
                            if contribution:
                                key = (contribution.source_file, contribution.source_id)
                                if key not in seen:
                                    seen.add(key)
                                    contributions.append(contribution)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for contribution in contributions:
            f.write(json.dumps(asdict(contribution), ensure_ascii=False) + "\n")
    counts: dict[str, int] = {}
    for contribution in contributions:
        counts[contribution.contribution_type] = counts.get(contribution.contribution_type, 0) + 1
    return {"input": str(zip_path), "output": str(out_path), "count": len(contributions), "by_type": counts}

