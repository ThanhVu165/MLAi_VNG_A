"""Offline R2 diagnostics: synthetic values, no provider or default database writes."""

import json
from unittest.mock import Mock

import pytest

from core import extract
from infra import llm
from infra.provider_observability import current_correlation, provider_correlation


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
        output = extract.extract_facts("private-prompt", "private-identity")
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
