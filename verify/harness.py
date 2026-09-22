"""Chạy các bộ Verify qua đúng pipeline dùng cho email thật."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from corpus.api import is_active
from core.pipeline import process_case
from core.types import CaseInput, Decision, EscalationType, PipelineResult
from infra.audit import log_event
from infra.db import now_iso, to_local


LOGGER = logging.getLogger(__name__)
CASE_SETS = {
    "verify4": Path("verify/cases_verify4.json"),
    "escalation5": Path("verify/cases_escalation5.json"),
    "full15": Path("verify/cases_full15.json"),
}
VERIFY_ACTOR = "SYSTEM"


@dataclass(frozen=True)
class VerifyCase:
    case_id: str
    input: CaseInput
    expected_decision: Decision
    expected_type: EscalationType | None


@dataclass(frozen=True)
class VerifyResult:
    case_id: str
    subject: str
    question: str | None
    expected_decision: Decision
    expected_type: EscalationType | None
    actual_decision: Decision
    actual_type: EscalationType | None
    rule_id: str
    passed: bool
    elapsed_ms: int
    timestamp: str
    corpus_version: str
    case_ref: str


def _string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} phải là chuỗi không rỗng.")
    return value


def _case_from_payload(payload: object) -> VerifyCase:
    if not isinstance(payload, dict):
        raise ValueError("Mỗi case Verify phải là object.")
    input_payload = payload.get("input")
    if not isinstance(input_payload, dict):
        raise ValueError("Case Verify thiếu input.")
    received_at = datetime.fromisoformat(_string(input_payload.get("received_at"), "received_at"))
    if received_at.tzinfo is None or received_at.utcoffset() is None:
        raise ValueError("received_at phải có múi giờ.")
    expected_type = payload.get("expected_type")
    return VerifyCase(
        case_id=_string(payload.get("id"), "id"),
        input=CaseInput(
            sender=_string(input_payload.get("sender"), "input.sender"),
            subject=_string(input_payload.get("subject"), "input.subject"),
            body=_string(input_payload.get("body"), "input.body"),
            received_at=received_at,
            channel="verify",
            external_id=_string(payload.get("id"), "id"),
        ),
        expected_decision=Decision(_string(payload.get("expected_decision"), "expected_decision")),
        expected_type=EscalationType(expected_type) if isinstance(expected_type, str) else None,
    )


def load_cases(path: Path) -> tuple[VerifyCase, ...]:
    """Đọc và kiểm tra cấu trúc một file case JSON."""
    try:
        payload: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Không đọc được file case {path}: {error}") from error
    if not isinstance(payload, list):
        raise ValueError("File case Verify phải là danh sách.")
    return tuple(_case_from_payload(case) for case in payload)


def _has_active_citations(result: PipelineResult) -> bool:
    citations = result.draft.citations if result.draft is not None else []
    try:
        return bool(citations) and all(is_active(citation) for citation in citations)
    except (OSError, RuntimeError, ValueError) as error:
        LOGGER.warning("Không xác minh được citation ACTIVE: %s", error)
        return False


def _matches(case: VerifyCase, result: PipelineResult) -> bool:
    decision_matches = result.decision.decision is case.expected_decision
    type_matches = result.decision.escalation_type is case.expected_type
    citations_match = (
        _has_active_citations(result) if case.expected_decision is Decision.AUTO_REPLY else True
    )
    return decision_matches and type_matches and citations_match


def _run_case(case: VerifyCase) -> VerifyResult:
    started_at = perf_counter()
    result = process_case(case.input, actor=VERIFY_ACTOR)
    elapsed_ms = round((perf_counter() - started_at) * 1_000)
    return VerifyResult(
        case_id=case.case_id,
        subject=case.input.subject,
        question=result.card.question if result.card is not None else None,
        expected_decision=case.expected_decision,
        expected_type=case.expected_type,
        actual_decision=result.decision.decision,
        actual_type=result.decision.escalation_type,
        rule_id=result.decision.rule_id,
        passed=_matches(case, result),
        elapsed_ms=elapsed_ms,
        timestamp=to_local(now_iso()),
        corpus_version=result.corpus_version,
        case_ref=result.case_id,
    )


def run_cases(path: Path, *, run_name: str, case_id: str | None = None) -> tuple[VerifyResult, ...]:
    """Chạy tuần tự một bộ Verify và luôn ghi audit bắt đầu/kết thúc."""
    cases = load_cases(path)
    if case_id is not None:
        cases = tuple(case for case in cases if case.case_id == case_id)
        if not cases:
            raise ValueError(f"Không tìm thấy case {case_id}.")
    run_id = str(uuid4())
    log_event(
        case_id=None,
        actor=VERIFY_ACTOR,
        action="VERIFY_RUN_STARTED",
        input_ref=run_name,
        output_ref=run_id,
        reason="Bắt đầu chạy Verify tuần tự qua pipeline dùng chung.",
    )
    results: list[VerifyResult] = []
    try:
        for case in cases:
            results.append(_run_case(case))
    finally:
        log_event(
            case_id=None,
            actor=VERIFY_ACTOR,
            action="VERIFY_RUN_FINISHED",
            input_ref=run_name,
            output_ref=run_id,
            reason=f"Đã chạy tuần tự {len(results)}/{len(cases)} case Verify.",
        )
    return tuple(results)


def format_results(results: tuple[VerifyResult, ...]) -> str:
    """Tạo bảng văn bản ngắn gọn cho dòng lệnh."""
    header = "case_id | expected | actual | rule_id | PASS/FAIL | ms | timestamp (+07:00) | corpus"
    rows = [header, "-" * len(header)]
    for result in results:
        expected = f"{result.expected_decision}/{result.expected_type or '-'}"
        actual = f"{result.actual_decision}/{result.actual_type or '-'}"
        outcome = "PASS" if result.passed else "FAIL"
        rows.append(
            f"{result.case_id} | {expected} | {actual} | {result.rule_id} | {outcome} | "
            f"{result.elapsed_ms} | {result.timestamp} | {result.corpus_version}"
        )
    return "\n".join(rows)


def main(arguments: list[str] | None = None) -> int:
    """Chạy một bộ Verify từ dòng lệnh."""
    parser = argparse.ArgumentParser(description="Chạy Verify qua pipeline dùng chung.")
    parser.add_argument("--set", choices=tuple(CASE_SETS), required=True, dest="case_set")
    parser.add_argument("--case", dest="case_id")
    options = parser.parse_args(arguments)
    try:
        results = run_cases(
            CASE_SETS[options.case_set], run_name=options.case_set, case_id=options.case_id
        )
    except ValueError as error:
        parser.error(str(error))
    sys.stdout.write(f"{format_results(results)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
