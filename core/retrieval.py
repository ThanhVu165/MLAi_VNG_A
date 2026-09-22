"""Adapter R4 giữa pipeline và facade corpus."""

from __future__ import annotations

import logging

from corpus.api import search
from core.prepolicy import decision_lock
from core.types import CaseInput, ChunkLabel, Domain, EvidenceChunk, EvidenceResult, EvidenceStatus, Extraction
from infra.audit import log_event
from infra.settings import RETRIEVAL_TOP_K

logger = logging.getLogger(__name__)


def _domains(extraction: Extraction) -> list[Domain]:
    return list(
        dict.fromkeys(
            request.domain for request in extraction.requests if request.domain != Domain.UNKNOWN
        )
    )


def _query(inp: CaseInput, body_clean: str, extraction: Extraction) -> str:
    intents = "; ".join(request.intent for request in extraction.requests if request.intent)
    return "\n".join(part for part in (inp.subject, body_clean, intents) if part)


def _result(
    *,
    case_id: str,
    actor: str,
    corpus_version: str,
    status: EvidenceStatus,
    chunks: list[EvidenceChunk],
    reason: str,
) -> EvidenceResult:
    log_event(
        case_id=case_id,
        actor=actor,
        action="EVIDENCE_RETRIEVED",
        input_ref=case_id,
        reason=reason,
        sources=[chunk.chunk_id for chunk in chunks],
        corpus_version=corpus_version,
    )
    return EvidenceResult(status=status, chunks=chunks, failed_checks=[])


def retrieve_evidence(
    *,
    case_id: str,
    actor: str,
    inp: CaseInput,
    body_clean: str,
    extraction: Extraction,
    corpus_version: str,
) -> EvidenceResult:
    """Tìm căn cứ ACTIVE cho các domain đã trích xuất, luôn trả kết quả fail-safe."""
    domains = _domains(extraction)
    try:
        chunks = search(
            _query(inp, body_clean, extraction), domains, RETRIEVAL_TOP_K, inp.received_at
        )
        if decision_lock(extraction) is None:
            chunks = [chunk for chunk in chunks if chunk.label is ChunkLabel.AUTO_ANSWERABLE]
    except Exception as error:
        logger.exception("Không thể truy vấn corpus: %s", error, extra={"case_id": case_id})
        return _result(
            case_id=case_id,
            actor=actor,
            corpus_version=corpus_version,
            status=EvidenceStatus.NO_AUTHORITATIVE_SOURCE,
            chunks=[],
            reason="Không thể truy vấn căn cứ quy định; chuyển sang xử lý an toàn.",
        )
    return _result(
        case_id=case_id,
        actor=actor,
        corpus_version=corpus_version,
        status=EvidenceStatus.OK if chunks else EvidenceStatus.NO_AUTHORITATIVE_SOURCE,
        chunks=chunks,
        reason="Đã truy xuất căn cứ quy định đang hiệu lực.",
    )
