"""Validator R5 cho căn cứ truy xuất được."""

from __future__ import annotations

from corpus.api import supported_domains
from core.types import EvidenceChunk, EvidenceResult, EvidenceStatus, Extraction
from infra.audit import log_event
from infra.settings import SIMILARITY_THRESHOLD

FAILURE_STATUSES: dict[str, EvidenceStatus] = {
    "similarity": EvidenceStatus.NO_AUTHORITATIVE_SOURCE,
    "domain": EvidenceStatus.NO_AUTHORITATIVE_SOURCE,
    "supported_domain": EvidenceStatus.UNSUPPORTED_DOMAIN,
    "conflict": EvidenceStatus.CONFLICTING_SOURCES,
    "scope": EvidenceStatus.SCOPE_MISMATCH,
    "facts": EvidenceStatus.FACT_MISSING,
}
FAILURE_REASONS = {
    "similarity": "chưa tìm được điều khoản trả lời câu hỏi",
    "domain": "căn cứ không cùng nhóm nội dung với yêu cầu",
    "supported_domain": "có yêu cầu ngoài ba nhóm nội dung đang hỗ trợ",
    "conflict": "các căn cứ liên quan mâu thuẫn nhau",
    "scope": "căn cứ không áp dụng cho đối tượng đã nêu",
    "facts": "thiếu dữ kiện cần thiết để áp dụng quy định",
    "unanswered_request": "còn yêu cầu chưa có căn cứ trả lời",
}


def _scope_matches(chunk: EvidenceChunk, facts: dict[str, str]) -> bool:
    applies = {value.casefold() for value in chunk.applies_to}
    cohorts = {value.casefold() for value in chunk.cohorts}
    explicit_applies = facts.get("applies_to", "").casefold()
    explicit_cohort = facts.get("cohort", "").casefold()
    return (not applies or not explicit_applies or explicit_applies in applies) and (
        not cohorts or not explicit_cohort or explicit_cohort in cohorts
    )


def _failed_checks(chunks: list[EvidenceChunk], extraction: Extraction) -> list[str]:
    domains = {request.domain for request in extraction.requests}
    failures: list[str] = []
    if not any(chunk.score >= SIMILARITY_THRESHOLD for chunk in chunks):
        failures.append("similarity")
    if any(chunk.domain not in domains for chunk in chunks):
        failures.append("domain")
    if not domains.issubset(set(supported_domains())):
        failures.append("supported_domain")
    if any(chunk.conflict_flag for chunk in chunks):
        failures.append("conflict")
    if any(not _scope_matches(chunk, extraction.critical_facts) for chunk in chunks):
        failures.append("scope")
    if extraction.missing_critical_facts:
        failures.append("facts")
    return failures


def validate_evidence(
    *,
    case_id: str,
    actor: str,
    corpus_version: str,
    evidence: EvidenceResult,
    extraction: Extraction,
) -> EvidenceResult:
    """Kiểm tra phạm vi, nguồn, mâu thuẫn và dữ kiện cần thiết; nhãn cũ không cấp quyền."""
    failures = list(
        dict.fromkeys(_failed_checks(evidence.chunks, extraction) + evidence.failed_checks)
    )
    status = FAILURE_STATUSES.get(failures[0], evidence.status) if failures else evidence.status
    reason = (
        "Đã đối chiếu quy định: "
        + "; ".join(FAILURE_REASONS.get(item, "căn cứ cần kiểm tra thêm") for item in failures)
        + "."
        if failures
        else "Căn cứ truy xuất đạt các kiểm tra bắt buộc."
    )
    log_event(
        case_id=case_id,
        actor=actor,
        action="EVIDENCE_VALIDATED",
        input_ref=case_id,
        reason=reason,
        sources=[chunk.chunk_id for chunk in evidence.chunks],
        corpus_version=corpus_version,
    )
    return EvidenceResult(status=status, chunks=evidence.chunks, failed_checks=failures)
