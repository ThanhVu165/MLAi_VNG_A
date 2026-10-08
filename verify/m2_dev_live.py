"""Entrypoint Combined DEV LIVE có explicit run authorization; mặc định disabled."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import logging
import math
import os
from pathlib import Path
import sys
from threading import Lock
from typing import Iterator

from core.types import CaseInput, Decision
from verify import m2_dev_assessment as dev
from verify import m2_dev_execution as execution
from verify.m2_live_budget import (
    DEFAULT_LEDGER_PATH,
    check_budget_authorization,
    record_live_observation,
)

LIVE_CONFIG = {
    "LLM_PROVIDER": "openai",
    "OPENAI_MODEL": "gpt-6-luna",
    "OPENAI_REASONING_EFFORT": "none",
    "LLM_MODE": "live",
    "LLM_CACHE": "0",
}
_RUNTIME_LOCK = Lock()
ATTEMPT_FIELDS = {
    "event",
    "case_id",
    "call_id",
    "step",
    "attempt_index",
    "elapsed_ms",
    "effective_timeout_s",
    "attempts_remaining_before",
    "attempts_remaining_after",
    "remaining_case_time_s",
    "provider",
    "model",
    "success",
    "retryable",
    "will_retry",
    "retry_backoff_ms",
    "stop_reason",
    "exception_class",
    "http_status",
    "provider_code",
}


@dataclass(frozen=True)
class LiveRunAuthorization:
    run_id: str
    approved_case_ids: tuple[str, ...]
    max_cases: int
    max_cost_usd: float
    approval_reference: str


@dataclass(frozen=True)
class LiveRunResult:
    run_id: str
    run_mode: str
    attempted_observations: int
    stop_reason: str
    observed_cost_usd: float | None
    cases: list[dict[str, object]]


class _AttemptObserver(logging.Handler):
    """Chỉ extra metadata hiện có; không format message/prompt/exception."""

    def __init__(self, case_id: str) -> None:
        super().__init__()
        self.case_id = case_id
        self.attempts: list[dict[str, object]] = []

    def emit(self, record: logging.LogRecord) -> None:
        event = getattr(record, "provider_attempt", None)
        if isinstance(event, dict) and event.get("case_id") == self.case_id:
            self.attempts.append({k: v for k, v in event.items() if k in ATTEMPT_FIELDS})


@contextmanager
def _live_runtime(database: Path) -> Iterator[None]:
    # Global DB/env chỉ dùng trong standalone runner tuần tự; không thread-safe với app.
    from infra import db

    with _RUNTIME_LOCK:
        previous_db = db.DEFAULT_DATABASE_PATH
        previous_env = {key: os.environ.get(key) for key in LIVE_CONFIG}
        try:
            db.DEFAULT_DATABASE_PATH = database
            os.environ.update(LIVE_CONFIG)
            yield
        finally:
            db.DEFAULT_DATABASE_PATH = previous_db
            for key, value in previous_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


class LivePipelineAdapter:
    """Production process_case, fresh DB/corpus; không đọc gold để tạo output."""

    def invoke(
        self, payload: CaseInput, *, case_id: str, database: Path
    ) -> execution.AdapterOutput:
        from infra import db, llm

        if database.exists():
            raise ValueError("LIVE_DATABASE_NOT_FRESH")
        observer = _AttemptObserver(case_id)
        self.diagnostics = dev.CaptureDiagnostics(provider_attempts=observer.attempts, cost=None)
        with _live_runtime(database):
            db.initialize_database(database)
            # corpus.__init__ seeds on first import: only import after DB isolation.
            from core import pipeline
            from corpus.seed import ensure_seeded

            ensure_seeded(database_path=database)
            docs = db.fetch_one("SELECT COUNT(*) AS n FROM sources", database_path=database)
            chunks = db.fetch_one("SELECT COUNT(*) AS n FROM chunks", database_path=database)
            if docs["n"] != 6 or chunks["n"] != 72:
                raise ValueError("LIVE_CORPUS_NOT_FRESH")
            llm.LOGGER.addHandler(observer)
            try:
                result = pipeline.process_case(payload, actor="SYSTEM", case_id=case_id)
            finally:
                llm.LOGGER.removeHandler(observer)
        # Existing production telemetry không expose billed USD: UNAVAILABLE, không zero.
        return execution.AdapterOutput(result, dict(LIVE_CONFIG), self.diagnostics)


def _authorize(
    enabled: bool,
    authorization: LiveRunAuthorization | None,
    case_ids: tuple[str, ...] | None,
) -> LiveRunAuthorization:
    if enabled is not True or authorization is None:
        raise ValueError("LIVE_AUTHORIZATION_REQUIRED")
    a = authorization
    execution._validate_safe_id(a.run_id, "run_id")
    if (
        not case_ids
        or case_ids != a.approved_case_ids
        or len(set(case_ids)) != len(case_ids)
        or type(a.max_cases) is not int
        or not 1 <= len(case_ids) <= a.max_cases <= 12
    ):
        raise ValueError("LIVE_CASE_AUTHORIZATION_MISMATCH")
    if (
        type(a.max_cost_usd) not in (int, float)
        or not math.isfinite(a.max_cost_usd)
        or a.max_cost_usd <= 0
        or not isinstance(a.approval_reference, str)
        or not a.approval_reference.strip()
        or dev._safe(a.approval_reference) != a.approval_reference
    ):
        raise ValueError("LIVE_COST_OR_APPROVAL_INVALID")
    return a


def _payload(spec: dict[str, object]) -> CaseInput:
    raw = spec["input"]
    return CaseInput(**{**raw, "received_at": datetime.fromisoformat(raw["received_at"])})


def _retries(diagnostics: dev.CaptureDiagnostics | None) -> int:
    return (
        sum(
            e.get("event") == "llm_provider_attempt" and e.get("attempt_index", 1) > 1
            for e in (diagnostics.provider_attempts or [])
        )
        if diagnostics
        else 0
    )


def _capture_observation(
    snapshot: CaseInput,
    output: execution.AdapterOutput,
    cid: str,
    obs_id: str,
    directory: Path,
    fixture_path: Path,
) -> dev.Assessment:
    context = dev.execution_context(
        snapshot, output.result, case_id=cid, observation_id=obs_id, fixture=fixture_path
    )
    capture = dev.capture_result(
        output.result,
        case_id=cid,
        observation_id=obs_id,
        execution=context,
        config=output.config,
        diagnostics=output.diagnostics,
        fixture=fixture_path,
    )
    return dev.write_artifacts(directory / "cases" / cid, capture, fixture=fixture_path)


def _write_failure(directory: Path, cid: str, obs_id: str, error: Exception) -> dict[str, object]:
    target = directory / "cases" / cid
    target.mkdir(parents=True, exist_ok=True)
    failure = {
        "case_id": cid,
        "observation_id": obs_id,
        "technical_status": "ADAPTER_EXCEPTION",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **execution._adapter_failure(error),
    }
    execution._safe_write_json(target / "execution_failure.json", failure)
    return {
        "case_id": cid,
        "observation_id": obs_id,
        "technical_status": "TECHNICAL_FAILURE",
        "verdict": "TECHNICAL_ERROR",
    }


def _invoke_observation(
    spec: dict[str, object],
    authorization: LiveRunAuthorization,
    directory: Path,
    ledger_path: Path,
    fixture_path: Path,
) -> tuple[dict[str, object], float | None]:
    cid = spec["id"]
    obs_id = f"live_{authorization.run_id}_{cid}"
    payload = _payload(spec)
    snapshot = deepcopy(payload)
    if dev.input_hash(snapshot) != dev.input_hash(spec["input"]):
        raise ValueError("INPUT_IDENTITY_MISMATCH")
    record_live_observation(ledger_path, observation_id=obs_id, case_id=cid)
    output = None
    adapter = LivePipelineAdapter()
    try:
        output = adapter.invoke(
            payload, case_id=obs_id, database=directory / "databases" / f"{cid}.db"
        )
        if dev.input_hash(payload) != dev.input_hash(snapshot) or output.result.case_id != obs_id:
            raise ValueError("LIVE_RESULT_IDENTITY_MISMATCH")
        assessment = _capture_observation(snapshot, output, cid, obs_id, directory, fixture_path)
    except Exception as error:
        record_live_observation(
            ledger_path,
            observation_id=obs_id,
            case_id=cid,
            status="TECHNICAL_FAILURE",
            internal_retries=_retries(
                output.diagnostics if output else getattr(adapter, "diagnostics", None)
            ),
        )
        return _write_failure(directory, cid, obs_id, error), None
    technical = (
        output.result.decision.decision is Decision.ERROR or assessment.verdict == "TECHNICAL_ERROR"
    )
    record_live_observation(
        ledger_path,
        observation_id=obs_id,
        case_id=cid,
        status="TECHNICAL_FAILURE" if technical else "SEMANTIC_RESULT",
        internal_retries=_retries(output.diagnostics),
    )
    cost = output.diagnostics.cost if output.diagnostics else None
    return {
        "case_id": cid,
        "observation_id": obs_id,
        "result_case_id": output.result.case_id,
        "result_trace_id": output.result.trace_id,
        "technical_status": "TECHNICAL_FAILURE" if technical else "OK",
        "verdict": assessment.verdict,
        "artifact_directory": str(directory / "cases" / cid),
    }, cost


def run_live_cases(
    *,
    output_dir: Path,
    enabled: bool = False,
    authorization: LiveRunAuthorization | None = None,
    case_ids: tuple[str, ...] | None = None,
    ledger_path: Path = DEFAULT_LEDGER_PATH,
    fixture_path: Path = execution.FIXTURE,
) -> LiveRunResult:
    """Không default 12 cases; thiếu explicit approval/ledger/quota thì không invocation."""
    a = _authorize(enabled, authorization, case_ids)
    all_cases = {c["id"]: c for c in execution.load_frozen_cases(fixture_path)}
    if not set(case_ids) <= all_cases.keys():
        raise ValueError("LIVE_UNKNOWN_CASE")
    check_budget_authorization(len(case_ids), is_live=True, ledger_path=ledger_path)
    directory = output_dir.resolve()
    directory.mkdir(parents=True, exist_ok=False)
    execution._safe_write_json(
        directory / "live_manifest.json",
        {
            "run_mode": "LIVE",
            "is_synthetic_execution": False,
            "authorization": asdict(a),
            "fixture_sha256": execution.FIXTURE_SHA256,
            "config": LIVE_CONFIG,
        },
    )
    cases = []
    total_cost: float | None = 0.0  # trước attempt đầu tiên, không có chi phí run
    stop = "COMPLETED"
    for cid in case_ids:
        row, cost = _invoke_observation(all_cases[cid], a, directory, ledger_path, fixture_path)
        cases.append(row)
        if cost is None or type(cost) not in (int, float) or not math.isfinite(cost) or cost < 0:
            total_cost, stop = None, "COST_TELEMETRY_UNAVAILABLE"
        else:
            total_cost += cost
            if total_cost >= a.max_cost_usd:
                stop = "APPROVED_COST_LIMIT_REACHED"
        if row["technical_status"] != "OK":
            stop = "TECHNICAL_FAILURE"
        result = LiveRunResult(a.run_id, "LIVE", len(cases), stop, total_cost, cases)
        execution._safe_write_json(directory / f"progress_{len(cases)}.json", asdict(result))
        if stop != "COMPLETED":
            break
    execution._safe_write_json(directory / "run_summary.json", asdict(result))
    return result


def main(argv: list[str] | None = None) -> int:
    """CLI mới mặc định offline; LIVE chỉ khi run approval được truyền tường minh."""
    parser = argparse.ArgumentParser(description="Controlled M2 DEV runner; mặc định offline.")
    parser.add_argument("--execute-live", action="store_true")
    parser.add_argument("--case", action="append")
    parser.add_argument("--run-id")
    parser.add_argument("--authorize-run")
    parser.add_argument("--approval-reference")
    parser.add_argument("--max-cases", type=int)
    parser.add_argument("--max-cost-usd", type=float)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    if not args.execute_live:
        execution.orchestrate_m2_dev_run(
            output_dir=args.output_dir, case_ids=args.case or ["M2DEV-A1"]
        )
        return 0
    if (
        not args.case
        or not args.run_id
        or args.authorize_run != args.run_id
        or not args.approval_reference
        or args.max_cases is None
        or args.max_cost_usd is None
    ):
        parser.error("LIVE_AUTHORIZATION_REQUIRED")
    authorization = LiveRunAuthorization(
        args.run_id, tuple(args.case), args.max_cases, args.max_cost_usd, args.approval_reference
    )
    result = run_live_cases(
        output_dir=args.output_dir,
        enabled=True,
        authorization=authorization,
        case_ids=tuple(args.case),
    )
    sys.stdout.write(f"M2 DEV {result.stop_reason}; observations={result.attempted_observations}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
