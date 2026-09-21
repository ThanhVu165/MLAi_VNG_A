"""Gán nhãn thẩm quyền cho từng chunk bằng quyết định của con người."""

from __future__ import annotations

from dataclasses import dataclass, replace

from core.types import ChunkLabel
from corpus.store import DatabasePath, ChunkRecord, get_chunk_record, list_chunks, update_chunk
from infra.audit import log_event
from infra.llm import call_json

LABEL_SUGGESTION_PROMPT_V1 = """Đề xuất nhãn thẩm quyền cho một điều khoản quy định.
Chỉ đề xuất, không quyết định hay áp dụng nhãn. Chỉ trả về auto_answerable hoặc human_only.

Breadcrumb: {breadcrumb}
Nội dung: {text}"""
LABEL_SUGGESTION_SCHEMA: dict[str, object] = {
    "type": "object",
    "required": ["label"],
    "properties": {"label": {"enum": [label.value for label in ChunkLabel]}},
    "additionalProperties": False,
}


@dataclass(frozen=True)
class LabelSuggestion:
    label: ChunkLabel | None
    error: str | None


def chunks_for_coverage(doc_id: str, *, database_path: DatabasePath = None) -> list[ChunkRecord]:
    """Trả các chunk để người dùng gán nhãn; chunk mới mặc định human_only từ store."""
    return list_chunks(doc_id, database_path=database_path)


def set_chunk_label(
    chunk_id: str,
    label: ChunkLabel,
    *,
    actor: str,
    database_path: DatabasePath = None,
) -> ChunkRecord:
    """Chỉ người dùng gọi hàm này mới đổi nhãn và sinh audit event."""
    chunk = get_chunk_record(chunk_id, database_path=database_path)
    if chunk is None:
        raise KeyError(f"Không tìm thấy chunk {chunk_id}.")
    if chunk.label is label:
        return chunk
    updated = replace(chunk, label=label)
    update_chunk(updated, database_path=database_path)
    log_event(
        case_id=None,
        actor=actor,
        action="CHUNK_LABELLED",
        input_ref=chunk.label.value,
        output_ref=label.value,
        reason=f"Đổi nhãn chunk từ {chunk.label.value} sang {label.value}.",
        sources=[chunk.doc_id, chunk.chunk_id],
        database_path=str(database_path) if database_path is not None else None,
    )
    return updated


def suggest_chunk_label(chunk: ChunkRecord, *, case_id: str) -> LabelSuggestion:
    """Gợi ý LLM để hiển thị; không gọi ``set_chunk_label``."""
    result = call_json(
        LABEL_SUGGESTION_PROMPT_V1.format(breadcrumb=chunk.breadcrumb, text=chunk.text),
        schema=LABEL_SUGGESTION_SCHEMA,
        step="K6_label_suggestion",
        case_id=case_id,
        temperature=0.0,
    )
    if not result.ok:
        return LabelSuggestion(None, result.error)
    try:
        return LabelSuggestion(ChunkLabel(str(result.data["label"])), None)
    except (KeyError, ValueError):
        return LabelSuggestion(None, "Gợi ý nhãn không hợp lệ.")
