"""Đề xuất metadata tài liệu bằng LLM, luôn giữ dữ liệu không chắc là null."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from datetime import date

from core.types import Domain, SourceStatus
from infra.llm import JsonObject, call_json
from infra.audit import log_event
from corpus.store import DatabasePath, SourceRecord, create_source, get_source, update_source

METADATA_EXCERPT_LENGTH = 3_000
SUPPORTED_DOMAIN_VALUES = frozenset(domain.value for domain in Domain if domain is not Domain.UNKNOWN)
METADATA_PROMPT_V1 = """Bạn trích xuất metadata từ văn bản quy định bên dưới.
Chỉ dùng thông tin hiện diện trong văn bản; không suy đoán. Trường không chắc phải là null.
`transitional_clause` chỉ true khi văn bản có điều khoản chuyển tiếp rõ ràng.
`status` luôn là PENDING_REVIEW; `content_hash` luôn là null vì hệ thống tự tính.

Văn bản:
{excerpt}"""
METADATA_SCHEMA: dict[str, object] = {
    "type": "object",
    "required": [
        "document_id",
        "title",
        "issuer",
        "published_at",
        "effective_from",
        "effective_to",
        "applies_to",
        "cohorts",
        "supersedes",
        "transitional_clause",
        "domains",
        "status",
        "content_hash",
    ],
    "properties": {
        "document_id": {"type": ["string", "null"]},
        "title": {"type": ["string", "null"]},
        "issuer": {"type": ["string", "null"]},
        "published_at": {"type": ["string", "null"], "format": "date"},
        "effective_from": {"type": ["string", "null"], "format": "date"},
        "effective_to": {"type": ["string", "null"], "format": "date"},
        "applies_to": {"type": ["array", "null"], "items": {"type": "string"}},
        "cohorts": {"type": ["array", "null"], "items": {"type": "string"}},
        "supersedes": {"type": ["array", "null"], "items": {"type": "string"}},
        "transitional_clause": {"type": ["boolean", "null"]},
        "domains": {"type": ["array", "null"], "items": {"type": "string"}},
        "status": {"const": "PENDING_REVIEW"},
        "content_hash": {"type": "null"},
    },
    "additionalProperties": False,
}


@dataclass(frozen=True)
class MetadataDraft:
    document_id: str | None
    title: str | None
    issuer: str | None
    published_at: str | None
    effective_from: str | None
    effective_to: str | None
    applies_to: tuple[str, ...] | None
    cohorts: tuple[str, ...] | None
    supersedes: tuple[str, ...] | None
    transitional_clause: bool | None
    domains: tuple[str, ...] | None
    content_hash: str


@dataclass(frozen=True)
class MetadataProposal:
    draft: MetadataDraft | None
    error: str | None


def save_metadata(
    draft: MetadataDraft,
    *,
    actor: str,
    source_id: str | None = None,
    database_path: DatabasePath = None,
) -> SourceRecord:
    """Kiểm tra và lưu metadata, luôn giữ nguồn ở trạng thái chờ duyệt."""
    _validate_draft(draft)
    document_id = draft.document_id or ""
    existing = get_source(source_id or document_id, database_path=database_path)
    if source_id is None and existing is not None:
        raise ValueError("document_id đã tồn tại.")
    if source_id is not None and source_id != document_id:
        raise ValueError("Không thể đổi document_id của nguồn đã nạp.")

    stored = _source_from_draft(draft, existing)
    if existing is None:
        create_source(stored, database_path=database_path)
    else:
        update_source(stored, database_path=database_path)
    _log_metadata_edit(existing, stored, actor=actor, database_path=database_path)
    return stored


def propose_metadata(text: str, *, case_id: str) -> MetadataProposal:
    """Đề xuất bản nháp metadata từ tối đa 3.000 ký tự đầu của tài liệu."""
    prompt = METADATA_PROMPT_V1.format(excerpt=text[:METADATA_EXCERPT_LENGTH])
    result = call_json(
        prompt,
        schema=METADATA_SCHEMA,
        step="K3_metadata",
        case_id=case_id,
        temperature=0.0,
    )
    if not result.ok:
        return MetadataProposal(None, result.error or "LLM không trả metadata.")
    try:
        return MetadataProposal(_draft_from_data(result.data, text), None)
    except ValueError as error:
        return MetadataProposal(None, str(error))


def _draft_from_data(data: JsonObject, text: str) -> MetadataDraft:
    return MetadataDraft(
        document_id=_nullable_string(data, "document_id"),
        title=_nullable_string(data, "title"),
        issuer=_nullable_string(data, "issuer"),
        published_at=_nullable_date(data, "published_at"),
        effective_from=_nullable_date(data, "effective_from"),
        effective_to=_nullable_date(data, "effective_to"),
        applies_to=_nullable_strings(data, "applies_to"),
        cohorts=_nullable_strings(data, "cohorts"),
        supersedes=_nullable_strings(data, "supersedes"),
        transitional_clause=_nullable_bool(data, "transitional_clause"),
        domains=_nullable_strings(data, "domains"),
        content_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
    )


def _validate_draft(draft: MetadataDraft) -> None:
    if not draft.document_id or not draft.document_id.strip():
        raise ValueError("document_id không được để trống.")
    for value in (draft.published_at, draft.effective_from, draft.effective_to):
        if value:
            date.fromisoformat(value)
    if draft.effective_from and draft.effective_to:
        if date.fromisoformat(draft.effective_from) > date.fromisoformat(draft.effective_to):
            raise ValueError("effective_from phải trước hoặc bằng effective_to.")
    if not draft.domains or not set(draft.domains) <= SUPPORTED_DOMAIN_VALUES:
        raise ValueError("domains phải thuộc danh sách domain hợp lệ.")
    if draft.transitional_clause is None:
        raise ValueError("Cần xác nhận transitional_clause trước khi lưu.")


def _source_from_draft(draft: MetadataDraft, existing: SourceRecord | None) -> SourceRecord:
    assert draft.document_id is not None
    assert draft.transitional_clause is not None
    domains = tuple(Domain(domain) for domain in draft.domains or ())
    if existing is not None:
        return replace(
            existing,
            title=draft.title,
            issuer=draft.issuer,
            published_at=draft.published_at,
            effective_from=draft.effective_from,
            effective_to=draft.effective_to,
            applies_to=draft.applies_to or (),
            cohorts=draft.cohorts or (),
            domains=domains,
            supersedes=draft.supersedes or (),
            transitional_clause=draft.transitional_clause,
            status=SourceStatus.PENDING_REVIEW,
            content_hash=draft.content_hash,
        )
    return SourceRecord(
        doc_id=draft.document_id,
        title=draft.title,
        issuer=draft.issuer,
        published_at=draft.published_at,
        effective_from=draft.effective_from,
        effective_to=draft.effective_to,
        applies_to=draft.applies_to or (),
        cohorts=draft.cohorts or (),
        domains=domains,
        supersedes=draft.supersedes or (),
        transitional_clause=draft.transitional_clause,
        status=SourceStatus.PENDING_REVIEW,
        content_hash=draft.content_hash,
    )


def _log_metadata_edit(
    previous: SourceRecord | None,
    stored: SourceRecord,
    *,
    actor: str,
    database_path: DatabasePath,
) -> None:
    fields = _changed_fields(previous, stored)
    log_event(
        case_id=None,
        actor=actor,
        action="SOURCE_METADATA_EDITED",
        input_ref=stored.content_hash,
        output_ref=stored.doc_id,
        reason=f"Đã cập nhật metadata: {', '.join(fields)}.",
        sources=[stored.doc_id],
        database_path=str(database_path) if database_path is not None else None,
    )


def _changed_fields(previous: SourceRecord | None, stored: SourceRecord) -> list[str]:
    fields = [
        "title",
        "issuer",
        "published_at",
        "effective_from",
        "effective_to",
        "applies_to",
        "cohorts",
        "domains",
        "supersedes",
        "transitional_clause",
        "content_hash",
    ]
    return fields if previous is None else [
        field for field in fields if getattr(previous, field) != getattr(stored, field)
    ]


def _nullable_string(data: JsonObject, key: str) -> str | None:
    value = data.get(key)
    if value is None or isinstance(value, str):
        return value
    raise ValueError(f"{key} phải là string hoặc null.")


def _nullable_date(data: JsonObject, key: str) -> str | None:
    value = _nullable_string(data, key)
    if value is not None:
        date.fromisoformat(value)
    return value


def _nullable_strings(data: JsonObject, key: str) -> tuple[str, ...] | None:
    value = data.get(key)
    if value is None:
        return None
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return tuple(item for item in value if isinstance(item, str))
    raise ValueError(f"{key} phải là mảng string hoặc null.")


def _nullable_bool(data: JsonObject, key: str) -> bool | None:
    value = data.get(key)
    if value is None or isinstance(value, bool):
        return value
    raise ValueError(f"{key} phải là boolean hoặc null.")
