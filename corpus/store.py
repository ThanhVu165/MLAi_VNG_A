"""Lớp lưu trữ cho nguồn quy định, chunk và phiên bản corpus."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import unicodedata
from dataclasses import dataclass, replace
from pathlib import Path

from core.types import ChunkLabel, Domain, SourceStatus
from infra.db import SqlValue, execute, fetch_all, fetch_one, now_iso

DatabasePath = str | Path | None
CURRENT_CORPUS_VERSION_KEY = "current_corpus_version"


@dataclass(frozen=True)
class SourceRecord:
    doc_id: str
    title: str | None = None
    issuer: str | None = None
    source_url: str | None = None
    source_kind: str | None = None
    sha256: str | None = None
    fetched_at: str | None = None
    is_synthetic: bool = False
    published_at: str | None = None
    effective_from: str | None = None
    effective_to: str | None = None
    applies_to: tuple[str, ...] = ()
    cohorts: tuple[str, ...] = ()
    domains: tuple[Domain, ...] = ()
    supersedes: tuple[str, ...] = ()
    superseded_by: str | None = None
    superseded_at: str | None = None
    transitional_clause: bool = False
    status: SourceStatus = SourceStatus.PENDING_REVIEW
    content_hash: str = ""
    created_at: str | None = None
    activated_at: str | None = None
    activated_by: str | None = None


@dataclass(frozen=True)
class ChunkRecord:
    chunk_id: str
    doc_id: str
    breadcrumb: str
    text: str
    domain: Domain
    article_no: str | None = None
    clause_no: str | None = None
    label: ChunkLabel = ChunkLabel.HUMAN_ONLY
    conflict_flag: bool = False
    conflict_with: str | None = None
    ordinal: int | None = None
    token_count: int | None = None


@dataclass(frozen=True)
class CorpusVersionRecord:
    corpus_version: str
    actor: str | None
    note: str | None
    active_doc_ids: tuple[str, ...]
    created_at: str | None = None


@dataclass(frozen=True)
class SourceContent:
    doc_id: str
    content: bytes
    extracted_text: str = ""
    filename: str = ""


def save_source_content(record: SourceContent, *, database_path: DatabasePath = None) -> None:
    """Giữ bản gốc riêng; không thay thế nội dung của nguồn đã duyệt."""
    source = get_source(record.doc_id, database_path=database_path)
    if source is None:
        raise ValueError("Không tìm thấy nguồn để lưu bản gốc.")
    existing = get_source_content(record.doc_id, database_path=database_path)
    if existing and existing.content != record.content:
        raise ValueError("Bản gốc bất biến; hãy nạp nội dung thay đổi thành nguồn mới.")
    if existing and source.status is not SourceStatus.PENDING_REVIEW and existing != record:
        raise ValueError("Không sửa nội dung đã duyệt; hãy nạp một phiên bản thay thế.")
    execute(
        """INSERT INTO source_contents (doc_id, content, extracted_text, filename)
           VALUES (?, ?, ?, ?) ON CONFLICT(doc_id) DO UPDATE SET
           extracted_text=excluded.extracted_text, filename=excluded.filename""",
        (record.doc_id, record.content, record.extracted_text, record.filename),
        database_path=database_path,
    )


def get_source_content(doc_id: str, *, database_path: DatabasePath = None) -> SourceContent | None:
    row = fetch_one(
        "SELECT * FROM source_contents WHERE doc_id = ?", (doc_id,), database_path=database_path
    )
    return (
        SourceContent(row["doc_id"], bytes(row["content"]), row["extracted_text"], row["filename"])
        if row
        else None
    )


def _nfc(value: str | None) -> str | None:
    return unicodedata.normalize("NFC", value) if value is not None else None


def _json(values: tuple[str, ...]) -> str:
    return json.dumps([unicodedata.normalize("NFC", value) for value in values], ensure_ascii=False)


def _source_values(record: SourceRecord) -> tuple[SqlValue, ...]:
    return (
        _nfc(record.doc_id),
        _nfc(record.title),
        _nfc(record.issuer),
        record.source_url,
        record.source_kind,
        record.sha256,
        record.fetched_at,
        int(record.is_synthetic),
        record.published_at,
        record.effective_from,
        record.effective_to,
        _json(record.applies_to),
        _json(record.cohorts),
        _json(tuple(domain.value for domain in record.domains)),
        _json(record.supersedes),
        record.superseded_by,
        record.superseded_at,
        int(record.transitional_clause),
        record.status.value,
        record.content_hash,
        record.created_at,
        record.activated_at,
        record.activated_by,
    )


def _source_from_row(source: sqlite3.Row) -> SourceRecord:
    return SourceRecord(
        doc_id=source["doc_id"],
        title=source["title"],
        issuer=source["issuer"],
        source_url=source["source_url"],
        source_kind=source["source_kind"],
        sha256=source["sha256"],
        fetched_at=source["fetched_at"],
        is_synthetic=bool(source["is_synthetic"]),
        published_at=source["published_at"],
        effective_from=source["effective_from"],
        effective_to=source["effective_to"],
        applies_to=tuple(json.loads(source["applies_to_json"] or "[]")),
        cohorts=tuple(json.loads(source["cohorts_json"] or "[]")),
        domains=tuple(Domain(value) for value in json.loads(source["domains_json"] or "[]")),
        supersedes=tuple(json.loads(source["supersedes_json"] or "[]")),
        superseded_by=source["superseded_by"],
        superseded_at=source["superseded_at"],
        transitional_clause=bool(source["transitional_clause"]),
        status=SourceStatus(source["status"]),
        content_hash=source["content_hash"] or "",
        created_at=source["created_at"],
        activated_at=source["activated_at"],
        activated_by=source["activated_by"],
    )


def create_source(record: SourceRecord, *, database_path: DatabasePath = None) -> SourceRecord:
    stored = replace(record, created_at=record.created_at or now_iso())
    execute(
        """
        INSERT INTO sources (
            doc_id, title, issuer, source_url, source_kind, sha256, fetched_at, is_synthetic,
            published_at, effective_from, effective_to, applies_to_json, cohorts_json, domains_json,
            supersedes_json, superseded_by, superseded_at, transitional_clause, status, content_hash,
            created_at, activated_at, activated_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        _source_values(stored),
        database_path=database_path,
    )
    return stored


