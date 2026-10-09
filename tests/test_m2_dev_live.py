"""Controlled LIVE boundary tested entirely offline; real provider/pipeline forbidden."""

from dataclasses import replace
import json
import os
import socket

import pytest

from verify import m2_dev_assessment as dev
from verify import m2_dev_execution as execution
from verify import m2_dev_live as live
from verify import m2_live_budget as budget


@pytest.fixture(autouse=True)
def offline_guard(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Real network/provider/pipeline forbidden")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    from infra import llm
    from core import pipeline

    monkeypatch.setattr(llm, "call_json", forbidden)
    monkeypatch.setattr(llm, "_request_openai", forbidden)
    monkeypatch.setattr(pipeline, "process_case", forbidden)


@pytest.fixture
def ledger(tmp_path):
    path = tmp_path / "test-ledger.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "baseline": {
                    "total": 45,
                    "consumed": 3,
                    "confirmed_by": "test-only",
                    "confirmed_at": "2026-10-09T00:00:00+00:00",
                    "reconciliation_reference": "synthetic-test",
                },
                "attempts": [],
                "current": {"total": 45, "consumed": 3, "remaining": 42},
            }
        ),
        encoding="utf-8",
    )
    return path


def auth(cases=("M2DEV-A1",), cap=1.0):
    return live.LiveRunAuthorization("test_run", cases, len(cases), cap, "test-only approval")


def run(tmp_path, ledger, authorization=None, **kwargs):
    authorization = authorization or auth()
    return live.run_live_cases(
        output_dir=tmp_path / "output",
        ledger_path=ledger,
        enabled=True,
        authorization=authorization,
        case_ids=authorization.approved_case_ids,
        **kwargs
    )


def fake_output(payload, case_id, *, error=False, cost=None, retries=0):
    # Test-only fake; production entrypoint has no adapter injection argument.
    spec = execution.load_frozen_cases()[0]
    output = execution.DeterministicMockAdapter(force_error=error)(
        spec, payload, case_id, "OFFLINE"
    )
    events = [
        {
            "event": "llm_provider_attempt",
            "case_id": case_id,
            "attempt_index": i + 1,
            "success": i == retries,
        }
        for i in range(retries + 1)
    ]
    return execution.AdapterOutput(
        replace(output.result, case_id=case_id),
        dict(live.LIVE_CONFIG),
        dev.CaptureDiagnostics(provider_attempts=events, cost=cost),
    )


def patch_adapter(monkeypatch, **kwargs):
    def invoke(self, payload, *, case_id, database):
        return fake_output(payload, case_id, **kwargs)

    monkeypatch.setattr(live.LivePipelineAdapter, "invoke", invoke)


@pytest.mark.parametrize("enabled,authorization", [(False, None), (True, None), (False, auth())])
def test_no_authorization_denies_even_with_live_environment(
    tmp_path, ledger, monkeypatch, enabled, authorization
):
    monkeypatch.setenv("LLM_MODE", "live")
    with pytest.raises(ValueError, match="LIVE_AUTHORIZATION_REQUIRED"):
        live.run_live_cases(
            output_dir=tmp_path / "output",
            ledger_path=ledger,
            enabled=enabled,
            authorization=authorization,
        )
    assert budget.verify_live_budget(ledger).used_observations == 3
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize("change", ["missing", "corrupt", "quota"])
def test_invalid_budget_never_invokes(tmp_path, ledger, change):
    if change == "missing":
        ledger.unlink()
    elif change == "corrupt":
        ledger.write_text("{}", encoding="utf-8")
    else:
        data = json.loads(ledger.read_text())
        data["baseline"]["consumed"] = 45
        data["current"] = {"total": 45, "consumed": 45, "remaining": 0}
        ledger.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises((budget.BudgetVerificationError, budget.BudgetExceededError)):
        run(tmp_path, ledger)
    assert not (tmp_path / "output").exists()


def test_accounting_failure_prevents_adapter(tmp_path, ledger, monkeypatch):
    called = []
    monkeypatch.setattr(live.LivePipelineAdapter, "invoke", lambda *a, **k: called.append(True))

    def fail(*args, **kwargs):
        raise OSError("synthetic accounting failure")

    monkeypatch.setattr(live, "record_live_observation", fail)
    with pytest.raises(OSError):
        run(tmp_path, ledger)
    assert called == []
    assert budget.verify_live_budget(ledger).used_observations == 3


