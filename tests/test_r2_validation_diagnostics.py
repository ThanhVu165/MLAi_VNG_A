"""Offline R2 diagnostics: synthetic values, no provider or default database writes."""

import json
from dataclasses import asdict, replace
from datetime import date
from pathlib import Path
from unittest.mock import Mock

import pytest

from core import extract
from infra import llm
from infra.provider_observability import current_correlation, provider_correlation
from verify import m2_dev_assessment as dev
from verify import m2_dev_execution as execution
from verify import m2_dev_live as live


def payload(facts):
    return {
        "language": "vi",
        "requests": [],
        "critical_facts": facts,
        "missing_critical_facts": [],
        "injection_suspected": False,
    }


def result(data):
    return llm.LLMResult(True, data, None, 0, "synthetic", "mock")


def events(caplog):
    return [r.r2_validation for r in caplog.records if hasattr(r, "r2_validation")]


@pytest.fixture(autouse=True)
def offline_audit(monkeypatch):
    # Audit semantics are covered elsewhere; these tests must never write a database.
    monkeypatch.setattr(extract, "log_event", Mock())


@pytest.mark.parametrize(
    "facts,code",
    [
        ([{"name": "  ", "value": "private-value"}], "FACT_NAME_EMPTY"),
        ([{"name": "private-name", "value": "  "}], "FACT_VALUE_EMPTY"),
        (
            [
                {"name": "private-name", "value": "private-value"},
                {"name": "private-name", "value": "different-private-value"},
            ],
            "FACT_DUPLICATE_CONFLICT",
        ),
    ],
)
def test_invalid_twice_keeps_both_diagnostics_and_fallback(monkeypatch, caplog, facts, code):
    call = Mock(side_effect=[result(payload(facts)), result(payload(facts))])
    monkeypatch.setattr(extract, "call_json", call)
    with provider_correlation("private-identity") as correlation:
        output = extract.extract_facts("private-email-body", "private-identity")
    observed = events(caplog)
    assert [e["logical_call_index"] for e in observed] == [1, 2]
    assert all(e["reason_code"] == code for e in observed)
    assert all(e["validation_stage"] == "critical_facts" for e in observed)
    assert all(e["provider_result"] == "SUCCESS" for e in observed)
    assert all(e["domain_validation"] == "FAIL" for e in observed)
    assert all(e["correlation_id"] == correlation for e in observed)
    assert "private-" not in json.dumps(observed) + caplog.text
    assert [e["retry_reason"] for e in observed] == [
        "INTERNAL_VALIDATION_RETRY",
        "VALIDATION_RETRY_EXHAUSTED",
    ]
    assert call.call_count == 2
    assert call.call_args_list[0] == call.call_args_list[1]
    assert output.requests == [] and output.critical_facts == {} and output.raw_json == "{}"
    assert output.llm_error == (
        "Phản hồi LLM không hợp lệ: Dữ kiện cần tên, nội dung rõ ràng và không tự mâu thuẫn."
    )
    extract.log_event.assert_called_once()
    assert extract.log_event.call_args.kwargs["action"] == "CASE_ERROR"
    assert current_correlation("private-identity") is None


def test_invalid_then_valid_and_identical_duplicate(monkeypatch, caplog):
    invalid = payload([{"name": "private-name", "value": " "}])
    valid = payload(
        [
            {"name": "private-name", "value": "same-value"},
            {"name": "private-name", "value": " same-value "},
        ]
    )
    call = Mock(side_effect=[result(invalid), result(valid)])
    monkeypatch.setattr(extract, "call_json", call)
    output = extract.extract_facts("synthetic-body", "synthetic-case")
    observed = events(caplog)
    assert [e["domain_validation"] for e in observed] == ["FAIL", "PASS"]
    assert observed[0]["reason_code"] == "FACT_VALUE_EMPTY"
    assert observed[1]["reason_code"] is None
    assert observed[1]["validation_stage"] == "complete"
    assert observed[1]["retry_reason"] == "NONE"
    assert output.llm_error is None
    assert output.critical_facts == {"private-name": "same-value"}
    assert call.call_count == 2
    extract.log_event.assert_called_once()
    assert extract.log_event.call_args.kwargs["action"] == "FACTS_EXTRACTED"


