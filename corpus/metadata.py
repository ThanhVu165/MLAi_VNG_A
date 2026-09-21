"""Đề xuất metadata tài liệu bằng LLM, luôn giữ dữ liệu không chắc là null."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date

from infra.llm import JsonObject, call_json

METADATA_EXCERPT_LENGTH = 3_000
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