def test_durable_attempt_before_invocation_and_retry_count(tmp_path, ledger, monkeypatch):
    def invoke(self, payload, *, case_id, database):
        data = json.loads(ledger.read_text())
        assert data["current"]["consumed"] == 4
        assert data["attempts"][0]["status"] == "ATTEMPTED"
        assert data["attempts"][0]["observation_id"] == case_id
        return fake_output(payload, case_id, retries=1)

    monkeypatch.setattr(live.LivePipelineAdapter, "invoke", invoke)
    result = run(tmp_path, ledger)
    data = json.loads(ledger.read_text())
    assert result.attempted_observations == 1
    assert data["current"]["consumed"] == 4
    assert len(data["attempts"]) == 1
    assert data["attempts"][0]["internal_retries"] == 1
    assert data["attempts"][0]["status"] == "SEMANTIC_RESULT"
    assert result.cases[0]["verdict"] != "PASS"


def test_technical_failure_consumes_one_without_refund(tmp_path, ledger, monkeypatch):
    patch_adapter(monkeypatch, error=True)
    result = run(tmp_path, ledger)
    assert result.stop_reason == "TECHNICAL_FAILURE"
    assert result.cases[0]["verdict"] == "TECHNICAL_ERROR"
    data = json.loads(ledger.read_text())
    assert data["current"]["consumed"] == 4
    assert data["attempts"][0]["status"] == "TECHNICAL_FAILURE"


def test_exception_message_never_persisted(tmp_path, ledger, monkeypatch):
    class SensitiveError(Exception):
        def __str__(self):
            pytest.fail("Exception message must not be read")

        def __repr__(self):
            pytest.fail("Exception repr must not be read")

    def invoke(*args, **kwargs):
        raise SensitiveError("synthetic-private-body synthetic-test-token")

    monkeypatch.setattr(live.LivePipelineAdapter, "invoke", invoke)
    result = run(tmp_path, ledger)
    assert result.stop_reason == "TECHNICAL_FAILURE"
    for path in (tmp_path / "output").rglob("*.json"):
        text = path.read_text(encoding="utf-8")
        assert "synthetic-private-body" not in text
        assert "synthetic-test-token" not in text
        assert "SensitiveError" not in text
    assert budget.verify_live_budget(ledger).used_observations == 4


@pytest.mark.parametrize("mutation", ["payload", "result_id"])
def test_wrong_identity_cannot_capture_pass(tmp_path, ledger, monkeypatch, mutation):
    def invoke(self, payload, *, case_id, database):
        if mutation == "payload":
            payload.body = "altered test input"
        return fake_output(payload, "wrong-id" if mutation == "result_id" else case_id)

    monkeypatch.setattr(live.LivePipelineAdapter, "invoke", invoke)
    result = run(tmp_path, ledger)
    assert result.cases[0]["verdict"] == "TECHNICAL_ERROR"
    assert not list((tmp_path / "output").rglob("capture.json"))
    assert budget.verify_live_budget(ledger).used_observations == 4


@pytest.mark.parametrize(
    "cost,cap,expected_count,stop",
    [
        (None, 1.0, 1, "COST_TELEMETRY_UNAVAILABLE"),
        (0.6, 0.5, 1, "APPROVED_COST_LIMIT_REACHED"),
        (0.1, 1.0, 2, "COMPLETED"),
    ],
)
def test_stop_before_next_case_on_cost(
    tmp_path, ledger, monkeypatch, cost, cap, expected_count, stop
):
    patch_adapter(monkeypatch, cost=cost)
    result = run(tmp_path, ledger, auth(("M2DEV-A1", "M2DEV-A2"), cap))
    assert result.attempted_observations == expected_count
    assert result.stop_reason == stop
    assert budget.verify_live_budget(ledger).used_observations == 3 + expected_count
    assert result.observed_cost_usd == (None if cost is None else cost * expected_count)


@pytest.mark.parametrize(
    "authorization",
    [
        replace(auth(), max_cases=0),
        replace(auth(), max_cost_usd=float("nan")),
        replace(auth(), approved_case_ids=("M2DEV-A1", "M2DEV-A1"), max_cases=2),
        replace(auth(), approved_case_ids=("UNKNOWN",)),
    ],
)
def test_invalid_approval_fails_closed(tmp_path, ledger, authorization):
    with pytest.raises(ValueError):
        run(tmp_path, ledger, authorization)
    assert budget.verify_live_budget(ledger).used_observations == 3
    assert not (tmp_path / "output").exists()


