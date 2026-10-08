from __future__ import annotations

import inspect
import json
import os
import socket
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import pytest

from core import pipeline
from core.ground_guard import GroundednessResult
from core.types import (
    CaseInput,
    CaseStatus,
    ChunkLabel,
    Decision,
    Domain,
    DraftReply,
    EvidenceChunk,
    EvidenceResult,
    EvidenceStatus,
    EscalationType,
    Extraction,
    PolicyDecision,
    RequestItem,
)
from infra import db
from infra.settings import load_local_env


def test_m2_combined_dev_registration_and_frozen_manifest(monkeypatch) -> None:
    from verify import harness

    def forbidden(*args, **kwargs):
        pytest.fail("Network/provider/pipeline execution forbidden in fixture loading test")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(harness, "process_case", forbidden)
    monkeypatch.setattr(harness, "run_cases", forbidden)
    path = harness.CASE_SETS["m2_combined_dev"]
    assert path == Path("verify/cases_m2_combined_dev.json")
    assert {"verify4", "escalation5", "full15", "fresh5"} <= harness.CASE_SETS.keys()
    cases = harness.load_cases(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert len(cases) == 12
    assert {case.case_id for case in cases} == {
        f"M2DEV-{group}{index}" for group in "ABC" for index in range(1, 5)
    }
    assert Counter(case.expected_rule_id for case in cases) == {
        "P01": 3,
        "P02": 3,
        "P03": 2,
        "P05": 4,
    }
    assert Counter(case.expected_decision for case in cases) == {"AUTO_REPLY": 4, "ESCALATE": 8}
    types = {
        "P01": "AUTHORITY_REQUIRED",
        "P02": "OUT_OF_POLICY",
        "P03": "FACT_UNRESOLVED",
        "P05": None,
    }
    for case, item in zip(cases, payload, strict=True):
        assert case.expected_type == types[case.expected_rule_id]
        assert case.input.received_at.utcoffset() is not None
        assert case.input.body == item["input"]["body"]
        assert item["meta"]["status"] == "GOLD_VERIFIED_READY_FOR_FREEZE"


def _input(channel: str) -> CaseInput:
    return CaseInput(
        sender="student@example.edu",
        subject="Hỏi hạn rút học phần",
        body="Em cần biết hạn rút học phần trong học kỳ này là khi nào?",
        received_at=datetime(2026, 9, 22, tzinfo=timezone.utc),
        channel=channel,  # type: ignore[arg-type]
    )


def _extraction() -> Extraction:
    return Extraction(
        "vi",
        [
            RequestItem(
                Domain.COURSE_WITHDRAWAL, "hạn rút học phần", True, False, False, False, False
            )
        ],
        {"semester": "2026-1"},
        [],
        False,
        "{}",
    )


def _evidence() -> EvidenceResult:
    return EvidenceResult(
        EvidenceStatus.OK,
        [
            EvidenceChunk(
                "chunk-1",
                "doc-1",
                "Điều 1",
                "Hạn rút học phần là ngày 30/09/2026.",
                Domain.COURSE_WITHDRAWAL,
                ChunkLabel.AUTO_ANSWERABLE,
                0.9,
                datetime(2026, 1, 1, tzinfo=timezone.utc).date(),
                None,
                [],
                [],
                False,
                False,
            )
        ],
        [],
    )


def _install_success_path(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    evidence = _evidence()
    decision = PolicyDecision(Decision.AUTO_REPLY, None, "P05", "Đủ căn cứ.", ["chunk-1"], "cv")
    draft = DraftReply("Hạn rút học phần", "Hạn là 30/09/2026. [chunk-1]", ["chunk-1"], True, [])
    monkeypatch.setattr(pipeline, "get_corpus_version", lambda: "cv")
    monkeypatch.setattr(pipeline, "extract_facts", lambda body, case_id: _extraction())
    monkeypatch.setattr(pipeline, "retrieve_evidence", lambda **kwargs: evidence)
    monkeypatch.setattr(pipeline, "validate_evidence", lambda **kwargs: evidence)
    monkeypatch.setattr(pipeline, "decide_policy", lambda policy_input: decision)
    monkeypatch.setattr(pipeline, "generate_reply", lambda **kwargs: draft)
    monkeypatch.setattr(
        pipeline,
        "guard_groundedness",
        lambda **kwargs: GroundednessResult(draft, None, []),
    )


def test_paste_inbox_and_verify_share_the_same_pipeline(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", tmp_path / "app.db")
    _install_success_path(monkeypatch)

    results = [pipeline.process_case(_input(channel)) for channel in ("paste", "inbox", "verify")]

    assert {result.status for result in results} == {CaseStatus.PENDING_SEND}
    assert {result.decision.rule_id for result in results} == {"P05"}
    assert {tuple(result.draft.citations) for result in results if result.draft} == {("chunk-1",)}
    assert all(
        set(result.step_latencies_ms) == {f"R{step}" for step in range(15)} for result in results
    )
    assert "if inp.channel" not in inspect.getsource(pipeline.process_case)


def test_pipeline_step_failure_returns_error_without_business_escalation(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setattr(db, "DEFAULT_DATABASE_PATH", tmp_path / "app.db")
    monkeypatch.setattr(pipeline, "get_corpus_version", lambda: "cv")
    monkeypatch.setattr(
        pipeline,
        "extract_facts",
        lambda body, case_id: (_ for _ in ()).throw(RuntimeError("extract failed")),
    )

    result = pipeline.process_case(_input("verify"))

    assert result.decision.decision is Decision.ERROR
    assert result.decision.rule_id == "TECHNICAL_ERROR"
    assert result.status is CaseStatus.ERROR
    assert result.card is None
    assert not db.fetch_one("SELECT case_id FROM escalations WHERE case_id = ?", (result.case_id,))


def test_local_env_does_not_override_existing_environment(monkeypatch, tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("GOOGLE_API_KEY=from-file\nLLM_MODE=replay\n", encoding="utf-8")
    monkeypatch.setenv("GOOGLE_API_KEY", "from-shell")
    monkeypatch.delenv("LLM_MODE", raising=False)

    load_local_env(Path(env_file))

    assert os.environ["GOOGLE_API_KEY"] == "from-shell"
    assert os.environ["LLM_MODE"] == "replay"


@pytest.mark.parametrize(
    "provider,configured_model,expected_provider,expected_model",
    [
        ("openai", "gpt-6-luna", "openai", "gpt-6-luna"),
        (" OPENAI ", " gpt-6-luna ", "openai", "gpt-6-luna"),
        ("gemini", "gemini-configured", "gemini", "gemini-configured"),
        (None, None, "gemini", "gemini-3.6-flash"),
    ],
)
def test_verify_metadata_uses_production_provider_config(
    monkeypatch, tmp_path, provider, configured_model, expected_provider, expected_model
) -> None:
    from verify import harness

    def forbidden(*args, **kwargs):
        pytest.fail("Network/provider/pipeline calls forbidden in metadata test")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(harness, "process_case", forbidden)
    for name in ("LLM_PROVIDER", "OPENAI_MODEL", "GEMINI_MODEL"):
        monkeypatch.delenv(name, raising=False)
    if provider is not None:
        monkeypatch.setenv("LLM_PROVIDER", provider)
        model_var = "OPENAI_MODEL" if provider.strip().lower() == "openai" else "GEMINI_MODEL"
        monkeypatch.setenv(model_var, configured_model)
    monkeypatch.setenv("LLM_MODE", "live")
    monkeypatch.setenv("LLM_CACHE", "0")
    result = harness.VerifyResult(
        case_id="V03",
        subject="Synthetic subject",
        question="Synthetic question?",
        expected_decision=Decision.ESCALATE,
        expected_type=EscalationType.AUTHORITY_REQUIRED,
        actual_decision=Decision.ESCALATE,
        actual_type=EscalationType.AUTHORITY_REQUIRED,
        rule_id="P01",
        passed=True,
        elapsed_ms=1000,
        timestamp="2026-10-05T09:00:00+07:00",
        corpus_version="synthetic-corpus",
        case_ref="synthetic-case",
        expected_rule_id="P01",
    )
    calls = []

    def offline_results(path, **kwargs):
        calls.append((path, kwargs))
        return (result,)

    monkeypatch.setattr(harness, "run_cases", offline_results)
    clock = iter((10.0, 11.0))
    monkeypatch.setattr(harness, "perf_counter", lambda: next(clock))
    output = tmp_path / "verify4.json"
    assert harness.main(["--set", "verify4", "--output", str(output)]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload == {
        "case_set": "verify4",
        "llm_mode": "live",
        "provider": expected_provider,
        "model": expected_model,
        "cache_enabled": False,
        "elapsed_seconds": 1.0,
        "within_time_limit": True,
        "results": [asdict(result)],
    }
    assert calls == [(harness.CASE_SETS["verify4"], {"run_name": "verify4", "case_id": None})]
