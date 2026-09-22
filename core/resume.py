"""R11: diễn đạt lại quyết định của chuyên viên, không tự đưa ra quyết định mới."""

from __future__ import annotations

import json
from sqlite3 import Row
from uuid import uuid4

from corpus.api import get_chunk
from core.ground_guard import guard_resume_groundedness
from core.sanitize import mask_pii
from core.types import CaseStatus, DraftReply, EvidenceResult, EvidenceStatus
from infra.audit import log_event
from infra.db import execute, fetch_one, now_iso
from infra.llm import call_json

RESUME_PROMPT_V1 = """Soạn email bằng tiếng Việt chỉ để diễn đạt quyết định của chuyên viên.
Quyết định: {choice}
Lý do bắt buộc phải giữ nguyên ý và dữ kiện: {reason}

Chỉ dùng lý do và căn cứ dưới đây. Không thêm quy định, điều khoản, suy diễn, cam kết hay quyết định mới.
Body phải nêu rõ lựa chọn của chuyên viên và giữ nguyên lý do. Mỗi câu phải có [chunk_id].

Căn cứ:
{evidence}"""
RESUME_SCHEMA: dict[str, object] = {
    "type": "object",
    "required": ["subject", "body", "citations"],
    "properties": {
        "subject": {"type": "string"},
        "body": {"type": "string"},
        "citations": {"type": "array", "items": {"type": "string"}},
    },
}


def _required_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} phải là chuỗi không rỗng.")
    return value.strip()


def _case_and_evidence(case_id: str) -> tuple[Row, EvidenceResult]:
    case = fetch_one("SELECT * FROM cases WHERE case_id = ?", (case_id,))
    if case is None or case["status"] != CaseStatus.HUMAN_DECIDED:
        raise ValueError("Case phải ở trạng thái HUMAN_DECIDED.")
    decision = fetch_one(
        "SELECT evidence_ids_json FROM decisions WHERE case_id = ? ORDER BY created_at DESC LIMIT 1",
        (case_id,),
    )
    evidence_ids = json.loads(decision["evidence_ids_json"] or "[]") if decision else []
    if not isinstance(evidence_ids, list) or not all(
        isinstance(item, str) for item in evidence_ids
    ):
        raise ValueError("Evidence của case không hợp lệ.")
    chunks = [chunk for chunk_id in evidence_ids if (chunk := get_chunk(chunk_id)) is not None]
    if not chunks:
        raise ValueError("Case không có căn cứ còn hiệu lực để diễn đạt lại.")
    return case, EvidenceResult(EvidenceStatus.OK, chunks, [])


def _citations(value: object, evidence: EvidenceResult) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError("citations phải là mảng chuỗi.")
    citations = [item for item in value if item]
    if not citations or not set(citations) <= {chunk.chunk_id for chunk in evidence.chunks}:
        raise ValueError("citations phải thuộc căn cứ của case.")
    return citations


def resume_case(case_id: str, choice: str, reason: str, actor: str) -> DraftReply:
    """Diễn đạt lại quyết định của người và chuyển case sang chờ duyệt gửi."""
    if not actor.startswith("HUMAN:"):
        raise ValueError("R11 chỉ nhận actor HUMAN:<user>.")
    choice = _required_string(choice, "choice")
    reason = _required_string(reason, "reason")
    case, evidence = _case_and_evidence(case_id)
    evidence_text = "\n\n".join(f"[{chunk.chunk_id}] {chunk.text}" for chunk in evidence.chunks)
    result = call_json(
        RESUME_PROMPT_V1.format(choice=choice, reason=reason, evidence=evidence_text),
        schema=RESUME_SCHEMA,
        step="R11_resume",
        case_id=case_id,
        temperature=0.0,
    )
    if not result.ok:
        raise ValueError(result.error or "LLM không diễn đạt được quyết định.")
    body = _required_string(result.data.get("body"), "body")
    if choice.casefold() not in body.casefold() or reason.casefold() not in body.casefold():
        raise ValueError("Bản nháp phải giữ nguyên quyết định và lý do của chuyên viên.")
    draft = guard_resume_groundedness(
        DraftReply(
            _required_string(result.data.get("subject"), "subject"),
            body,
            _citations(result.data.get("citations"), evidence),
            False,
            [],
        )
    )
    if (
        execute(
            "UPDATE cases SET status = ? WHERE case_id = ? AND status = ?",
            (CaseStatus.PENDING_APPROVAL, case_id, CaseStatus.HUMAN_DECIDED),
        )
        != 1
    ):
        raise ValueError("Case không còn ở trạng thái HUMAN_DECIDED.")
    execute(
        """
        INSERT INTO drafts (draft_id, case_id, kind, subject, body, citations_json, grounded, guard_failures_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(uuid4()),
            case_id,
            "resume",
            draft.subject,
            mask_pii(draft.body),
            json.dumps(draft.citations),
            int(draft.grounded),
            json.dumps(draft.guard_failures),
            now_iso(),
        ),
    )
    log_event(
        case_id=case_id,
        actor=actor,
        action="CASE_RESUMED",
        input_ref=case_id,
        reason=mask_pii(f"Chuyên viên chọn {choice}: {reason}"),
        sources=draft.citations,
        corpus_version=case["corpus_version"],
    )
    return draft
