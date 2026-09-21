from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime, timezone
from time import perf_counter
from uuid import uuid4

from core.types import (
    CaseInput,
    CaseStatus,
    Decision,
    EscalationType,
    PipelineResult,
    PolicyDecision,
)

logger = logging.getLogger(__name__)

MILLISECONDS_PER_SECOND = 1_000
FAIL_SAFE_REASON = "Hệ thống không hoàn tất được bước xử lý nên dừng lại thay vì phỏng đoán."


def _r0_intake() -> None:
    return None


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
    ("R0", _r0_intake),
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


def _run_step(name: str, step: Callable[[], None], latencies: dict[str, int]) -> None:
    started = perf_counter()
    try:
        step()
    finally:
        latencies[name] = round((perf_counter() - started) * MILLISECONDS_PER_SECOND)


def _fail_safe_decision() -> PolicyDecision:
    return PolicyDecision(
        decision=Decision.ESCALATE,
        escalation_type=EscalationType.FACT_UNRESOLVED,
        rule_id="P04",
        reason=FAIL_SAFE_REASON,
        evidence_ids=[],
        corpus_version="",
    )


def process_case(inp: CaseInput, *, actor: str = "SYSTEM") -> PipelineResult:
    """Run the runtime scaffold and return a fail-safe result for every ordinary error."""
    del inp, actor
    started_at = datetime.now(timezone.utc)
    case_id = str(uuid4())
    trace_id = str(uuid4())
    latencies: dict[str, int] = {}
    try:
        for name, step in STEPS:
            _run_step(name, step, latencies)
        status = CaseStatus.AWAITING_HUMAN
    except Exception:
        logger.exception("Pipeline failed safely", extra={"case_id": case_id, "trace_id": trace_id})
        status = CaseStatus.ERROR

    return PipelineResult(
        case_id=case_id,
        trace_id=trace_id,
        status=status,
        decision=_fail_safe_decision(),
        extraction=None,
        evidence=None,
        draft=None,
        card=None,
        corpus_version="",
        step_latencies_ms=latencies,
        started_at=started_at,
        finished_at=datetime.now(timezone.utc),
    )
