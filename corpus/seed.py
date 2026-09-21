"""Nạp một lần corpus giả lập đi kèm bản triển khai mới."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, replace
from pathlib import Path

from infra.db import execute, fetch_one, now_iso

SEED_DOCUMENTS_DIRECTORY = Path(__file__).parents[1] / "data" / "seed_docs"
EXPECTED_DOCUMENT_COUNT = 6
EXPECTED_CHUNK_COUNT = 72
ARTICLE_PATTERN = re.compile(r"^Điều\s+(\d+)\.", re.IGNORECASE)
CLAUSE_PATTERN = re.compile(r"^Khoản\s+(\d+)\.", re.IGNORECASE)
POINT_PATTERN = re.compile(r"^Điểm\s+([a-zđ])\)", re.IGNORECASE)
REFUND_CONFLICT_DOCUMENTS = frozenset({"RH-2026-101", "HP-2026-1"})
REFUND_CONFLICT_ARTICLE = "3"
REFUND_CONFLICT_CHUNK_COUNT = 6


@dataclass(frozen=True)
class SeedResult:
    seeded: bool
    document_count: int
    chunk_count: int


@dataclass(frozen=True)
class _SeedChunk:
    chunk_id: str
    doc_id: str
    article_no: str
    clause_no: str | None
    breadcrumb: str
    text: str
    domain: str
    label: str
    ordinal: int
    conflict_flag: bool = False
    conflict_with: str | None = None


def ensure_seeded(*, database_path: str | Path | None = None) -> SeedResult:
    """Nạp seed chỉ khi chưa có nguồn nào; không ghi đè corpus do admin quản trị."""
    if fetch_one("SELECT doc_id FROM sources LIMIT 1", database_path=database_path) is not None:
        return SeedResult(False, 0, 0)

    documents = [_read_document(path) for path in sorted(SEED_DOCUMENTS_DIRECTORY.glob("*.json"))]
    if len(documents) != EXPECTED_DOCUMENT_COUNT:
        raise RuntimeError("Bộ corpus seed phải có đúng sáu tài liệu.")

    chunks = [chunk for document in documents for chunk in _document_chunks(document)]
    if len(chunks) != EXPECTED_CHUNK_COUNT:
        raise RuntimeError("Số chunk seed không khớp với corpus đã kiểm thử.")

    _insert_sources(documents, database_path=database_path)
    _insert_chunks(_with_refund_conflicts(chunks), database_path=database_path)
    return SeedResult(True, len(documents), len(chunks))


def _read_document(path: Path) -> dict[str, object]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError(f"Seed {path.name} phải là object JSON.")
    return _normalise_document(document)


def _normalise_document(document: dict[str, object]) -> dict[str, object]:
    return {
        key: unicodedata.normalize("NFC", value) if isinstance(value, str) else value
        for key, value in document.items()
    }


def _insert_sources(
    documents: list[dict[str, object]], *, database_path: str | Path | None
) -> None:
    created_at = now_iso()
    for document in documents:
        text = _string(document, "text")
        status = _string(document, "status")
        if not _boolean(document, "is_synthetic"):
            raise ValueError("Mọi seed phải được đánh dấu is_synthetic: true.")
        execute(
            """
            INSERT INTO sources (
                doc_id, title, issuer, source_kind, sha256, is_synthetic, published_at,
                effective_from, effective_to, applies_to_json, cohorts_json, domains_json,
                supersedes_json, transitional_clause, status, content_hash, created_at,
                activated_at, activated_by
            ) VALUES (?, ?, ?, 'seed', ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _string(document, "document_id"),
                _string(document, "title"),
                _string(document, "issuer"),
                hashlib.sha256(text.encode("utf-8")).hexdigest(),
                _optional_string(document, "published_at"),
                _string(document, "effective_from"),
                _optional_string(document, "effective_to"),
                _json_value(document, "applies_to"),
                _json_value(document, "cohorts"),
                _json_value(document, "domains"),
                _json_value(document, "supersedes"),
                int(_boolean(document, "transitional_clause")),
                status,
                hashlib.sha256(text.encode("utf-8")).hexdigest(),
                created_at,
                created_at if status == "ACTIVE" else None,
                "ADMIN:seed" if status == "ACTIVE" else None,
            ),
            database_path=database_path,
        )


