"""Tests for verify/m2_dev_execution.py.

Offline mock only; cấm network, provider và pipeline thật.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from datetime import datetime
import hashlib
import json
from pathlib import Path
import socket
import pytest

from core.types import (
    CaseInput,
)
from verify import m2_dev_assessment as dev
from verify import m2_dev_execution as exec_mod
from verify import m2_live_budget as ledger


def synthetic_budget(consumed=3):
    # Chỉ synthetic baseline trong tmp_path; không xác nhận ngân sách repo.
    return {
        "schema_version": 1,
        "baseline": {
            "total": 45,
            "consumed": consumed,
            "confirmed_by": "synthetic-coordinator",
            "confirmed_at": "2026-10-09T12:00:00+07:00",
            "reconciliation_reference": "synthetic-test-only",
        },
        "attempts": [],
        "current": {"total": 45, "consumed": consumed, "remaining": 45 - consumed},
    }


@pytest.fixture
def verified_ledger(tmp_path):
    path = tmp_path / "synthetic-budget.json"
    path.write_text(json.dumps(synthetic_budget()), encoding="utf-8")
    return path


@pytest.fixture(autouse=True)
def offline_guard(monkeypatch):
    """Đảm bảo mọi test chạy 100% offline, không có kết nối socket hay provider."""

    def forbidden(*args, **kwargs):
        pytest.fail("Network, provider hoặc pipeline invocation bị cấm trong offline tests!")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)

    from infra import llm
    from core import pipeline

    monkeypatch.setattr(llm, "call_json", forbidden)
    monkeypatch.setattr(llm, "_request_openai", forbidden)
    monkeypatch.setattr(pipeline, "process_case", forbidden)


# Test 1: All 12 frozen cases load correctly
def test_all_12_frozen_cases_load_correctly():
    cases = exec_mod.load_frozen_cases()
    assert len(cases) == 12

    ids = tuple(c["id"] for c in cases)
    assert ids == exec_mod.EXPECTED_CASE_IDS

    distribution = {
        "P01": sum(1 for c in cases if c["expected_rule_id"] == "P01"),
        "P02": sum(1 for c in cases if c["expected_rule_id"] == "P02"),
        "P03": sum(1 for c in cases if c["expected_rule_id"] == "P03"),
        "P05": sum(1 for c in cases if c["expected_rule_id"] == "P05"),
        "AUTO_REPLY": sum(1 for c in cases if c["expected_decision"] == "AUTO_REPLY"),
        "ESCALATE": sum(1 for c in cases if c["expected_decision"] == "ESCALATE"),
    }
    assert distribution == exec_mod.EXPECTED_GOLD_DISTRIBUTION

    for c in cases:
        inp = c["input"]
        dt = datetime.fromisoformat(inp["received_at"])
        assert dt.tzinfo is not None and dt.utcoffset() is not None
        assert inp["channel"] == "verify"
        assert inp.get("external_id") is None
        assert c["meta"]["status"] == "GOLD_VERIFIED_READY_FOR_FREEZE"


# Test 2: Frozen fixture hash mismatch blocks execution
def test_frozen_fixture_hash_mismatch_blocks_execution(tmp_path):
    tampered_fixture = tmp_path / "tampered_fixture.json"
    tampered_fixture.write_text(json.dumps([{"id": "TAMPERED"}]), encoding="utf-8")

    with pytest.raises(ValueError, match="BLOCKED_FIXTURE_HASH_MISMATCH"):
        exec_mod.load_frozen_cases(tampered_fixture)

    with pytest.raises(ValueError, match="BLOCKED_FIXTURE_HASH_MISMATCH"):
        exec_mod.orchestrate_m2_dev_run(
            output_dir=tmp_path / "run_out",
            fixture_path=tampered_fixture,
        )


# Test 3: Offline mock runs produce 12 distinct observation IDs
def test_offline_mock_runs_produce_12_distinct_observation_ids(tmp_path):
    run_dir = tmp_path / "run_out"
    summary = exec_mod.orchestrate_m2_dev_run(output_dir=run_dir)

    assert summary.total_cases == 12
    assert summary.completed_cases == 12
    assert summary.failed_cases == 0

    obs_ids = [c.observation_id for c in summary.cases]
    assert len(obs_ids) == 12
    assert len(set(obs_ids)) == 12
    for oid in obs_ids:
        assert oid.startswith("obs_")


# Test 4: The adapter receives exactly the submitted payload bound into capture
def test_adapter_receives_exactly_submitted_payload_bound_into_capture(tmp_path):
    received_payloads: dict[str, CaseInput] = {}

    class InspectingAdapter:
        adapter_id = "inspecting_adapter"
        is_offline_mock = True

        def __call__(self, case_spec, submitted_input, observation_id, mode):
            received_payloads[str(case_spec["id"])] = deepcopy(submitted_input)
            default_adapter = exec_mod.DeterministicMockAdapter()
            return default_adapter(case_spec, submitted_input, observation_id, mode)

    run_dir = tmp_path / "run_out"
    summary = exec_mod.orchestrate_m2_dev_test_run(
        output_dir=run_dir,
        adapter=InspectingAdapter(),
        case_ids=["M2DEV-A1"],
    )

    assert "M2DEV-A1" in received_payloads
    received_inp = received_payloads["M2DEV-A1"]
    frozen_spec = dev.load_prereg("M2DEV-A1")
    assert dev.input_hash(received_inp) == dev.input_hash(frozen_spec["input"])

    # Check that capture on disk preserves this exact submitted input
    capture_path = Path(summary.cases[0].artifact_paths["capture"])
    capture_data = json.loads(capture_path.read_text(encoding="utf-8"))
    assert capture_data["identity"]["submitted_input_sha256"] == dev.input_hash(received_inp)


# Test 5: A swapped A1/A2 input is rejected
def test_swapped_a1_a2_input_is_rejected(tmp_path):
    a2_spec = dev.load_prereg("M2DEV-A2")
    a2_input = CaseInput(
        sender=a2_spec["input"]["sender"],
        subject=a2_spec["input"]["subject"],
        body=a2_spec["input"]["body"],
        received_at=datetime.fromisoformat(a2_spec["input"]["received_at"]),
        channel="verify",
    )

    class SwappingAdapter:
        adapter_id = "swapping_adapter"
        is_offline_mock = True

        def __call__(self, case_spec, submitted_input, observation_id, mode):
            default_adapter = exec_mod.DeterministicMockAdapter()
            return default_adapter(case_spec, submitted_input, observation_id, mode)

    # Calling execution_context with swapped input for M2DEV-A1 fails closed
    default_adapter = exec_mod.DeterministicMockAdapter()
    res = default_adapter(
        dev.load_prereg("M2DEV-A1"), a2_input, "obs-swapped", "OFFLINE_MOCK"
    ).result
    with pytest.raises(ValueError, match="INPUT_IDENTITY_MISMATCH"):
        dev.execution_context(a2_input, res, case_id="M2DEV-A1", observation_id="obs-swapped")


# Test 6: A mutated input after adapter invocation cannot create a false identity match
def test_mutated_input_after_adapter_invocation_cannot_create_false_identity_match(tmp_path):
    class MutatingAdapter:
        adapter_id = "mutating_adapter"
        is_offline_mock = True

        def __call__(self, case_spec, submitted_input, observation_id, mode):
            # Mutate the supposedly frozen input object
            object.__setattr__(submitted_input, "body", "TAMPERED_BODY")
            default_adapter = exec_mod.DeterministicMockAdapter()
            return default_adapter(case_spec, submitted_input, observation_id, mode)

    run_dir = tmp_path / "run_out"
    with pytest.raises(ValueError, match="INPUT_IDENTITY_MUTATED"):
        exec_mod.orchestrate_m2_dev_test_run(
            output_dir=run_dir,
            adapter=MutatingAdapter(),
            case_ids=["M2DEV-A1"],
        )


# Test 7: Wrong result ID or trace ID is rejected where verifiable
def test_wrong_result_id_or_trace_id_is_rejected(tmp_path):
    class BadResultIdAdapter:
        adapter_id = "bad_result_id_adapter"
        is_offline_mock = True

        def __call__(self, case_spec, submitted_input, observation_id, mode):
            default_adapter = exec_mod.DeterministicMockAdapter()
            out = default_adapter(case_spec, submitted_input, observation_id, mode)
            # Tamper result case_id to empty string
            bad_res = replace(out.result, case_id="")
            return exec_mod.AdapterOutput(result=bad_res)

    run_dir = tmp_path / "run_out"
    with pytest.raises(ValueError, match="INPUT_IDENTITY_INVALID"):
        exec_mod.orchestrate_m2_dev_test_run(
            output_dir=run_dir,
            adapter=BadResultIdAdapter(),
            case_ids=["M2DEV-A1"],
        )


# Test 8: Missing execution context prevents assessment PASS
def test_missing_execution_context_prevents_assessment_pass():
    default_adapter = exec_mod.DeterministicMockAdapter()
    spec = dev.load_prereg("M2DEV-A1")
    inp = CaseInput(
        sender=spec["input"]["sender"],
        subject=spec["input"]["subject"],
        body=spec["input"]["body"],
        received_at=datetime.fromisoformat(spec["input"]["received_at"]),
        channel="verify",
    )
    res = default_adapter(spec, inp, "obs-test", "OFFLINE_MOCK").result

    # capture_result without execution context creates capture without identity
    # assess_capture must reject it with INPUT_IDENTITY_REQUIRED
    captured = dev.Capture(
        dev.FIXTURE_SHA256,
        "M2DEV-A1",
        "obs-test",
        dev._safe(dev.asdict(res)),
        {},
        {},
        identity=None,
    )
    with pytest.raises(ValueError, match="INPUT_IDENTITY_REQUIRED"):
        dev.assess_capture(captured)


# Test 9: Decision.ERROR remains a technical error
def test_decision_error_remains_technical_error(tmp_path):
    error_adapter = exec_mod.DeterministicMockAdapter(force_error=True)
    run_dir = tmp_path / "run_out"
    summary = exec_mod.orchestrate_m2_dev_run(
        output_dir=run_dir,
        adapter=error_adapter,
        case_ids=["M2DEV-A1"],
    )

    case_summary = summary.cases[0]
    assert case_summary.actual_decision == "ERROR"
    assert case_summary.actual_rule_id == "TECHNICAL_ERROR"
    assert case_summary.technical_status == "TECHNICAL_ERROR"
    assert case_summary.assessment_verdict == "TECHNICAL_ERROR"
    # Never converted to P01/P02/P03
    assert case_summary.actual_escalation_type is None


# Test 10: Adapter exception is recorded separately without fabricated PipelineResult
def test_adapter_exception_recorded_separately_without_fabricated_pipeline_result(tmp_path):
    crashing_adapter = exec_mod.DeterministicMockAdapter(force_adapter_exception=True)
    run_dir = tmp_path / "run_out"
    summary = exec_mod.orchestrate_m2_dev_run(
        output_dir=run_dir,
        adapter=crashing_adapter,
        case_ids=["M2DEV-A1"],
    )

    assert summary.completed_cases == 0
    assert summary.failed_cases == 1
    case_summary = summary.cases[0]
    assert case_summary.technical_status == "ADAPTER_EXCEPTION"
    assert case_summary.assessment_verdict == "ERROR"
    assert case_summary.capture_sha256 is None
    assert case_summary.result_case_id is None

    # Check failure record file
    failure_file = Path(case_summary.artifact_paths["failure"])
    assert failure_file.exists()
    failure_data = json.loads(failure_file.read_text(encoding="utf-8"))
    assert failure_data["technical_status"] == "ADAPTER_EXCEPTION"
    assert failure_data["error_category"] == "ADAPTER_RUNTIME_ERROR"
    assert failure_data["exception_class"] == "RuntimeError"
    assert "error" not in failure_data


# Test 11: Assessment or artifact-write failure does not produce a false PASS
def test_assessment_or_artifact_write_failure_does_not_produce_false_pass(tmp_path, monkeypatch):
    def broken_write(*args, **kwargs):
        raise OSError("SIMULATED_DISK_WRITE_FAILURE")

    monkeypatch.setattr(dev, "write_artifacts", broken_write)

    run_dir = tmp_path / "run_out"
    with pytest.raises(OSError, match="SIMULATED_DISK_WRITE_FAILURE"):
        exec_mod.orchestrate_m2_dev_run(
            output_dir=run_dir,
            case_ids=["M2DEV-A1"],
        )


# Test 12: An unreviewed semantic case remains REVIEW_REQUIRED
def test_unreviewed_semantic_case_remains_review_required(tmp_path):
    run_dir = tmp_path / "run_out"
    summary = exec_mod.orchestrate_m2_dev_run(
        output_dir=run_dir,
        case_ids=["M2DEV-A1"],
    )

    case_summary = summary.cases[0]
    assert case_summary.technical_status == "OK"
    assert case_summary.assessment_verdict == "REVIEW_REQUIRED"
    assert summary.verdicts["REVIEW_REQUIRED"] == 1
    assert summary.verdicts["PASS"] == 0


# Test 13: Existing artifact directories cannot be overwritten
def test_existing_artifact_directories_cannot_be_overwritten(tmp_path):
    existing_dir = tmp_path / "already_exists"
    existing_dir.mkdir()

    with pytest.raises(FileExistsError, match="ARTIFACT_DIRECTORY_EXISTS"):
        exec_mod.orchestrate_m2_dev_run(output_dir=existing_dir)


# Test 14: Path traversal is rejected
def test_path_traversal_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="PATH_TRAVERSAL_PREVENTED"):
        exec_mod._validate_safe_id("../../evil_path", "test_id")

    with pytest.raises(ValueError, match="PATH_TRAVERSAL_PREVENTED"):
        exec_mod._validate_safe_id("run..bad/id", "run_id")

    with pytest.raises(ValueError, match="PATH_TRAVERSAL_PREVENTED"):
        exec_mod.orchestrate_m2_dev_run(
            output_dir=tmp_path / "out",
            run_id="../escaped_run",
        )


# Test 15: LIVE mode is rejected
def test_live_mode_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="LIVE_EXECUTION_NOT_ENABLED"):
        exec_mod.orchestrate_m2_dev_run(
            output_dir=tmp_path / "out",
            mode="LIVE",
        )

    # CLI rejection
    exit_code = exec_mod.main(["--live"])
    assert exit_code == 1


# Test 16: Mock execution never consumes the LIVE budget
def test_mock_execution_never_consumes_live_budget(tmp_path, verified_ledger):
    ledger_before = verified_ledger.read_bytes()
    budget_before = exec_mod.verify_live_budget(verified_ledger)
    run_dir = tmp_path / "run_out"
    summary = exec_mod.orchestrate_m2_dev_run(output_dir=run_dir, ledger_path=verified_ledger)

    budget_after = exec_mod.verify_live_budget(verified_ledger)
    assert verified_ledger.read_bytes() == ledger_before
    assert budget_after.used_observations == budget_before.used_observations
    assert budget_after.remaining_budget == budget_before.remaining_budget
    assert summary.live_budget_status["live_consumed_this_run"] == 0


# Test 17: Budget overrun is rejected by the budget-check interface
def test_budget_overrun_is_rejected_by_budget_check_interface(verified_ledger):
    budget = exec_mod.verify_live_budget(verified_ledger)
    assert budget.remaining_budget == 42

    # Requesting 43 in LIVE mode (exceeding 42 remaining) is rejected
    with pytest.raises(exec_mod.BudgetExceededError, match="BUDGET_EXCEEDED"):
        exec_mod.check_budget_authorization(
            requested_count=budget.remaining_budget + 1,
            is_live=True,
            ledger_path=verified_ledger,
        )


# Test 18: Missing or unverified budget information fails closed
def test_missing_or_unverified_budget_fails_closed(tmp_path):
    missing_file = tmp_path / "non_existent_progress.md"
    with pytest.raises(exec_mod.BudgetVerificationError, match="BUDGET_UNVERIFIED"):
        exec_mod.verify_live_budget(missing_file)

    corrupted_file = tmp_path / "corrupted_progress.md"
    corrupted_file.write_text("Không có thông tin ngân sách nào.", encoding="utf-8")
    with pytest.raises(exec_mod.BudgetVerificationError, match="BUDGET_UNVERIFIED"):
        exec_mod.verify_live_budget(corrupted_file)


# Test 19: No provider or network calls occur
def test_no_provider_or_network_calls_occur(tmp_path):
    # offline_guard fixture is active and strictly asserts no network/provider calls
    run_dir = tmp_path / "run_out"
    summary = exec_mod.orchestrate_m2_dev_run(output_dir=run_dir)
    assert summary.completed_cases == 12


# Test 20: Frozen fixture SHA-256 remains unchanged after execution
def test_frozen_fixture_sha256_remains_unchanged_after_execution(tmp_path):
    hash_before = hashlib.sha256(exec_mod.FIXTURE.read_bytes()).hexdigest()
    assert hash_before == exec_mod.FIXTURE_SHA256

    run_dir = tmp_path / "run_out"
    exec_mod.orchestrate_m2_dev_run(output_dir=run_dir)

    hash_after = hashlib.sha256(exec_mod.FIXTURE.read_bytes()).hexdigest()
    assert hash_after == exec_mod.FIXTURE_SHA256


# Test 21: Synthetic case with unsupported factual options preserves findings
def test_synthetic_case_with_unsupported_factual_options_preserves_findings(tmp_path):
    unsupported_adapter = exec_mod.DeterministicMockAdapter(
        unsupported_options=["Gia hạn 3 ngày", "Hoàn 50% học phí"]
    )
    run_dir = tmp_path / "run_out"
    summary = exec_mod.orchestrate_m2_dev_run(
        output_dir=run_dir,
        adapter=unsupported_adapter,
        case_ids=["M2DEV-A1"],
    )

    assessment_path = Path(summary.cases[0].artifact_paths["assessment"])
    assessment_data = json.loads(assessment_path.read_text(encoding="utf-8"))

    # Assessment must preserve unsupported factual options in risk_findings
    risk_findings = assessment_data["risk_findings"]
    assert any("3 ngày" in f or "50%" in f for f in risk_findings)
    assert summary.cases[0].assessment_verdict == "REVIEW_REQUIRED"
    assert summary.cases[0].assessment_verdict != "PASS"


# Test 22: CLI dry-run validation
def test_cli_dry_run(capsys, monkeypatch, tmp_path):
    monkeypatch.setattr(
        exec_mod,
        "check_budget_authorization",
        lambda n, **kwargs: ledger.check_budget_authorization(
            n, is_live=False, ledger_path=tmp_path / "missing.json"
        ),
    )
    exit_code = exec_mod.main(["--mode", "dry_run"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "DRY_RUN_VALIDATION_OK" in captured.out
    assert "BUDGET_UNVERIFIED" in captured.out


def test_historical_progress_never_authorizes_current_budget(tmp_path):
    path = tmp_path / "progress.md"
    path.write_text("Cumulative M2 Goal LIVE = 3/45\nCumulative M2 Goal LIVE = 15/45")
    with pytest.raises(ledger.BudgetVerificationError, match="BUDGET_UNVERIFIED"):
        ledger.verify_live_budget(path)
    info = ledger.check_budget_authorization(1, is_live=False, ledger_path=path)
    assert not info.is_verified and info.used_observations is None


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate_key",
        "conflicting_current",
        "negative",
        "over_total",
        "no_confirmation",
        "no_reference",
        "duplicate_observation",
        "bool_count",
    ],
)
def test_invalid_authoritative_ledger_fails_closed(verified_ledger, mutation):
    data = synthetic_budget()
    if mutation == "duplicate_key":
        text = json.dumps(data).replace(
            '"schema_version": 1', '"schema_version": 1, "schema_version": 1'
        )
    else:
        if mutation == "conflicting_current":
            data["current"] = [data["current"], {"total": 45, "consumed": 15, "remaining": 30}]
        elif mutation == "negative":
            data["baseline"]["consumed"] = -1
        elif mutation == "over_total":
            data["baseline"]["consumed"] = 46
        elif mutation == "no_confirmation":
            data["baseline"]["confirmed_by"] = ""
        elif mutation == "no_reference":
            data["baseline"].pop("reconciliation_reference")
        elif mutation == "bool_count":
            data["current"]["consumed"] = True
        else:
            event = {
                "observation_id": "repeat",
                "case_id": "M2DEV-A1",
                "started_at": "2026-10-09T12:00:00+07:00",
                "status": "ATTEMPTED",
                "internal_retries": 0,
            }
            data["attempts"] = [event, event]
            data["current"].update(consumed=5, remaining=40)
        text = json.dumps(data)
    verified_ledger.write_text(text, encoding="utf-8")
    with pytest.raises(ledger.BudgetVerificationError, match="BUDGET_UNVERIFIED"):
        ledger.check_budget_authorization(1, is_live=True, ledger_path=verified_ledger)


def test_missing_ledger_fails_closed_for_live_but_mock_is_unverified(tmp_path):
    path = tmp_path / "absent.json"
    with pytest.raises(ledger.BudgetVerificationError, match="BUDGET_UNVERIFIED"):
        ledger.check_budget_authorization(1, is_live=True, ledger_path=path)
    summary = exec_mod.orchestrate_m2_dev_run(output_dir=tmp_path / "mock", ledger_path=path)
    assert summary.live_budget_status["authorization"] == "BUDGET_UNVERIFIED"
    assert summary.live_budget_status["live_consumed_this_run"] == 0
    assert not path.exists()


def test_attempt_and_technical_failure_consumed_once_retries_not_observations(verified_ledger):
    begin = ledger.record_live_observation(
        verified_ledger, observation_id="obs1", case_id="M2DEV-A1"
    )
    assert begin.used_observations == 4  # dù crash trước result vẫn đã debit
    end = ledger.record_live_observation(
        verified_ledger,
        observation_id="obs1",
        case_id="M2DEV-A1",
        status="TECHNICAL_FAILURE",
        internal_retries=2,
    )
    assert end.used_observations == 4 and end.remaining_budget == 41
    data = json.loads(verified_ledger.read_text())
    assert len(data["attempts"]) == 1
    assert data["attempts"][0]["internal_retries"] == 2
    assert data["attempts"][0]["status"] == "TECHNICAL_FAILURE"
    with pytest.raises(ledger.BudgetVerificationError):
        ledger.record_live_observation(verified_ledger, observation_id="obs1", case_id="M2DEV-A1")


def test_unstarted_failure_cannot_be_silently_zero_counted(verified_ledger):
    before = verified_ledger.read_bytes()
    with pytest.raises(ledger.BudgetVerificationError):
        ledger.record_live_observation(
            verified_ledger,
            observation_id="missing",
            case_id="M2DEV-A1",
            status="TECHNICAL_FAILURE",
        )
    assert verified_ledger.read_bytes() == before


def test_ledger_lock_and_exhaustion_fail_closed(verified_ledger):
    lock = verified_ledger.with_suffix(".json.lock")
    lock.write_text("synthetic lock")
    with pytest.raises(ledger.BudgetVerificationError):
        ledger.record_live_observation(verified_ledger, observation_id="locked", case_id="M2DEV-A1")
    lock.unlink()
    verified_ledger.write_text(json.dumps(synthetic_budget(45)))
    with pytest.raises(ledger.BudgetExceededError):
        ledger.record_live_observation(verified_ledger, observation_id="over", case_id="M2DEV-A1")


def test_self_declared_adapter_and_subclass_are_rejected_operationally(tmp_path):
    class SelfDeclared:
        is_offline_mock = True

        def __call__(self, *args, **kwargs):
            pytest.fail("Untrusted adapter must never execute")

    class Subclass(exec_mod.DeterministicMockAdapter):
        pass

    for adapter in (
        SelfDeclared(),
        Subclass(),
        exec_mod.DeterministicMockAdapter(custom_result_factory=lambda *a: None),
    ):
        with pytest.raises(ValueError, match="ADAPTER_NOT_TRUSTED_BUILTIN"):
            exec_mod.orchestrate_m2_dev_run(output_dir=tmp_path / "rejected", adapter=adapter)
    assert not (tmp_path / "rejected").exists()


def test_cli_has_no_adapter_loading(tmp_path):
    with pytest.raises(SystemExit) as error:
        exec_mod.main(
            ["--adapter", "malicious.module:Adapter", "--output-dir", str(tmp_path / "out")]
        )
    assert error.value.code == 2
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("unknown", [False, True])
def test_exception_secret_and_private_body_never_persisted(tmp_path, unknown):
    secret = "sk-SYNTHETIC-SECRET"
    body = "SYNTHETIC private email body: my entire personal history and records."

    class UnknownAdapterError(Exception):
        def __str__(self):
            pytest.fail("Exception text must never be accessed")

        def __repr__(self):
            pytest.fail("Exception repr must never be accessed")

    class Crashing:
        adapter_id = "synthetic"

        def __call__(self, **kwargs):
            raise (UnknownAdapterError if unknown else RuntimeError)(secret + body)

    summary = exec_mod.orchestrate_m2_dev_test_run(
        output_dir=tmp_path / "out", adapter=Crashing(), case_ids=["M2DEV-A1"]
    )
    case = summary.cases[0]
    failure = json.loads(Path(case.artifact_paths["failure"]).read_text(encoding="utf-8"))
    assert failure["case_id"] == "M2DEV-A1" and failure["observation_id"] == case.observation_id
    assert failure["technical_status"] == "ADAPTER_EXCEPTION"
    assert failure["error_category"] == (
        "UNCLASSIFIED_ADAPTER_ERROR" if unknown else "ADAPTER_RUNTIME_ERROR"
    )
    expected_keys = {
        "case_id",
        "observation_id",
        "technical_status",
        "timestamp",
        "error_category",
        "error_code",
    }
    assert set(failure) == expected_keys | (set() if unknown else {"exception_class"})
    assert case.actual_decision is None and case.capture_sha256 is None
    for artifact in (tmp_path / "out").rglob("*"):
        if artifact.is_file():
            text = artifact.read_text(encoding="utf-8")
            assert secret not in text and body not in text and "UnknownAdapterError" not in text


def test_test_only_injection_cannot_enable_live(tmp_path):
    with pytest.raises(ValueError, match="LIVE_EXECUTION_NOT_ENABLED"):
        exec_mod.orchestrate_m2_dev_test_run(
            output_dir=tmp_path / "out", adapter=object(), mode="LIVE"
        )


def test_environment_cannot_select_live_adapter(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_MODE", "live")
    monkeypatch.setenv("M2_DEV_ADAPTER", "untrusted.module:Adapter")
    summary = exec_mod.orchestrate_m2_dev_run(output_dir=tmp_path / "mock", case_ids=["M2DEV-A1"])
    assert summary.run_mode == "OFFLINE_MOCK"
    assert summary.live_budget_status["live_consumed_this_run"] == 0
    assert summary.cases[0].actual_rule_id == "P01"


def test_authoritative_current_counts_must_match_attempts(verified_ledger):
    data = synthetic_budget()
    data["current"].update(consumed=15, remaining=30)
    verified_ledger.write_text(json.dumps(data))
    with pytest.raises(ledger.BudgetVerificationError, match="BUDGET_UNVERIFIED"):
        ledger.verify_live_budget(verified_ledger)


def test_semantic_result_finalization_does_not_double_debit(verified_ledger):
    ledger.record_live_observation(verified_ledger, observation_id="semantic", case_id="M2DEV-A1")
    info = ledger.record_live_observation(
        verified_ledger,
        observation_id="semantic",
        case_id="M2DEV-A1",
        status="SEMANTIC_RESULT",
        internal_retries=1,
    )
    assert info.used_observations == 4
    assert len(json.loads(verified_ledger.read_text())["attempts"]) == 1
