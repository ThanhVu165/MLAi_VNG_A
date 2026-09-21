"""Sinh bản nháp R7a chỉ từ căn cứ đã được lọc."""

from __future__ import annotations

from typing import Literal

from core.types import DraftReply, EvidenceResult
from infra.audit import log_event
from infra.llm import call_json

GENERATE_PROMPT_V1 = """Soạn email phản hồi sinh viên bằng {language}.
Chỉ dùng các căn cứ bên dưới; không suy đoán nếu căn cứ không nói.
Không cam kết, phê duyệt hoặc quyết định thay mặt DSA. Không nhắc tới hồ sơ cá nhân sinh viên.
Mỗi đoạn trong body phải kết thúc bằng [chunk_id] của căn cứ dùng cho đoạn đó.
Trả JSON subject, body, citations; citations chỉ gồm chunk_id xuất hiện trong căn cứ.

Căn cứ đã lọc:
{evidence}"""
GENERATE_SCHEMA: dict[str, object] = {
    "type": "object",
    "required": ["subject", "body", "citations"],
    "properties": {
        "subject": {"type": "string"},
        "body": {"type": "string"},
        "citations": {"type": "array", "items": {"type": "string"}},
    },
}
LANGUAGE_NAMES = {"vi": "Vietnamese", "en": "English"}


def _evidence_text(evidence: EvidenceResult) -> str:
    return "\n\n".join(
        f"[{chunk.chunk_id}] {chunk.breadcrumb}\n{chunk.text}" for chunk in evidence.chunks
    )


def _string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} phải là chuỗi không rỗng.")
    return value.strip()


def _citations(value: object, evidence: EvidenceResult) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError("citations phải là mảng chuỗi.")
    citations = [item for item in value if item]
    allowed = {chunk.chunk_id for chunk in evidence.chunks}
    if not citations or not set(citations).issubset(allowed):
        raise ValueError("citations phải trỏ tới evidence đã lọc.")
    return citations


def _paragraphs_cited(body: str, citations: list[str]) -> bool:
    paragraphs = [paragraph.strip() for paragraph in body.split("\n\n") if paragraph.strip()]
    return bool(paragraphs) and all(
        any(f"[{citation}]" in paragraph for citation in citations) for paragraph in paragraphs
    )


def generate_reply(
    *,
    case_id: str,
    actor: str,
    corpus_version: str,
    language: Literal["vi", "en"],
    evidence: EvidenceResult,
) -> DraftReply:
    """Gọi LLM một lần để diễn đạt căn cứ đã lọc thành bản nháp có citation."""
    result = call_json(
        GENERATE_PROMPT_V1.format(
            language=LANGUAGE_NAMES[language], evidence=_evidence_text(evidence)
        ),
        schema=GENERATE_SCHEMA,
        step="R7_generate",
        case_id=case_id,
        temperature=0.0,
    )
    if not result.ok:
        raise ValueError(result.error or "LLM không tạo được bản nháp.")
    subject = _string(result.data.get("subject"), "subject")
    body = _string(result.data.get("body"), "body")
    citations = _citations(result.data.get("citations"), evidence)
    if not _paragraphs_cited(body, citations):
        raise ValueError("Mỗi đoạn bản nháp phải có chunk_id căn cứ.")
    draft = DraftReply(subject, body, citations, False, [])
    log_event(
        case_id=case_id,
        actor=actor,
        action="DRAFT_GENERATED",
        input_ref=case_id,
        reason="Đã tạo bản nháp chỉ từ căn cứ đã lọc.",
        sources=citations,
        corpus_version=corpus_version,
    )
    return draft
