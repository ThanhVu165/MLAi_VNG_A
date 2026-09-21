from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from secrets import randbits
from time import perf_counter, time_ns
from typing import TypeVar
from uuid import uuid4

from corpus.api import get_corpus_version
from core.types import (
    CaseInput,
    CaseStatus,
    Decision,
    EscalationType,
    PipelineResult,
    PolicyDecision,
)
from infra.audit import log_event
from infra.db import execute, now_iso, to_utc_iso

logger = logging.getLogger(__name__)

MILLISECONDS_PER_SECOND = 1_000
NANOSECONDS_PER_MILLISECOND = 1_000_000
ULID_RANDOM_BITS = 80
CROCKFORD_BASE32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
FAIL_SAFE_REASON = "Hệ thống không hoàn tất được bước xử lý nên dừng lại thay vì phỏng đoán."
INVALID_INPUT_REASON = "Email thiếu thông tin bắt buộc để tiếp nhận xử lý."
RECEIVED_REASON = "Đã tiếp nhận email để xử lý theo quy trình."

T = TypeVar("T")


@dataclass(frozen=True)
class _Intake:
    case_id: str
    trace_id: str
    corpus_version: str
    status: CaseStatus


def _new_ulid() -> str:
    value = (time_ns() // NANOSECONDS_PER_MILLISECOND << ULID_RANDOM_BITS) | randbits(
        ULID_RANDOM_BITS
    )
    return "".join(CROCKFORD_BASE32[value >> (index * 5) & 31] for index in range(25, -1, -1))


def _is_missing_required(inp: CaseInput) -> bool:
    return not all((inp.sender.strip(), inp.subject.strip(), inp.body.strip())) or (
        inp.received_at.tzinfo is None or inp.received_at.utcoffset() is None
    )


def _r0_intake(inp: CaseInput, actor: str, case_id: str, trace_id: str) -> _Intake:
    corpus_version = get_corpus_version()
    status = CaseStatus.INVALID_INPUT if _is_missing_required(inp) else CaseStatus.RECEIVED
    execute(
        """
        INSERT INTO cases (
            case_id, trace_id, channel, sender, subject, body_raw, received_at, created_at,
            status, corpus_version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            case_id,
            trace_id,
            inp.channel,
            inp.sender,
            inp.subject,
            inp.body,
            to_utc_iso(inp.received_at),
            now_iso(),
            status,
            corpus_version,
        ),
    )
    log_event(
        case_id=case_id,
        actor=actor,
        action="CASE_RECEIVED",
        input_ref=case_id,
        reason=INVALID_INPUT_REASON if status is CaseStatus.INVALID_INPUT else RECEIVED_REASON,
        corpus_version=corpus_version,
    )
    return _Intake(case_id, trace_id, corpus_version, status)


def _r1_sanitize() -> None:
    return None


def _r2_extract() -> None:
    return None


def _r3_prepolicy() -> None:
    return None


def _r4_retrieve() -> None:
    return None


def _r5_validate_evidence() -> None:
    return None


def _r6_policy() -> None:
    return None


def _r7_generate() -> None:
    return None


def _r8_guard() -> None:
    return None


def _r9_queue_or_send() -> None:
    return None


def _r10_human_decision() -> None:
    return None


def _r11_resume() -> None:
    return None


def _r12_approve() -> None:
    return None


def _r13_dispatch() -> None:
    return None


def _r14_audit_and_telemetry() -> None:
    return None


STEPS: tuple[tuple[str, Callable[[], None]], ...] = (
    ("R1", _r1_sanitize),
    ("R2", _r2_extract),
    ("R3", _r3_prepolicy),
    ("R4", _r4_retrieve),
    ("R5", _r5_validate_evidence),
    ("R6", _r6_policy),
    ("R7", _r7_generate),
    ("R8", _r8_guard),
    ("R9", _r9_queue_or_send),
    ("R10", _r10_human_decision),
    ("R11", _r11_resume),
    ("R12", _r12_approve),
    ("R13", _r13_dispatch),
    ("R14", _r14_audit_and_telemetry),
)


def _run_step(name: str, step: Callable[[], T], latencies: dict[str, int]) -> T:
    started = perf_counter()
    try:
        return step()
    finally:
        latencies[name] = round((perf_counter() - started) * MILLISECONDS_PER_SECOND)


def _fail_safe_decision(corpus_version: str) -> PolicyDecision:
    return PolicyDecision(
        decision=Decision.ESCALATE,
        escalation_type=EscalationType.FACT_UNRESOLVED,
        rule_id="P04",
        reason=FAIL_SAFE_REASON,
        evidence_ids=[],
        corpus_version=corpus_version,
    )


def _invalid_input_decision(corpus_version: str) -> PolicyDecision:
    return PolicyDecision(
        decision=Decision.INVALID_INPUT,
        escalation_type=None,
        rule_id="R0",
        reason=INVALID_INPUT_REASON,
        evidence_ids=[],
        corpus_version=corpus_version,
    )


def _result(
    intake: _Intake,
    status: CaseStatus,
    decision: PolicyDecision,
    latencies: dict[str, int],
    started_at: datetime,
) -> PipelineResult:
    return PipelineResult(
        case_id=intake.case_id,
        trace_id=intake.trace_id,
        status=status,
        decision=decision,
        extraction=None,
        evidence=None,
        draft=None,
        card=None,
        corpus_version=intake.corpus_version,
        step_latencies_ms=latencies,
        started_at=started_at,
        finished_at=datetime.now(timezone.utc),
    )


def process_case(inp: CaseInput, *, actor: str = "SYSTEM") -> PipelineResult:
    """Run the pipeline and return a fail-safe result for every ordinary error."""
    started_at = datetime.now(timezone.utc)
    case_id = f"c_{_new_ulid()}"
    trace_id = str(uuid4())
    latencies: dict[str, int] = {}
    intake: _Intake | None = None
    try:
        intake = _run_step("R0", lambda: _r0_intake(inp, actor, case_id, trace_id), latencies)
        if intake.status is CaseStatus.INVALID_INPUT:
            return _result(
                intake,
                intake.status,
                _invalid_input_decision(intake.corpus_version),
                latencies,
                started_at,
            )
        for name, step in STEPS:
            _run_step(name, step, latencies)
        return _result(
            intake,
            CaseStatus.AWAITING_HUMAN,
            _fail_safe_decision(intake.corpus_version),
            latencies,
            started_at,
        )
    except Exception:
        logger.exception("Pipeline failed safely", extra={"case_id": case_id, "trace_id": trace_id})
        failed_intake = intake or _Intake(case_id, trace_id, "", CaseStatus.ERROR)
        return _result(
            failed_intake,
            CaseStatus.ERROR,
            _fail_safe_decision(failed_intake.corpus_version),
            latencies,
            started_at,
        )
