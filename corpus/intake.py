"""Nạp nguồn thủ công một lần cho Corpus Admin."""

from __future__ import annotations

import hashlib
import logging
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from urllib.request import urlopen

from corpus.store import DatabasePath, SourceRecord, create_source, get_source, list_sources
from infra.audit import log_event
from infra.db import now_iso

LOGGER = logging.getLogger(__name__)
TEXT_SOURCE_KIND = "text"
URL_SOURCE_KIND = "url"
DEFAULT_TEXT_TITLE = "Văn bản dán trực tiếp"
SUPPORTED_FILE_KINDS = frozenset({".pdf", ".docx"})
FetchBytes = Callable[[str], bytes]


@dataclass(frozen=True)
class IntakeResult:
    source: SourceRecord
    created: bool
    message: str
    content: bytes


def _source_kind(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_FILE_KINDS:
        raise ValueError("Chỉ hỗ trợ tệp PDF hoặc DOCX.")
    return suffix.removeprefix(".")


def _find_by_sha256(digest: str, *, database_path: DatabasePath) -> SourceRecord | None:
    return next(
        (source for source in list_sources(database_path=database_path) if source.sha256 == digest),
        None,
    )


def _audit_database_path(database_path: DatabasePath) -> str | None:
    return str(database_path) if isinstance(database_path, Path) else database_path


def _ingest(
    content: bytes,
    *,
    title: str,
    source_kind: str,
    actor: str,
    source_url: str | None = None,
    fetched_at: str | None = None,
    document_id: str | None = None,
    database_path: DatabasePath = None,
) -> IntakeResult:
    if not content:
        raise ValueError("Nội dung tài liệu không được để trống.")

    digest = hashlib.sha256(content).hexdigest()
    existing = _find_by_sha256(digest, database_path=database_path)
    if existing is not None:
        return IntakeResult(existing, False, "Tài liệu không thay đổi", content)

    doc_id = document_id or f"src_{digest[:12]}"
    if get_source(doc_id, database_path=database_path) is not None:
        raise ValueError(f"Mã tài liệu {doc_id} đã được dùng cho nội dung khác.")

    source = create_source(
        SourceRecord(
            doc_id=doc_id,
            title=title,
            source_url=source_url,
            source_kind=source_kind,
            sha256=digest,
            fetched_at=fetched_at,
            content_hash=digest,
        ),
        database_path=database_path,
    )
    log_event(
        case_id=None,
        actor=actor,
        action="SOURCE_UPLOADED",
        input_ref=digest,
        output_ref=source.doc_id,
        reason="Nạp nguồn thủ công để chờ kiểm tra và duyệt.",
        sources=[source.doc_id],
        database_path=_audit_database_path(database_path),
    )
    LOGGER.info("Đã nạp nguồn %s", source.doc_id)
    return IntakeResult(source, True, "Đã nạp tài liệu chờ duyệt", content)


def ingest_file(
    content: bytes,
    filename: str,
    *,
    actor: str,
    document_id: str | None = None,
    database_path: DatabasePath = None,
) -> IntakeResult:
    """Nạp một tệp PDF/DOCX do admin chọn thủ công."""
    return _ingest(
        content,
        title=filename,
        source_kind=_source_kind(filename),
        actor=actor,
        document_id=document_id,
        database_path=database_path,
    )


def ingest_text(
    text: str,
    *,
    actor: str,
    title: str = DEFAULT_TEXT_TITLE,
    document_id: str | None = None,
    database_path: DatabasePath = None,
) -> IntakeResult:
    """Nạp văn bản được admin dán trực tiếp sau khi chuẩn hóa NFC."""
    content = unicodedata.normalize("NFC", text).encode("utf-8")
    return _ingest(
        content,
        title=title,
        source_kind=TEXT_SOURCE_KIND,
        actor=actor,
        document_id=document_id,
        database_path=database_path,
    )


def ingest_url(
    url: str,
    *,
    actor: str,
    fetch: FetchBytes | None = None,
    document_id: str | None = None,
    database_path: DatabasePath = None,
) -> IntakeResult:
    """Tải một URL khi admin gọi hàm; không tạo lịch chạy nền."""
    if not url.strip():
        raise ValueError("URL không được để trống.")
    content = (fetch or _download_once)(url)
    return _ingest(
        content,
        title=url,
        source_kind=URL_SOURCE_KIND,
        actor=actor,
        source_url=url,
        fetched_at=now_iso(),
        document_id=document_id,
        database_path=database_path,
    )


def _download_once(url: str) -> bytes:
    with urlopen(url) as response:  # nosec B310: chỉ gọi từ thao tác admin thủ công.
        return response.read()