def test_real_adapter_boundary_fresh_seed_payload_and_runtime_restore(tmp_path, monkeypatch):
    from core import pipeline
    from infra import db, llm

    spec = execution.load_frozen_cases()[0]
    payload = live._payload(spec)
    original_db = db.DEFAULT_DATABASE_PATH
    original_env = {k: os.environ.get(k) for k in live.LIVE_CONFIG}
    database = tmp_path / "fresh.db"

    def fake_process(inp, *, actor, case_id):
        from infra.provider_observability import current_correlation

        assert dev.input_hash(inp) == dev.input_hash(spec["input"])
        assert actor == "SYSTEM" and case_id == "live_test"
        assert db.DEFAULT_DATABASE_PATH == database
        assert all(os.environ[k] == v for k, v in live.LIVE_CONFIG.items())
        assert db.fetch_one("SELECT COUNT(*) AS n FROM chunks")["n"] == 72
        llm.LOGGER.warning(
            "ignored raw message",
            extra={
                "provider_attempt": {
                    "event": "llm_provider_attempt",
                    "case_id": case_id,
                    "correlation_id": current_correlation(case_id),
                    "attempt_index": 1,
                    "success": True,
                    "raw_json": "not retained",
                }
            },
        )
        return fake_output(inp, case_id).result

    monkeypatch.setattr(pipeline, "process_case", fake_process)
    output = live.LivePipelineAdapter().invoke(payload, case_id="live_test", database=database)
    assert output.result.case_id == "live_test"
    assert output.diagnostics.cost is None
    assert "raw_json" not in output.diagnostics.provider_attempts[0]
    assert db.DEFAULT_DATABASE_PATH == original_db
    assert {k: os.environ.get(k) for k in live.LIVE_CONFIG} == original_env
    with pytest.raises(ValueError, match="LIVE_DATABASE_NOT_FRESH"):
        live.LivePipelineAdapter().invoke(payload, case_id="live_test", database=database)


def test_default_cli_offline_and_no_ledger_consumption(tmp_path, ledger, monkeypatch):
    original = ledger.read_bytes()
    monkeypatch.setattr(
        execution,
        "check_budget_authorization",
        lambda requested_count, **kwargs: budget.check_budget_authorization(
            requested_count, is_live=False, ledger_path=ledger
        ),
    )
    monkeypatch.setenv("LLM_MODE", "live")
    assert live.main(["--output-dir", str(tmp_path / "offline")]) == 0
    assert ledger.read_bytes() == original
    summary = json.loads((tmp_path / "offline" / "run_summary.json").read_text())
    assert summary["run_mode"] == "OFFLINE_MOCK"


def test_cli_live_requires_explicit_matching_run_approval(tmp_path):
    with pytest.raises(SystemExit) as error:
        live.main(
            [
                "--execute-live",
                "--case",
                "M2DEV-A1",
                "--run-id",
                "test_run",
                "--output-dir",
                str(tmp_path / "output"),
            ]
        )
    assert error.value.code == 2
    assert not (tmp_path / "output").exists()


def test_finalize_failure_keeps_attempt_debited_and_stops(tmp_path, ledger, monkeypatch):
    patch_adapter(monkeypatch, cost=0.1)
    record = live.record_live_observation

    def fail_finalize(*args, **kwargs):
        if kwargs.get("status"):
            raise OSError("synthetic finalize failure")
        return record(*args, **kwargs)

    monkeypatch.setattr(live, "record_live_observation", fail_finalize)
    with pytest.raises(OSError):
        run(tmp_path, ledger, auth(("M2DEV-A1", "M2DEV-A2")))
    data = json.loads(ledger.read_text())
    assert len(data["attempts"]) == 1
    assert data["attempts"][0]["status"] == "ATTEMPTED"
    assert data["current"]["consumed"] == 4


def test_exception_after_provider_retries_retains_retry_metadata(tmp_path, ledger, monkeypatch):
    def invoke(self, payload, *, case_id, database):
        self.diagnostics = dev.CaptureDiagnostics(
            provider_attempts=[
                {"event": "llm_provider_attempt", "attempt_index": 1},
                {"event": "llm_provider_attempt", "attempt_index": 2},
            ]
        )
        raise RuntimeError("not persisted")

    monkeypatch.setattr(live.LivePipelineAdapter, "invoke", invoke)
    result = run(tmp_path, ledger)
    assert result.stop_reason == "TECHNICAL_FAILURE"
    data = json.loads(ledger.read_text())
    assert data["current"]["consumed"] == 4
    assert data["attempts"][0]["internal_retries"] == 1