@pytest.mark.parametrize("stage", ["response", "requests", "language", "critical_facts"])
def test_other_validation_errors_have_safe_stage(monkeypatch, caplog, stage):
    data = payload([])
    if stage == "response":
        data = []
    else:
        data[stage] = None
    monkeypatch.setattr(extract, "call_json", Mock(return_value=result(data)))
    output = extract.extract_facts("synthetic", "synthetic")
    assert output.llm_error
    assert len(events(caplog)) == 2
    assert all(e["validation_stage"] == stage for e in events(caplog))
    assert all(e["reason_code"] == "R2_PAYLOAD_INVALID" for e in events(caplog))


@pytest.mark.parametrize("recover", [False, True])
def test_transport_retry_is_not_domain_validation_retry(monkeypatch, caplog, recover):
    monkeypatch.setenv("OPENAI_API_KEY", "private-credential")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-6-luna")
    monkeypatch.setattr(llm, "sleep", lambda _: None)
    request = Mock(
        side_effect=(
            [ConnectionError("private-transport-detail"), result(payload([]))]
            if recover
            else ConnectionError("private-transport-detail")
        )
    )
    monkeypatch.setattr(llm, "_request_openai", request)
    monkeypatch.setattr(
        extract,
        "call_json",
        lambda prompt, **kwargs: llm._call_live(
            prompt,
            kwargs["schema"],
            "synthetic-hash",
            "gpt-6-luna",
            30,
            1,
            case_id=kwargs["case_id"],
            step=kwargs["step"],
        ),
    )
    with provider_correlation("private-identity") as correlation, llm.case_call_budget():
        observer = live._AttemptObserver("private-identity", correlation)
        llm.LOGGER.addHandler(observer)
        try:
            output = extract.extract_facts("private-prompt", "private-identity")
        finally:
            llm.LOGGER.removeHandler(observer)
    observed = events(caplog)
    assert len(observed) == 1 and observed[0]["logical_call_index"] == 1
    assert observed[0]["correlation_id"] == correlation
    assert observed[0]["provider_result"] == ("SUCCESS" if recover else "FAILURE")
    assert observed[0]["domain_validation"] == ("PASS" if recover else "NOT_RUN")
    assert observed[0]["reason_code"] is None
    assert observed[0]["retry_reason"] == ("NONE" if recover else "PROVIDER_FAILURE")
    assert bool(output.llm_error) is not recover
    attempts = [r.provider_attempt for r in caplog.records if hasattr(r, "provider_attempt")]
    assert [a["attempt_index"] for a in attempts] == [1, 2]
    assert all(a["call_id"] == attempts[0]["call_id"] for a in attempts)
    assert observer.diagnostics().provider_attempts == [
        {k: v for k, v in event.items() if k in live.ATTEMPT_FIELDS} for event in attempts
    ]
    assert observer.diagnostics().r2_validation == observed
    assert live._retries(observer.diagnostics()) == 1


def test_event_excludes_all_raw_values_and_preserves_uuid(monkeypatch, caplog):
    monkeypatch.setenv("OPENAI_API_KEY", "private-credential")
    monkeypatch.setattr(
        extract,
        "call_json",
        Mock(
            return_value=result(
                payload(
                    [
                        {"name": "private-name", "value": "private-value"},
                    ]
                )
            )
        ),
    )
    with provider_correlation("private-identity") as correlation:
        extract.extract_facts("private-email private-prompt private-credential", "private-identity")
    event = events(caplog)[0]
    assert set(event) == {
        "event",
        "correlation_id",
        "phase",
        "logical_call_index",
        "provider_result",
        "domain_validation",
        "validation_stage",
        "reason_code",
        "retry_reason",
    }
    assert event["phase"] == "R2_extract" and event["correlation_id"] == correlation
    serialized = json.dumps(event) + caplog.text
    assert "private-" not in serialized


