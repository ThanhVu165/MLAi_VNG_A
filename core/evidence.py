"""Validator R5 cho căn cứ truy xuất được."""

from __future__ import annotations

from corpus.api import supported_domains
from core.types import ChunkLabel, EvidenceChunk, EvidenceResult, EvidenceStatus, Extraction
from infra.audit import log_event
from infra.settings import SIMILARITY_THRESHOLD

FAILURE_STATUSES: dict[str, EvidenceStatus] = {
    "similarity": EvidenceStatus.NO_AUTHORITATIVE_SOURCE,
    "domain": EvidenceStatus.NO_AUTHORITATIVE_SOURCE,
    "supported_domain": EvidenceStatus.UNSUPPORTED_DOMAIN,
    "authority": EvidenceStatus.AUTHORITY_CONTENT,
    "conflict": EvidenceStatus.CONFLICTING_SOURCES,
    "scope": EvidenceStatus.SCOPE_MISMATCH,
    "facts": EvidenceStatus.FACT_MISSING,
}
TRANSITION_FACT_KEYS = frozenset(
    {
        "academic_year",
        "cohort",
        "date",
        "semester",
        "term",
        "thoi_diem",
        "thời_điểm",
        "year",
        "khóa",
        "khoa",
        "học_kỳ",
        "hoc_ky",
    }
)


def _scope_matches(chunk: EvidenceChunk, facts: dict[str, str]) -> bool:
    values = {value.casefold() for value in facts.values() if value.strip()}
    applies = {value.casefold() for value in chunk.applies_to}
    cohorts = {value.casefold() for value in chunk.cohorts}
    return (not applies or bool(applies & values)) and (not cohorts or bool(cohorts & values))


def _has_transition_context(facts: dict[str, str]) -> bool:
    return any(
        value.strip() and key.casefold() in TRANSITION_FACT_KEYS for key, value in facts.items()
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
    if any(chunk.label is not ChunkLabel.AUTO_ANSWERABLE for chunk in chunks):
        failures.append("authority")
    if any(chunk.conflict_flag for chunk in chunks):
        failures.append("conflict")
    if any(not _scope_matches(chunk, extraction.critical_facts) for chunk in chunks):
        failures.append("scope")
    if extraction.missing_critical_facts or (
        any(chunk.transitional_clause for chunk in chunks)
        and not _has_transition_context(extraction.critical_facts)
    ):
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
    """Đánh giá bảy điều kiện R5 theo thứ tự đặc tả và ghi audit kết quả."""
    failures = _failed_checks(evidence.chunks, extraction)
    status = FAILURE_STATUSES[failures[0]] if failures else EvidenceStatus.OK
    reason = (
        f"Đã kiểm tra căn cứ; không đạt: {', '.join(failures)}."
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