def get_source(doc_id: str, *, database_path: DatabasePath = None) -> SourceRecord | None:
    row = fetch_one(
        "SELECT * FROM sources WHERE doc_id = ?", (_nfc(doc_id),), database_path=database_path
    )
    return _source_from_row(row) if row is not None else None


def list_sources(
    status: SourceStatus | None = None, *, database_path: DatabasePath = None
) -> list[SourceRecord]:
    if status is None:
        rows = fetch_all("SELECT * FROM sources ORDER BY doc_id", database_path=database_path)
    else:
        rows = fetch_all(
            "SELECT * FROM sources WHERE status = ? ORDER BY doc_id",
            (status.value,),
            database_path=database_path,
        )
    return [_source_from_row(row) for row in rows]


def update_source(record: SourceRecord, *, database_path: DatabasePath = None) -> None:
    affected = execute(
        """
        UPDATE sources SET
            title = ?, issuer = ?, source_url = ?, source_kind = ?, sha256 = ?, fetched_at = ?,
            is_synthetic = ?, published_at = ?, effective_from = ?, effective_to = ?,
            applies_to_json = ?, cohorts_json = ?, domains_json = ?, supersedes_json = ?,
            superseded_by = ?, superseded_at = ?, transitional_clause = ?, status = ?, content_hash = ?,
            created_at = COALESCE(?, created_at), activated_at = ?, activated_by = ?
        WHERE doc_id = ?
        """,
        _source_values(record)[1:] + (_nfc(record.doc_id),),
        database_path=database_path,
    )
    if affected != 1:
        raise KeyError(f"Không tìm thấy nguồn {record.doc_id}.")


