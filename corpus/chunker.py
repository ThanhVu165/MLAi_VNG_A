"""Chia văn bản quy định theo Điều, Khoản và Điểm."""

from __future__ import annotations

import re
from dataclasses import dataclass

from core.types import Domain
from corpus.store import ChunkRecord

MAX_CHUNK_TOKENS = 800
ARTICLE_HEADING = re.compile(r"^Điều\s+([\dA-Za-z]+)\.", re.I)
CLAUSE_HEADING = re.compile(r"^Khoản\s+([\dA-Za-z]+)\.", re.I)
POINT_HEADING = re.compile(r"^(?:Điểm\s+)?([a-zđ])\)", re.I)


@dataclass
class _LegalUnit:
    article_no: str | None
    clause_no: str | None
    point_no: str | None
    lines: list[str]


def chunk_document(
    text: str,
    *,
    doc_id: str,
    document_title: str,
    domain: Domain,
) -> list[ChunkRecord]:
    """Tách Điều → Khoản → Điểm; chỉ chia nhỏ thêm khi vượt 800 token."""
    units = _legal_units(text)
    chunks: list[ChunkRecord] = []
    for unit in units:
        chunks.extend(_records_for_unit(unit, doc_id, document_title, domain, len(chunks) + 1))
    return chunks


def _legal_units(text: str) -> list[_LegalUnit]:
    units: list[_LegalUnit] = []
    current = _LegalUnit(None, None, None, [])
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        heading = ARTICLE_HEADING.match(line)
        if heading:
            _append_unit(units, current)
            current = _LegalUnit(heading.group(1), None, None, [line])
            continue
        heading = CLAUSE_HEADING.match(line)
        if heading:
            _append_unit(units, current)
            current = _LegalUnit(current.article_no, heading.group(1), None, [line])
            continue
        heading = POINT_HEADING.match(line)
        if heading:
            _append_unit(units, current)
            current = _LegalUnit(current.article_no, current.clause_no, heading.group(1), [line])
            continue
        current.lines.append(line)
    _append_unit(units, current)
    return units


def _append_unit(units: list[_LegalUnit], unit: _LegalUnit) -> None:
    if unit.lines:
        units.append(unit)


def _records_for_unit(
    unit: _LegalUnit,
    doc_id: str,
    document_title: str,
    domain: Domain,
    first_ordinal: int,
) -> list[ChunkRecord]:
    breadcrumb = _breadcrumb(document_title, unit)
    text = "\n".join(unit.lines)
    parts = _split_tokens(text)
    return [
        ChunkRecord(
            chunk_id=f"{doc_id}:chunk:{first_ordinal + index}",
            doc_id=doc_id,
            breadcrumb=breadcrumb,
            text=part,
            domain=domain,
            article_no=unit.article_no,
            clause_no=unit.clause_no,
            ordinal=first_ordinal + index,
            token_count=len(part.split()),
        )
        for index, part in enumerate(parts)
    ]


def _breadcrumb(document_title: str, unit: _LegalUnit) -> str:
    parts = [document_title]
    if unit.article_no is not None:
        parts.append(f"Điều {unit.article_no}")
    if unit.clause_no is not None:
        parts.append(f"Khoản {unit.clause_no}")
    if unit.point_no is not None:
        parts.append(f"Điểm {unit.point_no}")
    return " · ".join(parts)


def _split_tokens(text: str) -> list[str]:
    tokens = text.split()
    return [
        " ".join(tokens[index : index + MAX_CHUNK_TOKENS])
        for index in range(0, len(tokens), MAX_CHUNK_TOKENS)
    ]
