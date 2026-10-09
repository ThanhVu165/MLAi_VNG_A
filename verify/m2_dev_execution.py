"""Bounded offline execution orchestrator for M2 Combined DEV probe.

Phạm vi: OFFLINE MOCK ONLY; cấm gọi live LLM provider, cấm mạng.
Tích hợp: frozen case loading -> offline adapter -> execution context -> capture -> assessment -> artifacts.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Callable, Protocol

from core.types import (
    CaseInput,
    CaseStatus,
    ChunkLabel,
    Decision,
    Domain,
    DraftReply,
    EscalationCard,
    EscalationType,
    EvidenceChunk,
    EvidenceResult,
    EvidenceStatus,
    PipelineResult,
    PolicyDecision,
)
from verify import m2_dev_assessment as dev
from verify.m2_live_budget import (
    DEFAULT_LEDGER_PATH,
    BudgetVerificationError as BudgetVerificationError,
    BudgetExceededError as BudgetExceededError,
    check_budget_authorization,
    verify_live_budget as verify_live_budget,
)

FIXTURE = Path(__file__).with_name("cases_m2_combined_dev.json")
FIXTURE_SHA256 = "d18cd77081c1ebb3bd72587d0a9cd438ecdbe5f06b0409ef7c61ba2408cccc04"


EXPECTED_CASE_IDS: tuple[str, ...] = tuple(
    f"M2DEV-{group}{i}" for group in ("A", "B", "C") for i in range(1, 5)
)
EXPECTED_GOLD_DISTRIBUTION: dict[str, int] = {
    "P01": 3,
    "P02": 3,
    "P03": 2,
    "P05": 4,
    "AUTO_REPLY": 4,
    "ESCALATE": 8,
}
SAFE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


@dataclass(frozen=True)
class AdapterOutput:
    result: PipelineResult
    config: dict[str, str] | None = None
    diagnostics: dev.CaptureDiagnostics | None = None


class ExecutionAdapter(Protocol):
    adapter_id: str

    def __call__(
        self,
        case_spec: dict[str, object],
        submitted_input: CaseInput,
        observation_id: str,
        mode: str,
    ) -> PipelineResult | AdapterOutput: ...


def _validate_safe_id(value: str, field_name: str) -> str:
    """Ngăn chặn path traversal từ case IDs, observation IDs và run IDs."""
    if not isinstance(value, str) or not value.strip() or not SAFE_ID_PATTERN.fullmatch(value):
        raise ValueError(
            f"PATH_TRAVERSAL_PREVENTED: {field_name} chứa ký tự không an toàn: {value!r}"
        )
    return value


def load_frozen_cases(fixture: Path = FIXTURE) -> tuple[dict[str, object], ...]:
    """Tải và thẩm định toàn diện 12 frozen cases từ fixture đã freeze.

    Xác minh:
    - Fixture final-bytes SHA-256.
    - Đúng 12 case IDs duy nhất theo danh mục định trước.
    - Phân bổ expected gold (P01=3, P02=3, P03=2, P05=4; AUTO=4, ESC=8).
    - Input schema đầy đủ, channel=verify, received_at timezone-aware.
    - Metadata status GOLD_VERIFIED_READY_FOR_FREEZE và rubric definitions.
    Fail closed, không tự ý sửa đổi input.
    """
    if not fixture.exists():
        raise FileNotFoundError(f"Fixture không tồn tại: {fixture}")
    raw_bytes = fixture.read_bytes()
    actual_hash = hashlib.sha256(raw_bytes).hexdigest()
    if actual_hash != FIXTURE_SHA256:
        raise ValueError("BLOCKED_FIXTURE_HASH_MISMATCH")

    try:
        cases_raw = json.loads(raw_bytes.decode("utf-8"))
    except Exception as error:
        raise ValueError("Fixture JSON không hợp lệ.") from error

    if not isinstance(cases_raw, list) or len(cases_raw) != 12:
        raise ValueError("Fixture phải chứa đúng 12 cases.")

    case_ids = [c.get("id") for c in cases_raw if isinstance(c, dict)]
    if tuple(case_ids) != EXPECTED_CASE_IDS:
        raise ValueError(f"Danh sách case IDs không khớp kỳ vọng: {case_ids}")

    distribution: dict[str, int] = {
        "P01": 0,
        "P02": 0,
        "P03": 0,
        "P05": 0,
        "AUTO_REPLY": 0,
        "ESCALATE": 0,
    }

    for item in cases_raw:
        if not isinstance(item, dict):
            raise ValueError("Mỗi case phải là dictionary.")
        cid = item.get("id")
        _validate_safe_id(str(cid), "case_id")

        dec = item.get("expected_decision")
        if dec not in ("AUTO_REPLY", "ESCALATE"):
            raise ValueError(f"Decision không hợp lệ: {dec} trong case {cid}")
        distribution[dec] += 1

        rule = item.get("expected_rule_id")
        if rule not in ("P01", "P02", "P03", "P05"):
            raise ValueError(f"Rule ID không hợp lệ: {rule} trong case {cid}")
        distribution[rule] += 1

        exp_type = item.get("expected_type")
        if dec == "AUTO_REPLY" and exp_type is not None:
            raise ValueError(f"AUTO_REPLY phải có expected_type=None trong case {cid}")
        if dec == "ESCALATE" and exp_type not in (
            "AUTHORITY_REQUIRED",
            "OUT_OF_POLICY",
            "FACT_UNRESOLVED",
        ):
            raise ValueError(f"ESCALATE có expected_type không hợp lệ trong case {cid}")

        inp = item.get("input")
        if not isinstance(inp, dict):
            raise ValueError(f"Case {cid} thiếu input payload.")

        required_keys = {"sender", "subject", "body", "received_at", "channel"}
        if not required_keys <= inp.keys():
            raise ValueError(f"Case {cid} thiếu trường bắt buộc trong input.")

        if inp.get("channel") != "verify":
            raise ValueError(f"Case {cid} phải có channel='verify'.")

        received_at_str = inp.get("received_at")
        if not isinstance(received_at_str, str):
            raise ValueError(f"Case {cid} received_at phải là string.")
        try:
            dt = datetime.fromisoformat(received_at_str)
            if dt.tzinfo is None or dt.utcoffset() is None:
                raise ValueError("received_at thiếu timezone.")
        except Exception as error:
            raise ValueError(f"Case {cid} received_at không hợp lệ.") from error

        meta = item.get("meta")
        if not isinstance(meta, dict):
            raise ValueError(f"Case {cid} thiếu meta.")
        if meta.get("status") != "GOLD_VERIFIED_READY_FOR_FREEZE":
            raise ValueError(f"Case {cid} meta.status chưa đóng băng.")
        for group in ("pass_criteria", "fail_signals", "forbidden_assumptions"):
            if not isinstance(meta.get(group), list) or not meta[group]:
                raise ValueError(f"Case {cid} thiếu rubric {group}.")

    if distribution != EXPECTED_GOLD_DISTRIBUTION:
        raise ValueError(
            f"Phân bổ gold không khớp: kỳ vọng {EXPECTED_GOLD_DISTRIBUTION}, thực tế {distribution}"
        )

    return tuple(cases_raw)


class DeterministicMockAdapter:
    """Offline synthetic mock adapter cho testing và diagnostic orchestrator.

    Hoàn toàn deterministic, không gọi mạng, không đọc key, dán nhãn SYNTHETIC rõ ràng.
    """

    adapter_id: str = "deterministic_offline_mock"
    is_offline_mock: bool = True

    def __init__(
        self,
        *,
        custom_result_factory: (
            Callable[[dict[str, object], CaseInput, str], PipelineResult] | None
        ) = None,
        force_error: bool = False,
        force_adapter_exception: bool = False,
        unsupported_options: list[str] | None = None,
    ):
        self.custom_result_factory = custom_result_factory
        self.force_error = force_error
        self.force_adapter_exception = force_adapter_exception
        self.unsupported_options = unsupported_options

    def __call__(
        self,
        case_spec: dict[str, object],
        submitted_input: CaseInput,
        observation_id: str,
        mode: str,
    ) -> AdapterOutput:
        if mode.upper() == "LIVE":
            raise ValueError("LIVE_EXECUTION_NOT_ENABLED")

        if self.force_adapter_exception:
            raise RuntimeError("SIMULATED_MOCK_ADAPTER_EXCEPTION")

        if self.custom_result_factory is not None:
            res = self.custom_result_factory(case_spec, submitted_input, observation_id)
            return AdapterOutput(
                result=res,
                config={
                    "LLM_PROVIDER": "openai",
                    "OPENAI_MODEL": "gpt-6-luna",
                    "LLM_MODE": "replay",
                },
                diagnostics=dev.CaptureDiagnostics(),
            )

        now = datetime(2026, 10, 8, tzinfo=timezone.utc)

        if self.force_error:
            pipeline_case_id = f"synthetic-case-{observation_id}"
            pipeline_trace_id = f"synthetic-trace-{observation_id}"
            policy_decision = PolicyDecision(
                Decision.ERROR,
                None,
                "TECHNICAL_ERROR",
                "SYNTHETIC technical pipeline error.",
                [],
                "synthetic-corpus",
            )
            res = PipelineResult(
                case_id=pipeline_case_id,
                trace_id=pipeline_trace_id,
                status=CaseStatus.ERROR,
                decision=policy_decision,
                extraction=None,
                evidence=None,
                draft=None,
                card=None,
                corpus_version="synthetic-corpus",
                step_latencies_ms={"R0": 1, "R1": 2},
                started_at=now,
                finished_at=now,
            )
            return AdapterOutput(
                result=res,
                config={
                    "LLM_PROVIDER": "openai",
                    "OPENAI_MODEL": "gpt-6-luna",
                    "LLM_MODE": "replay",
                },
                diagnostics=dev.CaptureDiagnostics(),
            )

        expected_dec_str = str(case_spec["expected_decision"])
        decision = Decision(expected_dec_str)
        exp_type_str = case_spec.get("expected_type")
        kind = EscalationType(str(exp_type_str)) if exp_type_str else None
        rule_id = str(case_spec["expected_rule_id"])

        chunk = EvidenceChunk(
            chunk_id="PK-2026-204:seed:1" if "PK" in rule_id else "RH-2026-101:seed:1",
            doc_id="PK-2026-204" if "PK" in rule_id else "RH-2026-101",
            breadcrumb="Điều 1",
            text="SYNTHETIC: Căn cứ quy định áp dụng.",
            domain=Domain.GRADE_APPEAL if "PK" in rule_id else Domain.COURSE_WITHDRAWAL,
            label=ChunkLabel.AUTO_ANSWERABLE,
            score=0.9,
            effective_from=date(2026, 8, 15),
            effective_to=None,
            applies_to=[],
            cohorts=[],
            transitional_clause=False,
            conflict_flag=False,
        )

        card: EscalationCard | None = None
        draft: DraftReply | None = None

        if decision is Decision.ESCALATE:
            options = (
                self.unsupported_options
                if self.unsupported_options is not None
                else ["Đồng ý xử lý theo thẩm quyền", "Không đồng ý xử lý theo thẩm quyền"]
            )
            card = EscalationCard(
                summary="SYNTHETIC: Hồ sơ cần chuyên viên xem xét.",
                facts=["Có tình tiết cần người có thẩm quyền xác minh."],
                basis=[(chunk.breadcrumb, chunk.text)],
                question="Chuyên viên có thể xác nhận hướng xử lý cho trường hợp này không?",
                options=options,
                escalation_type=kind or EscalationType.AUTHORITY_REQUIRED,
                partial_draft=None,
            )
        elif decision is Decision.AUTO_REPLY:
            draft = DraftReply(
                subject=f"SYNTHETIC: Trả lời về {submitted_input.subject}",
                body=f"Căn cứ quy định, thông tin giải đáp như sau. [{chunk.chunk_id}]",
                citations=[chunk.chunk_id],
                grounded=True,
                guard_failures=[],
            )

        policy_decision = PolicyDecision(
            decision=decision,
            escalation_type=kind,
            rule_id=rule_id,
            reason="SYNTHETIC deterministic offline mock result.",
            evidence_ids=[chunk.chunk_id],
            corpus_version="synthetic-corpus",
        )

        pipeline_case_id = f"synthetic-case-{observation_id}"
        pipeline_trace_id = f"synthetic-trace-{observation_id}"

        res = PipelineResult(
            case_id=pipeline_case_id,
            trace_id=pipeline_trace_id,
            status=CaseStatus.AWAITING_HUMAN if card else CaseStatus.PENDING_SEND,
            decision=policy_decision,
            extraction=None,
            evidence=EvidenceResult(EvidenceStatus.OK, [chunk], []),
            draft=draft,
            card=card,
            corpus_version="synthetic-corpus",
            step_latencies_ms={"R0": 1, "R1": 2, "R2": 10, "R4": 15, "R6": 5},
            started_at=now,
            finished_at=now,
        )

        return AdapterOutput(
            result=res,
            config={
                "LLM_PROVIDER": "openai",
                "OPENAI_MODEL": "gpt-6-luna",
                "LLM_MODE": "replay",
            },
            diagnostics=dev.CaptureDiagnostics(
                logical_calls=[
                    {
                        "step": "R2",
                        "ok": True,
                        "latency_ms": 10,
                        "model": "synthetic",
                        "error_class": None,
                    }
                ]
            ),
        )


@dataclass(frozen=True)
class CaseExecutionSummary:
    case_id: str
    observation_id: str
    fixture_sha256: str
    submitted_input_sha256: str
    capture_sha256: str | None
    result_case_id: str | None
    result_trace_id: str | None
    actual_decision: str | None
    actual_escalation_type: str | None
    actual_rule_id: str | None
    expected_decision: str
    expected_type: str | None
    expected_rule_id: str
    technical_status: str  # "OK", "ADAPTER_EXCEPTION", "IDENTITY_MISMATCH", "TECHNICAL_ERROR", etc.
    assessment_verdict: str | None  # "PASS", "FAIL", "REVIEW_REQUIRED", "TECHNICAL_ERROR", None
    dimension_verdicts: dict[str, str] | None
    criterion_review_status: dict[str, str] | None
    artifact_paths: dict[str, str]
    run_timestamp: str
    run_mode: str
    corpus_version: str | None
    observed_provider_attempts: list[dict[str, object]] | None = None
    observed_logical_calls: list[dict[str, object]] | None = None
    observed_cost: float | None = None


@dataclass(frozen=True)
class RunExecutionSummary:
    run_id: str
    run_mode: str
    run_timestamp: str
    fixture_sha256: str
    total_cases: int
    completed_cases: int
    failed_cases: int
    verdicts: dict[str, int]
    live_budget_status: dict[str, object]
    cases: list[CaseExecutionSummary]
    artifacts_directory: str


def _safe_write_json(path: Path, data: object) -> None:
    sanitized = dev._safe(data)
    with path.open("x", encoding="utf-8") as f:
        f.write(dev._json(sanitized) + "\n")


def _adapter_failure(error: Exception) -> dict[str, str]:
    # Không đọc str/repr/traceback hay __name__ của unknown type.
    allowed = {
        RuntimeError: ("RuntimeError", "ADAPTER_RUNTIME_ERROR"),
        TypeError: ("TypeError", "ADAPTER_RESULT_TYPE_ERROR"),
        ValueError: ("ValueError", "ADAPTER_VALUE_ERROR"),
        TimeoutError: ("TimeoutError", "ADAPTER_TIMEOUT"),
        OSError: ("OSError", "ADAPTER_IO_ERROR"),
    }
    safe = allowed.get(type(error))
    record = {
        "error_category": "UNCLASSIFIED_ADAPTER_ERROR",
        "error_code": "ADAPTER_INVOCATION_FAILED",
    }
    if safe is not None:
        record.update(exception_class=safe[0], error_category=safe[1])
    return record


def _validate_mode(mode: str) -> None:
    if mode.strip().upper() == "LIVE":
        raise ValueError("LIVE_EXECUTION_NOT_ENABLED")
    if mode.strip().upper() != "OFFLINE_MOCK":
        raise ValueError("UNSUPPORTED_MODE")


def orchestrate_m2_dev_run(
    *,
    output_dir: Path,
    adapter: DeterministicMockAdapter | None = None,
    mode: str = "OFFLINE_MOCK",
    case_ids: list[str] | tuple[str, ...] | None = None,
    fixture_path: Path = FIXTURE,
    ledger_path: Path = DEFAULT_LEDGER_PATH,
    run_id: str | None = None,
    human_reviews: dict[str, dev.HumanReview] | None = None,
) -> RunExecutionSummary:
    """Operational OFFLINE: exact built-in type, không nhận callback/plugin."""
    _validate_mode(mode)
    chosen = adapter if adapter is not None else DeterministicMockAdapter()
    if type(chosen) is not DeterministicMockAdapter or chosen.custom_result_factory is not None:
        raise ValueError("ADAPTER_NOT_TRUSTED_BUILTIN")
    return _orchestrate_m2_dev_run(
        output_dir=output_dir,
        adapter=chosen,
        mode=mode,
        case_ids=case_ids,
        fixture_path=fixture_path,
        ledger_path=ledger_path,
        run_id=run_id,
        human_reviews=human_reviews,
    )


def orchestrate_m2_dev_test_run(
    *,
    adapter: ExecutionAdapter,
    output_dir: Path,
    mode: str = "OFFLINE_MOCK",
    case_ids: list[str] | tuple[str, ...] | None = None,
    fixture_path: Path = FIXTURE,
    ledger_path: Path = DEFAULT_LEDGER_PATH,
    run_id: str | None = None,
    human_reviews: dict[str, dev.HumanReview] | None = None,
) -> RunExecutionSummary:
    """TEST-ONLY injection; caller tests phải chặn socket/provider/pipeline thật."""
    _validate_mode(mode)
    return _orchestrate_m2_dev_run(
        output_dir=output_dir,
        adapter=adapter,
        mode=mode,
        case_ids=case_ids,
        fixture_path=fixture_path,
        ledger_path=ledger_path,
        run_id=run_id,
        human_reviews=human_reviews,
    )


def _orchestrate_m2_dev_run(
    *,
    output_dir: Path,
    adapter: ExecutionAdapter | None = None,
    mode: str = "OFFLINE_MOCK",
    case_ids: list[str] | tuple[str, ...] | None = None,
    fixture_path: Path = FIXTURE,
    ledger_path: Path = DEFAULT_LEDGER_PATH,
    run_id: str | None = None,
    human_reviews: dict[str, dev.HumanReview] | None = None,
) -> RunExecutionSummary:
    """Thực thi orchestrator an toàn cho 12 frozen cases DEV probe.

    Chỉ hỗ trợ OFFLINE_MOCK. Từ chối dứt khoát mọi yêu cầu LIVE.
    Thực hiện contract identity nghiêm ngặt tại execution boundary.
    """
    if mode.strip().upper() == "LIVE":
        raise ValueError("LIVE_EXECUTION_NOT_ENABLED")
    if mode.strip().upper() != "OFFLINE_MOCK":
        raise ValueError(f"UNSUPPORTED_MODE: Chỉ hỗ trợ OFFLINE_MOCK trong task này, nhận {mode!r}")

    exec_adapter = adapter
    assert exec_adapter is not None
    budget_info = check_budget_authorization(
        is_live=False, requested_count=12, ledger_path=ledger_path
    )

    all_cases = load_frozen_cases(fixture_path)
    if case_ids is not None:
        target_ids = set(case_ids)
        available_ids = {c["id"] for c in all_cases}
        if not target_ids <= available_ids:
            raise ValueError(
                f"Các case ID không tồn tại trong frozen fixture: {target_ids - available_ids}"
            )
        cases_to_run = [c for c in all_cases if c["id"] in target_ids]
    else:
        cases_to_run = list(all_cases)

    run_timestamp = datetime.now(timezone.utc).isoformat()
    raw_run_id = (
        run_id
        or f"dev_run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"
    )
    validated_run_id = _validate_safe_id(raw_run_id, "run_id")

    resolved_output = output_dir.resolve()
    if resolved_output.exists():
        raise FileExistsError(
            f"ARTIFACT_DIRECTORY_EXISTS: Thư mục kết quả đã tồn tại: {resolved_output}"
        )

    resolved_output.mkdir(parents=True, exist_ok=False)
    cases_dir = resolved_output / "cases"
    cases_dir.mkdir(parents=True, exist_ok=False)

    case_summaries: list[CaseExecutionSummary] = []
    verdict_counts: dict[str, int] = {
        "PASS": 0,
        "FAIL": 0,
        "REVIEW_REQUIRED": 0,
        "TECHNICAL_ERROR": 0,
        "ERROR": 0,
    }

    for case_spec in cases_to_run:
        cid = str(case_spec["id"])
        _validate_safe_id(cid, "case_id")
        obs_id = _validate_safe_id(f"obs_{validated_run_id}_{cid}", "observation_id")

        raw_inp = case_spec["input"]
        assert isinstance(raw_inp, dict)

        submitted_payload = CaseInput(
            sender=raw_inp["sender"],
            subject=raw_inp["subject"],
            body=raw_inp["body"],
            received_at=datetime.fromisoformat(raw_inp["received_at"]),
            channel=raw_inp["channel"],
            external_id=raw_inp.get("external_id"),
        )

        submitted_snapshot = deepcopy(submitted_payload)
        submitted_hash_before = dev.input_hash(submitted_snapshot)
        expected_hash = dev.input_hash(case_spec["input"])

        if submitted_hash_before != expected_hash:
            raise ValueError("INPUT_IDENTITY_MISMATCH: Payload không khớp frozen input.")

        case_target_dir = cases_dir / cid
        if not case_target_dir.resolve().is_relative_to(resolved_output):
            raise ValueError(
                f"PATH_TRAVERSAL_PREVENTED: Case directory nằm ngoài output_dir: {cid}"
            )

        adapter_error: dict[str, str] | None = None
        adapter_output: AdapterOutput | None = None

        try:
            raw_out = exec_adapter(
                case_spec=case_spec,
                submitted_input=submitted_payload,
                observation_id=obs_id,
                mode=mode,
            )
            if isinstance(raw_out, AdapterOutput):
                adapter_output = raw_out
            elif isinstance(raw_out, PipelineResult):
                adapter_output = AdapterOutput(result=raw_out)
            else:
                raise TypeError(f"Adapter trả về kiểu không hợp lệ: {type(raw_out)}")
        except Exception as exc:
            adapter_error = _adapter_failure(exc)

        # Kiểm tra payload không bị mutate bởi adapter
        submitted_hash_after = dev.input_hash(submitted_payload)
        if submitted_hash_after != submitted_hash_before:
            raise ValueError("INPUT_IDENTITY_MUTATED: Payload bị thay đổi sau khi gọi adapter.")

        if adapter_error is not None or adapter_output is None:
            case_target_dir.mkdir(parents=True, exist_ok=False)
            failure_record = {
                "case_id": cid,
                "observation_id": obs_id,
                "technical_status": "ADAPTER_EXCEPTION",
                **(
                    adapter_error
                    or {
                        "error_category": "UNCLASSIFIED_ADAPTER_ERROR",
                        "error_code": "ADAPTER_INVOCATION_FAILED",
                    }
                ),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            _safe_write_json(case_target_dir / "execution_failure.json", failure_record)
            verdict_counts["ERROR"] += 1
            case_summaries.append(
                CaseExecutionSummary(
                    case_id=cid,
                    observation_id=obs_id,
                    fixture_sha256=FIXTURE_SHA256,
                    submitted_input_sha256=submitted_hash_before,
                    capture_sha256=None,
                    result_case_id=None,
                    result_trace_id=None,
                    actual_decision=None,
                    actual_escalation_type=None,
                    actual_rule_id=None,
                    expected_decision=str(case_spec["expected_decision"]),
                    expected_type=case_spec.get("expected_type"),
                    expected_rule_id=str(case_spec["expected_rule_id"]),
                    technical_status="ADAPTER_EXCEPTION",
                    assessment_verdict="ERROR",
                    dimension_verdicts=None,
                    criterion_review_status=None,
                    artifact_paths={"failure": str(case_target_dir / "execution_failure.json")},
                    run_timestamp=run_timestamp,
                    run_mode=mode,
                    corpus_version=None,
                )
            )
            continue

        pipeline_res = adapter_output.result
        config_labels = adapter_output.config or {
            "LLM_PROVIDER": "openai",
            "OPENAI_MODEL": "gpt-6-luna",
            "LLM_MODE": "replay",
        }
        diagnostics = adapter_output.diagnostics or dev.CaptureDiagnostics()

        # Tạo execution context tại invocation boundary
        context = dev.execution_context(
            submitted_snapshot,
            pipeline_res,
            case_id=cid,
            observation_id=obs_id,
            fixture=fixture_path,
        )

        captured = dev.capture_result(
            pipeline_res,
            case_id=cid,
            observation_id=obs_id,
            execution=context,
            config=config_labels,
            diagnostics=diagnostics,
            fixture=fixture_path,
        )

        review = human_reviews.get(cid) if human_reviews else None
        assessment = dev.write_artifacts(
            case_target_dir,
            captured,
            review=review,
            fixture=fixture_path,
        )

        v = assessment.verdict
        verdict_counts[v] = verdict_counts.get(v, 0) + 1

        tech_status = (
            "TECHNICAL_ERROR" if assessment.dimensions["technical_error"].status == "FAIL" else "OK"
        )

        dim_verdicts = {k: d.status for k, d in assessment.dimensions.items()}
        crit_verdicts = {k: c.status for k, c in assessment.criteria.items()}

        case_summaries.append(
            CaseExecutionSummary(
                case_id=cid,
                observation_id=obs_id,
                fixture_sha256=FIXTURE_SHA256,
                submitted_input_sha256=submitted_hash_before,
                capture_sha256=assessment.capture_sha256,
                result_case_id=pipeline_res.case_id,
                result_trace_id=pipeline_res.trace_id,
                actual_decision=str(pipeline_res.decision.decision),
                actual_escalation_type=(
                    str(pipeline_res.decision.escalation_type)
                    if pipeline_res.decision.escalation_type
                    else None
                ),
                actual_rule_id=str(pipeline_res.decision.rule_id),
                expected_decision=str(case_spec["expected_decision"]),
                expected_type=case_spec.get("expected_type"),
                expected_rule_id=str(case_spec["expected_rule_id"]),
                technical_status=tech_status,
                assessment_verdict=assessment.verdict,
                dimension_verdicts=dim_verdicts,
                criterion_review_status=crit_verdicts,
                artifact_paths={
                    "capture": str(case_target_dir / "capture.json"),
                    "assessment": str(case_target_dir / "assessment.json"),
                    "report": str(case_target_dir / "report.md"),
                },
                run_timestamp=run_timestamp,
                run_mode=mode,
                corpus_version=pipeline_res.corpus_version,
                observed_provider_attempts=diagnostics.provider_attempts,
                observed_logical_calls=diagnostics.logical_calls,
                observed_cost=diagnostics.cost,
            )
        )

    completed = sum(1 for c in case_summaries if c.technical_status in ("OK", "TECHNICAL_ERROR"))
    failed = len(case_summaries) - completed

    summary = RunExecutionSummary(
        run_id=validated_run_id,
        run_mode=mode,
        run_timestamp=run_timestamp,
        fixture_sha256=FIXTURE_SHA256,
        total_cases=len(cases_to_run),
        completed_cases=completed,
        failed_cases=failed,
        verdicts=verdict_counts,
        live_budget_status={
            "total_budget": budget_info.total_budget,
            "used_observations_before": budget_info.used_observations,
            "remaining_budget": budget_info.remaining_budget,
            "live_consumed_this_run": 0,
            "is_verified": budget_info.is_verified,
            "authorization": "BUDGET_VERIFIED" if budget_info.is_verified else "BUDGET_UNVERIFIED",
            "source_file": budget_info.source_file,
        },
        cases=case_summaries,
        artifacts_directory=str(resolved_output),
    )

    _safe_write_json(resolved_output / "run_summary.json", asdict(summary))

    report_md_lines = [
        f"# M2 Combined DEV Orchestrator Run Report — {validated_run_id}",
        "",
        f"- **Mode:** {mode} (OFFLINE MOCK)",
        f"- **Timestamp:** {run_timestamp}",
        f"- **Fixture SHA-256:** `{FIXTURE_SHA256}`",
        f"- **Total cases:** {len(cases_to_run)}",
        f"- **Completed cases:** {completed}",
        f"- **Failed cases:** {failed}",
        f"- **LIVE budget consumed:** 0 / {budget_info.remaining_budget} remaining",
        "",
        "## Verdicts Breakdown",
        "",
        "| Verdict | Count |",
        "| --- | --- |",
    ]
    for vk, vc in verdict_counts.items():
        report_md_lines.append(f"| {vk} | {vc} |")

    report_md_lines += [
        "",
        "## Case Details",
        "",
        "| Case ID | Expected | Actual Route | Status | Verdict | Capture SHA |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for c in case_summaries:
        exp_str = f"{c.expected_decision} ({c.expected_rule_id})"
        act_str = f"{c.actual_decision} ({c.actual_rule_id})" if c.actual_decision else "N/A"
        c_hash = (c.capture_sha256[:10] + "...") if c.capture_sha256 else "None"
        report_md_lines.append(
            f"| {c.case_id} | {exp_str} | {act_str} | {c.technical_status} | {c.assessment_verdict} | `{c_hash}` |"
        )

    with (resolved_output / "run_report.md").open("x", encoding="utf-8") as f:
        f.write("\n".join(report_md_lines) + "\n")

    return summary


def main(argv: list[str] | None = None) -> int:
    """CLI an toàn thuần offline; từ chối dứt khoát execution mode LIVE."""
    parser = argparse.ArgumentParser(
        description="M2 Combined DEV Execution Orchestrator (OFFLINE MOCK ONLY)."
    )
    parser.add_argument(
        "--mode",
        choices=["offline_mock", "dry_run"],
        default="offline_mock",
        help="Chế độ thực thi (offline_mock hoặc dry_run). Cấm LIVE.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Thư mục ghi artifacts. Nếu để trống, sẽ tạo thư mục mới an toàn.",
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        default=FIXTURE,
        help="Đường dẫn file frozen fixture JSON.",
    )
    parser.add_argument(
        "--case",
        type=str,
        default=None,
        help="Chỉ chạy duy nhất một case ID cụ thể.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Từ chối với LIVE_EXECUTION_NOT_ENABLED.",
    )
    args = parser.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

    if args.live:
        sys.stderr.write("LIVE_EXECUTION_NOT_ENABLED: Live execution is not permitted.\n")
        return 1

    if args.mode == "dry_run":
        cases = load_frozen_cases(args.fixture)
        budget = check_budget_authorization(0, is_live=False)
        sys.stdout.write(
            f"DRY_RUN_VALIDATION_OK: Verified {len(cases)} cases. "
            f"Fixture SHA-256: {FIXTURE_SHA256}. "
            f"LIVE budget: {'BUDGET_VERIFIED' if budget.is_verified else 'BUDGET_UNVERIFIED'}.\n"
        )
        return 0

    default_output = args.output_dir
    if default_output is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        default_output = Path("data/validation") / f"m2_dev_mock_{stamp}_{os.urandom(3).hex()}"

    case_filter = [args.case] if args.case else None
    summary = orchestrate_m2_dev_run(
        output_dir=default_output,
        mode="OFFLINE_MOCK",
        case_ids=case_filter,
        fixture_path=args.fixture,
    )
    sys.stdout.write(
        f"M2_DEV_ORCHESTRATOR_RUN_OK: Completed {summary.completed_cases}/{summary.total_cases} cases at {summary.artifacts_directory}.\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