def delete_source(doc_id: str, *, database_path: DatabasePath = None) -> bool:
    return (
        execute(
            "DELETE FROM sources WHERE doc_id = ?", (_nfc(doc_id),), database_path=database_path
        )
        == 1
    )


def _chunk_values(record: ChunkRecord) -> tuple[SqlValue, ...]:
    return (
        _nfc(record.chunk_id),
        _nfc(record.doc_id),
        _nfc(record.article_no),
        _nfc(record.clause_no),
        _nfc(record.breadcrumb),
        _nfc(record.text),
        record.domain.value,
        record.label.value,
        int(record.conflict_flag),
        _nfc(record.conflict_with),
        record.ordinal,
        record.token_count,
    )


def _chunk_from_row(chunk: sqlite3.Row) -> ChunkRecord:
    return ChunkRecord(
        chunk_id=chunk["chunk_id"],
        doc_id=chunk["doc_id"],
        article_no=chunk["article_no"],
        clause_no=chunk["clause_no"],
        breadcrumb=chunk["breadcrumb"],
        text=chunk["text"],
        domain=Domain(chunk["domain"]),
        label=ChunkLabel(chunk["label"]),
        conflict_flag=bool(chunk["conflict_flag"]),
        conflict_with=chunk["conflict_with"],
        ordinal=chunk["ord"],
        token_count=chunk["token_count"],
    )