def test_logging_failure_cannot_change_extraction(monkeypatch):
    monkeypatch.setattr(extract, "call_json", Mock(return_value=result(payload([]))))
    monkeypatch.setattr(extract.LLM_LOGGER, "warning", Mock(side_effect=RuntimeError("logger")))
    assert extract.extract_facts("synthetic", "synthetic").llm_error is None


@pytest.mark.parametrize("outcome", ["invalid_invalid", "invalid_valid", "provider_failure"])
def test_r2_logger_to_live_capture_and_summary(monkeypatch, tmp_path, outcome):
    """Run only the artifact boundary with synthetic extraction and provider mocks."""
    invalid = result(payload([{"name": "private-name", "value": " "}]))
    valid = result(payload([]))
    responses = (
        [llm.LLMResult(False, None, "private-error", 0, "mock", "mock")]
        if outcome == "provider_failure"
        else [invalid, invalid if outcome == "invalid_invalid" else valid]
    )
    monkeypatch.setenv("OPENAI_API_KEY", "private-credential")
    monkeypatch.setattr(live, "PRICING_VERIFIED_ON", date.today())
    monkeypatch.setattr(live, "PRICING_VALID_THROUGH", date.today())
    emitted = []

    def invoke(self, submitted, *, case_id, database):
        with provider_correlation(case_id) as correlation:
            observer = live._AttemptObserver(case_id, correlation)
            llm.LOGGER.addHandler(observer)

            def provider(*args, **kwargs):
                response = responses[len(emitted)]
                event = {
                    "event": "llm_provider_attempt",
                    "correlation_id": correlation,
                    "call_id": f"mock-call-{len(emitted) + 1}",
                    "step": "R2_extract",
                    "attempt_index": 1,
                    "provider": "openai",
                    "model": "gpt-6-luna",
                    "success": response.ok,
                    "elapsed_ms": 1,
                    "usage": {
                        "input_tokens": 10,
                        "output_tokens": 5,
                        "cached_input_tokens": 0,
                        "cache_write_tokens": 0,
                        "response_model": "gpt-6-luna",
                        "service_tier": "default",
                    },
                }
                emitted.append(event)
                llm.LOGGER.warning(
                    "private-prompt private-response", extra={"provider_attempt": event}
                )
                return response

            monkeypatch.setattr(extract, "call_json", provider)
            try:
                extracted = extract.extract_facts("private-email-body", case_id)
            finally:
                llm.LOGGER.removeHandler(observer)
            diagnostics = observer.diagnostics()
        spec = dev.load_prereg("M2DEV-A4")
        fake = execution.DeterministicMockAdapter(force_error=bool(extracted.llm_error))(
            spec, submitted, case_id, "OFFLINE"
        )
        return execution.AdapterOutput(
            replace(fake.result, case_id=case_id, extraction=extracted),
            dict(live.LIVE_CONFIG),
            diagnostics,
        )

    monkeypatch.setattr(live.LivePipelineAdapter, "invoke", invoke)
    ledger = tmp_path / "ledger.json"
    ledger.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "baseline": {
                    "total": 45,
                    "consumed": 6,
                    "confirmed_by": "synthetic",
                    "confirmed_at": "2026-10-09T00:00:00+00:00",
                    "reconciliation_reference": "synthetic",
                },
                "attempts": [],
                "current": {"total": 45, "consumed": 6, "remaining": 39},
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "artifacts"
    run = live.run_live_cases(
        output_dir=output,
        enabled=True,
        authorization=live.LiveRunAuthorization("mock_retention", ("M2DEV-A4",), 1, 0.5, "mock"),
        case_ids=("M2DEV-A4",),
        ledger_path=ledger,
    )
    captured = json.loads((output / "cases/M2DEV-A4/capture.json").read_text(encoding="utf-8"))
    events = captured["diagnostics"]["r2_validation"]
    expected = {
        "invalid_invalid": ["FAIL", "FAIL"],
        "invalid_valid": ["FAIL", "PASS"],
        "provider_failure": ["NOT_RUN"],
    }[outcome]
    assert [e["domain_validation"] for e in events] == expected
    assert [e["logical_call_index"] for e in events] == list(range(1, len(expected) + 1))
    assert len({e["correlation_id"] for e in events}) == 1
    assert captured["diagnostics"]["provider_attempts"] == emitted
    assert len(captured["diagnostics"]["logical_calls"]) == len(emitted)
    assert run.cases[0]["r2_validation"] == events
    for name in ("run_summary.json", "progress_1.json"):
        assert json.loads((output / name).read_text())["cases"][0]["r2_validation"] == events
    assert json.loads(ledger.read_text())["attempts"][0]["internal_retries"] == 0
    if outcome == "provider_failure":
        assert events[0]["provider_result"] == "FAILURE"
        assert events[0]["reason_code"] is None
        assert events[0]["retry_reason"] == "PROVIDER_FAILURE"
    else:
        assert events[0]["reason_code"] == "FACT_VALUE_EMPTY"
        assert events[0]["validation_stage"] == "critical_facts"
        assert events[0]["retry_reason"] == "INTERNAL_VALIDATION_RETRY"
        assert events[1]["retry_reason"] == (
            "VALIDATION_RETRY_EXHAUSTED" if outcome == "invalid_invalid" else "NONE"
        )
    # Production failure messages remain outside this metadata-only retention assertion.
    serialized = json.dumps(captured["diagnostics"]) + json.dumps(run.cases)
    assert "private-" not in serialized
    capture = dev.Capture(**captured)
    old = replace(
        capture,
        diagnostics={k: v for k, v in capture.diagnostics.items() if k != "r2_validation"},
    )
    before, after = dev.assess_capture(old), dev.assess_capture(capture)
    assert before.verdict == after.verdict
    assert {k: d.status for k, d in before.dimensions.items()} == {
        k: d.status for k, d in after.dimensions.items()
    }
    assert before.criteria == after.criteria


