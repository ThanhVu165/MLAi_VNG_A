"""Sinh thẻ escalation R7b từ fact và căn cứ đã xác định."""

from __future__ import annotations

from collections.abc import Mapping

from core.types import DraftReply, EscalationCard, EscalationType, EvidenceResult, Extraction
from infra.audit import log_event
from infra.llm import call_json

QUESTION_PROMPT_V1 = """Tạo thẻ escalation bằng tiếng Việt cho chuyên viên DSA.
Chỉ dùng facts và căn cứ bên dưới; không suy đoán hay tự tạo dữ kiện.
Thẻ có đúng bốn khối: summary một câu, facts dạng bullet, basis có căn cứ, question.
question là đúng một câu hỏi đóng và options có 2–4 phương án trả lời sẵn.
Trong basis chỉ dùng chunk_id có trong căn cứ.

Loại escalation: {escalation_type}
Fact đã xác định:
{known_facts}
Fact còn thiếu:
{missing_facts}
Căn cứ:
{evidence}"""
QUESTION_SCHEMA: dict[str, object] = {
    "type": "object",
    "required": ["summary", "facts", "basis", "question", "options"],
    "properties": {
        "summary": {"type": "string"},
        "facts": {"type": "array", "items": {"type": "string"}},
        "basis": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["chunk_id", "quote"],
                "properties": {"chunk_id": {"type": "string"}, "quote": {"type": "string"}},
            },
        },
        "question": {"type": "string"},
        "options": {"type": "array", "items": {"type": "string"}},
    },
}


def _strings(value: object, field: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"{field} phải là mảng chuỗi không rỗng.")
    return [item.strip() for item in value]


def _string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} phải là chuỗi không rỗng.")
    return value.strip()


def _facts(extraction: Extraction) -> tuple[str, str]:
    known = "\n".join(f"- {key}: {value}" for key, value in extraction.critical_facts.items())
    missing = "\n".join(f"- {fact}" for fact in extraction.missing_critical_facts)
    return known or "- Không có", missing or "- Không có"


def _evidence(evidence: EvidenceResult) -> str:
    return "\n\n".join(
        f"[{chunk.chunk_id}] {chunk.breadcrumb}\n{chunk.text}" for chunk in evidence.chunks
    )


def _basis(value: object, evidence: EvidenceResult) -> list[tuple[str, str]]:
    if not isinstance(value, list):
        raise ValueError("basis phải là mảng.")
    chunks = {chunk.chunk_id: chunk for chunk in evidence.chunks}
    basis: list[tuple[str, str]] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError("basis phải chứa object.")
        chunk_id = _string(item.get("chunk_id"), "basis.chunk_id")
        quote = _string(item.get("quote"), "basis.quote")
        chunk = chunks.get(chunk_id)
        if chunk is None or quote not in chunk.text:
            raise ValueError("basis phải trỏ tới trích dẫn thuộc evidence.")
        basis.append((chunk.breadcrumb, quote))
    return basis


def generate_escalation_card(
    *,
    case_id: str,
    actor: str,
    corpus_version: str,
    escalation_type: EscalationType,
    extraction: Extraction,
    evidence: EvidenceResult,
    partial_draft: DraftReply | None = None,
) -> EscalationCard:
    """Gọi LLM để tạo bốn khối escalation từ dữ liệu đã lọc."""
    known_facts, missing_facts = _facts(extraction)
    result = call_json(
        QUESTION_PROMPT_V1.format(
            escalation_type=escalation_type.value,
            known_facts=known_facts,
            missing_facts=missing_facts,
            evidence=_evidence(evidence),
        ),
        schema=QUESTION_SCHEMA,
        step="R7_question",
        case_id=case_id,
        temperature=0.0,
    )
    if not result.ok:
        raise ValueError(result.error or "LLM không tạo được câu hỏi chuyển tiếp.")
    basis = _basis(result.data.get("basis"), evidence)
    card = EscalationCard(
        summary=_string(result.data.get("summary"), "summary"),
        facts=_strings(result.data.get("facts"), "facts"),
        basis=basis,
        question=_string(result.data.get("question"), "question"),
        options=_strings(result.data.get("options"), "options"),
        escalation_type=escalation_type,
        partial_draft=partial_draft,
    )
    log_event(
        case_id=case_id,
        actor=actor,
        action="QUESTION_GENERATED",
        input_ref=case_id,
        reason="Đã tạo thẻ escalation từ facts và căn cứ đã lọc.",
        sources=[chunk.chunk_id for chunk in evidence.chunks],
        corpus_version=corpus_version,
    )
    return card