def create_chunk(record: ChunkRecord, *, database_path: DatabasePath = None) -> None:
    execute(
        """
        INSERT INTO chunks (
            chunk_id, doc_id, article_no, clause_no, breadcrumb, text, domain, label,
            conflict_flag, conflict_with, ord, token_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        _chunk_values(record),
        database_path=database_path,
    )


def get_chunk_record(chunk_id: str, *, database_path: DatabasePath = None) -> ChunkRecord | None:
    row = fetch_one(
        "SELECT * FROM chunks WHERE chunk_id = ?", (_nfc(chunk_id),), database_path=database_path
    )
    return _chunk_from_row(row) if row is not None else None


def list_chunks(
    doc_id: str | None = None, *, database_path: DatabasePath = None
) -> list[ChunkRecord]:
    if doc_id is None:
        rows = fetch_all("SELECT * FROM chunks ORDER BY doc_id, ord", database_path=database_path)
    else:
        rows = fetch_all(
            "SELECT * FROM chunks WHERE doc_id = ? ORDER BY ord",
            (_nfc(doc_id),),
            database_path=database_path,
        )
    return [_chunk_from_row(row) for row in rows]


def update_chunk(record: ChunkRecord, *, database_path: DatabasePath = None) -> None:
    affected = execute(
        """
        UPDATE chunks SET
            doc_id = ?, article_no = ?, clause_no = ?, breadcrumb = ?, text = ?, domain = ?, label = ?,
            conflict_flag = ?, conflict_with = ?, ord = ?, token_count = ?
        WHERE chunk_id = ?
        """,
        _chunk_values(record)[1:] + (_nfc(record.chunk_id),),
        database_path=database_path,
    )
    if affected != 1:
        raise KeyError(f"Không tìm thấy chunk {record.chunk_id}.")


def delete_chunk(chunk_id: str, *, database_path: DatabasePath = None) -> bool:
    return (
        execute(
            "DELETE FROM chunks WHERE chunk_id = ?", (_nfc(chunk_id),), database_path=database_path
        )
        == 1
    )


def _version_from_row(version: sqlite3.Row) -> CorpusVersionRecord:
    return CorpusVersionRecord(
        corpus_version=version["corpus_version"],
        created_at=version["created_at"],
        actor=version["actor"],
        note=version["note"],
        active_doc_ids=tuple(json.loads(version["active_doc_ids_json"] or "[]")),
    )


def create_corpus_version(
    record: CorpusVersionRecord, *, database_path: DatabasePath = None
) -> CorpusVersionRecord:
    stored = replace(record, created_at=record.created_at or now_iso())
    execute(
        "INSERT INTO corpus_versions (corpus_version, created_at, actor, note, active_doc_ids_json) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            stored.corpus_version,
            stored.created_at,
            stored.actor,
            stored.note,
            _json(stored.active_doc_ids),
        ),
        database_path=database_path,
    )
    return stored


def get_corpus_version_record(
    corpus_version: str, *, database_path: DatabasePath = None
) -> CorpusVersionRecord | None:
    row = fetch_one(
        "SELECT * FROM corpus_versions WHERE corpus_version = ?",
        (corpus_version,),
        database_path=database_path,
    )
    return _version_from_row(row) if row is not None else None


def list_corpus_versions(*, database_path: DatabasePath = None) -> list[CorpusVersionRecord]:
    rows = fetch_all(
        "SELECT * FROM corpus_versions ORDER BY created_at", database_path=database_path
    )
    return [_version_from_row(row) for row in rows]


def update_corpus_version(
    record: CorpusVersionRecord, *, database_path: DatabasePath = None
) -> None:
    affected = execute(
        """
        UPDATE corpus_versions
        SET created_at = COALESCE(?, created_at), actor = ?, note = ?, active_doc_ids_json = ?
        WHERE corpus_version = ?
        """,
        (
            record.created_at,
            record.actor,
            record.note,
            _json(record.active_doc_ids),
            record.corpus_version,
        ),
        database_path=database_path,
    )
    if affected != 1:
        raise KeyError(f"Không tìm thấy corpus version {record.corpus_version}.")


def delete_corpus_version(corpus_version: str, *, database_path: DatabasePath = None) -> bool:
    return (
        execute(
            "DELETE FROM corpus_versions WHERE corpus_version = ?",
            (corpus_version,),
            database_path=database_path,
        )
        == 1
    )


def compute_corpus_version(*, database_path: DatabasePath = None) -> str:
    rows = fetch_all(
        "SELECT doc_id, content_hash FROM sources WHERE status = ? ORDER BY doc_id",
        (SourceStatus.ACTIVE.value,),
        database_path=database_path,
    )
    digest_input = "\n".join(f"{row['doc_id']}:{row['content_hash'] or ''}" for row in rows)
    return f"cv_{hashlib.sha256(digest_input.encode()).hexdigest()[:12]}"


def bump_corpus_version(actor: str, note: str, *, database_path: DatabasePath = None) -> str:
    rows = fetch_all(
        "SELECT doc_id FROM sources WHERE status = ? ORDER BY doc_id",
        (SourceStatus.ACTIVE.value,),
        database_path=database_path,
    )
    corpus_version = compute_corpus_version(database_path=database_path)
    if get_corpus_version_record(corpus_version, database_path=database_path) is None:
        create_corpus_version(
            CorpusVersionRecord(
                corpus_version=corpus_version,
                actor=actor,
                note=note,
                active_doc_ids=tuple(row["doc_id"] for row in rows),
            ),
            database_path=database_path,
        )
    execute(
        """
        INSERT INTO settings (key, value, updated_at, actor) VALUES (?, ?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at,
            actor = excluded.actor
        """,
        (CURRENT_CORPUS_VERSION_KEY, corpus_version, now_iso(), actor),
        database_path=database_path,
    )
    return corpus_version


def get_current_corpus_version(*, database_path: DatabasePath = None) -> str | None:
    row = fetch_one(
        "SELECT value FROM settings WHERE key = ?",
        (CURRENT_CORPUS_VERSION_KEY,),
        database_path=database_path,
    )
    return row["value"] if row is not None else None