@pytest.mark.parametrize("probe,case", [("01", "A1"), ("02", "A4"), ("03", "A4")])
def test_historical_capture_without_r2_field_still_reads(probe, case):
    path = Path(__file__).resolve().parents[1] / (
        f"data/validation/m2_dev_live_probe_{probe}/cases/M2DEV-{case}"
    )
    if not path.exists():
        pytest.skip("Historical LIVE artifacts are local evidence, not required CI fixtures")
    captured = json.loads((path / "capture.json").read_text(encoding="utf-8"))
    expected = json.loads((path / "assessment.json").read_text(encoding="utf-8"))
    assert "r2_validation" not in captured["diagnostics"]
    assessment = dev.assess_capture(dev.Capture(**captured))
    assert assessment.capture_sha256 == expected["capture_sha256"]
    assert assessment.verdict == expected["verdict"]


def test_validation_metadata_filters_content_and_foreign_correlation():
    import logging

    with provider_correlation("synthetic") as correlation:
        observer = live._AttemptObserver("synthetic", correlation)
        event = {
            "event": "r2_validation",
            "correlation_id": correlation,
            "phase": "R2_extract",
            "logical_call_index": 1,
            "provider_result": "SUCCESS",
            "domain_validation": "PASS",
            "validation_stage": "complete",
            "reason_code": None,
            "retry_reason": "NONE",
        }

        def send(value):
            record = logging.LogRecord(
                "infra.llm", logging.WARNING, "", 0, "private-prompt", (), None
            )
            record.r2_validation = value
            observer.emit(record)

        send({**event, "raw_response": "private-response", "fact_name": "private-name"})
        assert observer.r2_validation == [event]
        for field, value in [
            ("correlation_id", "foreign"),
            ("reason_code", "private-value"),
            ("validation_stage", "private-email"),
            ("retry_reason", "private-credential"),
            ("logical_call_index", True),
            ("domain_validation", ["private"]),
        ]:
            send({**event, field: value})
        assert observer.r2_validation == [event]
        assert "private-" not in json.dumps(asdict(observer.diagnostics()))
        invalid = asdict(observer.diagnostics())
        invalid["r2_validation"] = [{**event, "raw_response": "private"}]
        with pytest.raises(ValueError, match="R2 validation"):
            dev._validate_diagnostics(invalid)