def _insert_chunks(chunks: list[_SeedChunk], *, database_path: str | Path | None) -> None:
    for chunk in chunks:
        execute(
            """
            INSERT INTO chunks (
                chunk_id, doc_id, article_no, clause_no, breadcrumb, text, domain, label,
                conflict_flag, conflict_with, ord, token_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                chunk.chunk_id,
                chunk.doc_id,
                chunk.article_no,
                chunk.clause_no,
                chunk.breadcrumb,
                chunk.text,
                chunk.domain,
                chunk.label,
                int(chunk.conflict_flag),
                chunk.conflict_with,
                chunk.ordinal,
                len(chunk.text.split()),
            ),
            database_path=database_path,
        )


def _document_chunks(document: dict[str, object]) -> list[_SeedChunk]:
    document_id = _string(document, "document_id")
    title = _string(document, "title")
    domain = _first_string(document, "domains")
    auto_articles = set(_integers(document, "auto_articles"))
    units = _legal_units(_string(document, "text"))
    return [
        _SeedChunk(
            chunk_id=f"{document_id}:seed:{ordinal}",
            doc_id=document_id,
            article_no=article_no,
            clause_no=clause_no,
            breadcrumb=_breadcrumb(title, article_no, clause_no, point_no),
            text="\n".join(lines),
            domain=domain,
            label="auto_answerable" if int(article_no) in auto_articles else "human_only",
            ordinal=ordinal,
        )
        for ordinal, (article_no, clause_no, point_no, lines) in enumerate(units, start=1)
    ]


def _legal_units(text: str) -> list[tuple[str, str | None, str | None, list[str]]]:
    units: list[tuple[str, str | None, str | None, list[str]]] = []
    article_no: str | None = None
    clause_no: str | None = None
    point_no: str | None = None
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        article = ARTICLE_PATTERN.match(line)
        clause = CLAUSE_PATTERN.match(line)
        point = POINT_PATTERN.match(line)
        if article or clause or point:
            _append_unit(units, article_no, clause_no, point_no, lines)
            if article:
                article_no, clause_no, point_no = article.group(1), None, None
            elif clause:
                clause_no, point_no = clause.group(1), None
            else:
                point_no = point.group(1) if point else None
            lines = [line]
        elif article_no is not None:
            lines.append(line)
    _append_unit(units, article_no, clause_no, point_no, lines)
    return units


def _append_unit(
    units: list[tuple[str, str | None, str | None, list[str]]],
    article_no: str | None,
    clause_no: str | None,
    point_no: str | None,
    lines: list[str],
) -> None:
    if article_no is not None and lines:
        units.append((article_no, clause_no, point_no, lines))


def _breadcrumb(title: str, article_no: str, clause_no: str | None, point_no: str | None) -> str:
    parts = [title, f"Điều {article_no}"]
    if clause_no is not None:
        parts.append(f"Khoản {clause_no}")
    if point_no is not None:
        parts.append(f"Điểm {point_no}")
    return " · ".join(parts)


def _with_refund_conflicts(chunks: list[_SeedChunk]) -> list[_SeedChunk]:
    candidates = [
        chunk
        for chunk in chunks
        if chunk.doc_id in REFUND_CONFLICT_DOCUMENTS and chunk.article_no == REFUND_CONFLICT_ARTICLE
    ]
    if len(candidates) != REFUND_CONFLICT_CHUNK_COUNT:
        raise RuntimeError("Cặp mâu thuẫn hoàn học phí phải có đủ sáu chunk.")
    return [
        replace(chunk, conflict_flag=True, conflict_with=_conflict_with(chunk))
        if chunk in candidates
        else chunk
        for chunk in chunks
    ]


def _conflict_with(chunk: _SeedChunk) -> str:
    other_document = "HP-2026-1" if chunk.doc_id == "RH-2026-101" else "RH-2026-101"
    return f"{other_document}:seed:{chunk.ordinal}"


def _string(document: dict[str, object], key: str) -> str:
    value = document.get(key)
    if not isinstance(value, str):
        raise ValueError(f"Seed thiếu trường string {key}.")
    return value


def _optional_string(document: dict[str, object], key: str) -> str | None:
    value = document.get(key)
    if value is None or isinstance(value, str):
        return value
    raise ValueError(f"Seed {key} phải là string hoặc null.")


def _boolean(document: dict[str, object], key: str) -> bool:
    value = document.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"Seed {key} phải là boolean.")
    return value


def _json_value(document: dict[str, object], key: str) -> str:
    value = document.get(key)
    if not isinstance(value, list):
        raise ValueError(f"Seed {key} phải là mảng.")
    return json.dumps(value, ensure_ascii=False)


def _first_string(document: dict[str, object], key: str) -> str:
    values = document.get(key)
    if not isinstance(values, list) or not values or not isinstance(values[0], str):
        raise ValueError(f"Seed {key} phải có ít nhất một domain.")
    return values[0]


def _integers(document: dict[str, object], key: str) -> list[int]:
    values = document.get(key)
    if not isinstance(values, list) or not all(isinstance(value, int) for value in values):
        raise ValueError(f"Seed {key} phải là mảng số nguyên.")
    return values
